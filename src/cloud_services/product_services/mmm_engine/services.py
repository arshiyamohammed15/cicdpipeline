"""
Core service layer for MMM Engine.
"""

from __future__ import annotations

import logging
from typing import Optional
from datetime import datetime
import asyncio
import time
import uuid

from sqlalchemy.orm import Session

from .models import (
    MMMDecision,
    MMMContext,
    MMMAction,
    DecideRequest,
    DecideResponse,
    ActionType,
    Surface,
    ActorType,
    MMMSignalInput,
    Playbook,
    PlaybookStatus,
    PlaybookCreateRequest,
)
from .service_registry import (
    get_policy_service,
    get_ubi_signal_service,
    get_eris,
)
from .context import ContextService
from .integrations.signal_bus import SignalBusClient, SignalEnvelope
from .integrations.downstream_clients import EdgeAgentClient, CIWorkflowClient, AlertingClient
from .actions import ActionComposer
from .routing import SurfaceRouter
from .database.repositories import PlaybookRepository, OutcomeRepository, DecisionRepository
from .fatigue import FatigueManager, EligibilityEngine, PrioritizationEngine, FatigueLimits
from .delivery import DeliveryOrchestrator
from .observability.metrics import record_decision_metrics, record_outcome_metrics
from .reliability.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class MMMService:
    """High-level orchestration service for MMM decisions."""

    def __init__(self) -> None:
        self.policy = get_policy_service()
        self.signal_service = get_ubi_signal_service()
        self.context_service = ContextService()
        self.eris = get_eris()
        self.eris_circuit = CircuitBreaker("eris")
        self.signal_bus = SignalBusClient()
        self.signal_bus.register_handler(self._handle_ingested_signal)
        self.action_composer = ActionComposer()
        self.surface_router = SurfaceRouter()
        self.fatigue_manager = FatigueManager()
        self.eligibility_engine = EligibilityEngine()
        self.prioritization_engine = PrioritizationEngine()
        self.delivery_orchestrator = DeliveryOrchestrator(
            EdgeAgentClient(),
            CIWorkflowClient(),
            AlertingClient(),
        )
        self.outcome_stats: dict[str, dict[str, int]] = {}

    def list_playbooks(self, tenant_id: str, db: Session) -> list[Playbook]:
        repo = PlaybookRepository(db)
        return repo.list_playbooks(tenant_id)

    def create_playbook(self, tenant_id: str, payload: PlaybookCreateRequest, db: Session) -> Playbook:
        playbook = Playbook(
            playbook_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            version=payload.version,
            name=payload.name,
            status=PlaybookStatus.DRAFT,
            triggers=payload.triggers,
            conditions=payload.conditions,
            actions=payload.actions,
            limits=payload.limits,
        )
        repo = PlaybookRepository(db)
        return repo.save(playbook)

    def publish_playbook(self, tenant_id: str, playbook_id: str, db: Session) -> Optional[Playbook]:
        repo = PlaybookRepository(db)
        return repo.publish(tenant_id, playbook_id)

    def decide(self, request: DecideRequest, db: Optional[Session] = None) -> DecideResponse:
        """Evaluate signals and produce Mirror/Mentor/Multiplier actions."""
        start = time.perf_counter()
        tenant_id = request.tenant_id
        actor_id = request.actor_id or "unknown"
        actor_type = request.actor_type or ActorType.HUMAN

        context = self.context_service.build_context(
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type=actor_type,
            extra=request.context,
        )
        policy_result = self.policy.evaluate(tenant_id, request.context)
        context.policy_snapshot_id = policy_result.get("policy_snapshot_id")

        playbooks = []
        if db is not None:
            repo = PlaybookRepository(db)
            playbooks = [
                p for p in repo.list_playbooks(tenant_id) if p.status == PlaybookStatus.PUBLISHED
            ]
        actions = self._evaluate_playbooks(context, playbooks)
        if not policy_result.get("allowed", True):
            logger.warning("Policy denied actions for tenant=%s", tenant_id)
            actions = []

        decision = MMMDecision(
            decision_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type=actor_type,
            context=context,
            actions=self.surface_router.route(actions),
            created_at=datetime.utcnow(),
            policy_snapshot_id=context.policy_snapshot_id,
        )
        if db is not None:
            DecisionRepository(db).save_decision(decision)
        latency = time.perf_counter() - start
        record_decision_metrics(tenant_id, actor_type.value, len(decision.actions), latency)
        self.delivery_orchestrator.deliver(decision)
        logger.info(
            "MMM decide issued %s actions for tenant=%s actor=%s",
            len(actions),
            tenant_id,
            actor_id,
        )
        return DecideResponse(decision=decision)

    async def ingest_signal(self, envelope: SignalEnvelope) -> None:
        """Public entrypoint for async signal ingestion."""
        await self.signal_bus.publish(envelope)

    async def _handle_ingested_signal(self, signal: MMMSignalInput) -> None:
        """Default handler for ingested signals (placeholder)."""
        logger.debug("Handled ingested signal %s", signal.signal_id)

    def record_outcome(self, outcome: MMMOutcome, db: Session) -> MMMOutcome:
        repo = OutcomeRepository(db)
        repo.save_outcome(outcome)
        record_outcome_metrics(outcome.tenant_id, outcome.result)
        self._emit_outcome_receipt(outcome)
        tenant_stats = self.outcome_stats.setdefault(outcome.tenant_id, {})
        tenant_stats[outcome.result] = tenant_stats.get(outcome.result, 0) + 1
        return outcome

    def _evaluate_playbooks(self, context: MMMContext, playbooks: list[Playbook]) -> list[MMMAction]:
        actions: list[MMMAction] = []
        score_lookup: dict[str, float] = {}
        now = datetime.utcnow()
        actor_key = context.actor_id or "unknown"

        ordered_playbooks = list(playbooks or [])
        ordered_playbooks.sort(key=lambda pb: float(pb.limits.get("priority", 1)) if pb.limits else 1.0, reverse=True)

        for order_index, playbook in enumerate(ordered_playbooks):
            if not self.eligibility_engine.is_eligible(playbook, context):
                continue

            limits = self._build_fatigue_limits(playbook, context)
            if not self.fatigue_manager.can_emit(context.tenant_id, actor_key, playbook.playbook_id, limits, now):
                continue

            playbook_score = self.prioritization_engine.score_playbook(playbook, context, order_index)
            playbook_actions = self.action_composer.compose_actions(playbook.name, playbook.actions, context)

            for action in playbook_actions:
                if not self.fatigue_manager.can_emit(
                    context.tenant_id, actor_key, action.type.value, limits, now
                ):
                    continue
                score_lookup[action.action_id] = playbook_score
                self.fatigue_manager.record(context.tenant_id, actor_key, action.type.value, now)
                actions.append(action)

        ordered = self.prioritization_engine.order(actions, score_lookup)
        if not ordered:
            ordered.append(
                MMMAction(
                    action_id=str(uuid.uuid4()),
                    type=ActionType.MIRROR,
                    surfaces=[Surface.IDE],
                    payload={
                        "title": "Mirror insight",
                        "body": f"Signals observed: {len(context.recent_signals)}",
                    },
                )
            )
        return ordered

    def _build_fatigue_limits(self, playbook: Playbook, context: MMMContext) -> FatigueLimits:
        limits = playbook.limits or {}
        quiet = limits.get("quiet_hours") or context.quiet_hours
        return FatigueLimits(
            max_per_day=int(limits.get("max_per_actor_per_day", 5)),
            cooldown_minutes=int(limits.get("cooldown_minutes", 30)),
            quiet_hours=quiet,
        )

    def _emit_outcome_receipt(self, outcome: MMMOutcome) -> None:
        try:
            payload = {
                "receipt_id": f"outcome-{outcome.decision_id}-{outcome.action_id}",
                "tenant_id": outcome.tenant_id,
                "gate_id": "mmm",
                "timestamp_utc": datetime.utcnow().isoformat(),
                "decision": {
                    "status": "pass",
                    "rationale": f"Outcome recorded: {outcome.result}",
                },
                "inputs": {"decision_id": outcome.decision_id, "action_id": outcome.action_id},
                "result": {"result": outcome.result, "reason": outcome.reason},
                "evidence_handles": [],
            }
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                self.eris_circuit.call(lambda: asyncio.run(self.eris.emit_receipt(payload)))
            else:
                loop.create_task(self.eris_circuit.call_async(self.eris.emit_receipt, payload))
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to emit outcome receipt: %s", exc)


