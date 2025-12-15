"""
Core service layer for MMM Engine.
"""

from __future__ import annotations

import logging
from typing import Optional
from datetime import datetime, timezone
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
    ActorPreferences,
    ActorPreferencesCreateRequest,
    ActorPreferencesUpdateRequest,
    ActorPreferencesSnoozeRequest,
    TenantMMMPolicy,
    TenantMMMPolicyUpdateRequest,
    DualChannelApproval,
    DualChannelApprovalRequest,
    DualChannelApprovalStatus,
)
from .service_registry import (
    get_policy_service,
    get_ubi_signal_service,
    get_eris,
    get_llm_gateway,
    get_data_governance,
    get_iam,
)
from .integrations.policy_client import PolicyClientError
from .context import ContextService
from .integrations.signal_bus import SignalBusClient, SignalEnvelope
from .integrations.downstream_clients import EdgeAgentClient, CIWorkflowClient, AlertingClient
from .actions import ActionComposer
from .routing import SurfaceRouter
from .database.repositories import (
    PlaybookRepository,
    OutcomeRepository,
    DecisionRepository,
    ActorPreferencesRepository,
    TenantPolicyRepository,
    DualChannelApprovalRepository,
    ExperimentRepository,
)
from .database.models import DecisionModel, ActionModel, OutcomeModel
from .fatigue import FatigueManager, EligibilityEngine, PrioritizationEngine, FatigueLimits
from .delivery import DeliveryOrchestrator
from .observability.metrics import record_decision_metrics, record_outcome_metrics
from .observability.tracing import get_tracing_service
from .observability.audit import AuditLogger
from .database.retention import RetentionService
from .reliability.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class MMMService:
    """High-level orchestration service for MMM decisions."""

    def __init__(self) -> None:
        self.policy_cache = get_policy_service()
        self.signal_service = get_ubi_signal_service()
        self.context_service = ContextService()
        self.eris = get_eris()
        self.llm_gateway = get_llm_gateway()
        self.data_governance = get_data_governance()
        self.iam = get_iam()
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
        # Preference cache (5min TTL per PRD)
        self._preference_cache: dict[str, tuple[ActorPreferences, float]] = {}
        self._preference_cache_ttl = 300.0  # 5 minutes
        self.retention_service = RetentionService()

    def list_playbooks(self, tenant_id: str, db: Session) -> list[Playbook]:
        repo = PlaybookRepository(db)
        return repo.list_playbooks(tenant_id)

    def create_playbook(self, tenant_id: str, payload: PlaybookCreateRequest, db: Session, admin_user_id: Optional[str] = None) -> Playbook:
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
        saved = repo.save(playbook)
        # Audit logging
        if admin_user_id:
                AuditLogger.log_admin_action(
                    admin_user_id=admin_user_id,
                    action="playbook_create",
                    resource_type="playbook",
                    resource_id=playbook.playbook_id,
                    after_state=playbook.model_dump(),
                )
        return saved

    def publish_playbook(self, tenant_id: str, playbook_id: str, db: Session, admin_user_id: Optional[str] = None) -> Optional[Playbook]:
        repo = PlaybookRepository(db)
        before = repo.get(tenant_id, playbook_id)
        published = repo.publish(tenant_id, playbook_id)
        # Audit logging
        if admin_user_id and published:
            AuditLogger.log_admin_action(
                admin_user_id=admin_user_id,
                action="playbook_publish",
                resource_type="playbook",
                resource_id=playbook_id,
                before_state=before.model_dump() if before else None,
                after_state=published.model_dump(),
            )
        return published

    def decide(self, request: DecideRequest, db: Optional[Session] = None) -> DecideResponse:
        """Evaluate signals and produce Mirror/Mentor/Multiplier actions."""
        start = time.perf_counter()
        tenant_id = request.tenant_id
        actor_id = request.actor_id or "unknown"
        actor_type = request.actor_type or ActorType.HUMAN

        # Create parent span for decision flow
        tracing = get_tracing_service()
        with tracing.span(
            "mmm.decide",
            attributes={
                "tenant_id": tenant_id,
                "actor_id": actor_id,
                "actor_type": actor_type.value,
            },
        ):
            # Check degraded mode for all dependencies
            degraded_mode = self._check_degraded_mode()

            # Build context (may use degraded defaults)
            with tracing.span("context.build", attributes={"tenant_id": tenant_id}):
                try:
                    context = self.context_service.build_context(
                        tenant_id=tenant_id,
                        actor_id=actor_id,
                        actor_type=actor_type,
                        extra=request.context,
                    )
                except Exception as exc:
                    logger.warning(
                        "Context build failed, using minimal context: %s (tenant_id=%s, actor_id=%s)",
                        exc,
                        tenant_id,
                        actor_id,
                    )
                    context = MMMContext(
                        tenant_id=tenant_id,
                        actor_id=actor_id,
                        actor_type=actor_type,
                        actor_roles=request.context.get("roles", []),
                        repo_id=request.context.get("repo_id"),
                        branch=request.context.get("branch"),
                        file_path=request.context.get("file_path"),
                        quiet_hours={"start": 22, "end": 6},  # Default
                        recent_signals=[],  # Empty if UBI unavailable
                    )
                    degraded_mode = True

            # Get policy snapshot (with degraded mode handling)
            policy_snapshot = None
            policy_allowed = True
            policy_restrictions = []
            policy_stale = False
            with tracing.span("policy.gate", attributes={"tenant_id": tenant_id}):
                try:
                    policy_snapshot = self.policy_cache.get_snapshot(tenant_id)
                    policy_allowed = policy_snapshot.allowed
                    policy_restrictions = policy_snapshot.restrictions
                    policy_stale = policy_snapshot.policy_stale
                    context.policy_snapshot_id = policy_snapshot.snapshot_id
                except PolicyClientError as exc:
                    logger.error(
                        "Policy unavailable for tenant %s: %s",
                        tenant_id,
                        exc,
                    )
                    degraded_mode = True
                    # Use default policy snapshot ID
                    context.policy_snapshot_id = f"{tenant_id}-snapshot-default"

            # Get actor preferences (with caching)
            actor_preferences = None
            if db is not None:
                actor_preferences = self._get_actor_preferences_cached(
                    db, tenant_id, actor_id
                )

            # Apply preference filtering: snooze check
            actions = []  # Initialize actions list
            if actor_preferences and actor_preferences.snooze_until:
                snooze_until = actor_preferences.snooze_until
                if snooze_until.tzinfo is None:
                    snooze_until = snooze_until.replace(tzinfo=timezone.utc)
                if snooze_until > datetime.now(timezone.utc):
                    logger.info(
                        "Actor %s snoozed until %s, returning empty actions",
                        actor_id,
                        snooze_until,
                    )
                    # Leave actions empty, skip playbook evaluation
                else:
                    # Snooze expired, continue with playbook evaluation
                    # Evaluate playbooks
                    playbooks = []
                    if db is not None:
                        repo = PlaybookRepository(db)
                        playbooks = [
                            p for p in repo.list_playbooks(tenant_id) if p.status == PlaybookStatus.PUBLISHED
                        ]
                    with tracing.span("playbook.evaluate", attributes={"playbook_count": len(playbooks)}):
                        actions = self._evaluate_playbooks(context, playbooks, degraded_mode)
            else:
                # No snooze, evaluate playbooks
                playbooks = []
                if db is not None:
                    repo = PlaybookRepository(db)
                    playbooks = [
                        p for p in repo.list_playbooks(tenant_id) if p.status == PlaybookStatus.PUBLISHED
                    ]
                with tracing.span("playbook.evaluate", attributes={"playbook_count": len(playbooks)}):
                    actions = self._evaluate_playbooks(context, playbooks, degraded_mode)

            # Apply policy restrictions
            if not policy_allowed:
                logger.warning("Policy denied actions for tenant=%s", tenant_id)
                actions = []
            elif policy_restrictions:
                # Filter actions by restrictions
                actions = [
                    a for a in actions
                    if a.type.value not in policy_restrictions
                ]

            # Apply actor preferences: opt-out categories and preferred surfaces
            if actor_preferences and actions:
                # Filter by opt-out categories
                if actor_preferences.opt_out_categories:
                    actions = [
                        a for a in actions
                        if a.type.value not in actor_preferences.opt_out_categories
                    ]
                # Filter by preferred surfaces
                if actor_preferences.preferred_surfaces:
                    filtered_actions = []
                    for action in actions:
                        # Only include surfaces that are in preferred_surfaces
                        preferred_surfaces = [
                            Surface(s) for s in actor_preferences.preferred_surfaces
                            if Surface(s) in action.surfaces
                        ]
                        if preferred_surfaces:
                            action.surfaces = preferred_surfaces
                            filtered_actions.append(action)
                    actions = filtered_actions

            # Get tenant policy and apply quotas/surfaces/action types
            tenant_policy = None
            if db is not None:
                tenant_policy_repo = TenantPolicyRepository(db)
                tenant_policy = tenant_policy_repo.get_policy(tenant_id)
                if tenant_policy:
                    # Filter by enabled_action_types
                    if tenant_policy.enabled_action_types:
                        actions = [
                            a for a in actions
                            if a.type.value in tenant_policy.enabled_action_types
                        ]
                    # Filter by enabled_surfaces
                    if tenant_policy.enabled_surfaces:
                        filtered_actions = []
                        for action in actions:
                            enabled_surfaces = [
                                Surface(s) for s in tenant_policy.enabled_surfaces
                                if Surface(s) in action.surfaces
                            ]
                            if enabled_surfaces:
                                action.surfaces = enabled_surfaces
                                filtered_actions.append(action)
                        actions = filtered_actions
                    # Use tenant policy quiet hours (override Data Governance)
                    if tenant_policy.quiet_hours:
                        context.quiet_hours = tenant_policy.quiet_hours

            decision = MMMDecision(
                decision_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                actor_id=actor_id,
                actor_type=actor_type,
                context=context,
                actions=self.surface_router.route(actions),
                created_at=datetime.now(timezone.utc),
                policy_snapshot_id=context.policy_snapshot_id,
                degraded_mode=degraded_mode,
            )
            if db is not None:
                DecisionRepository(db).save_decision(decision)

            # Emit decision receipt synchronously (per PRD FR-12)
            with tracing.span("eris.receipt", attributes={"decision_id": decision.decision_id}):
                receipt_success = self._emit_decision_receipt(decision, policy_snapshot, degraded_mode, policy_stale)
                from .observability.metrics import record_eris_receipt_emission
                record_eris_receipt_emission(tenant_id, receipt_success)

            latency = time.perf_counter() - start
            # Determine surface from context (default to IDE)
            surface = "ide"
            if request.context.get("source") == "ci":
                surface = "ci"
            record_decision_metrics(tenant_id, actor_type.value, len(decision.actions), latency, surface)

            # Check latency SLO and set warning flag if exceeded
            threshold = 0.150 if surface == "ide" else 0.500
            if latency > threshold:
                decision.latency_warning = True
                logger.warning(
                    "Decision latency exceeded SLO: %.3fs > %.3fs for tenant=%s surface=%s",
                    latency,
                    threshold,
                    tenant_id,
                    surface,
                )

            # Add trace ID to logs
            trace_id = tracing.get_trace_id()
            logger.info(
                "MMM decide issued %s actions for tenant=%s actor=%s (degraded=%s, trace_id=%s)",
                len(actions),
                tenant_id,
                actor_id,
                degraded_mode,
                trace_id,
            )

            # Update span attributes with final decision metadata
            current_span = tracing.get_current_span()
            if current_span:
                current_span.set_attribute("decision_id", decision.decision_id)
                current_span.set_attribute("action_count", len(decision.actions))
                current_span.set_attribute("latency_ms", latency * 1000)
                current_span.set_attribute("degraded_mode", degraded_mode)

            with tracing.span("delivery.route", attributes={"action_count": len(decision.actions)}):
                self.delivery_orchestrator.deliver(decision)

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

    def _check_degraded_mode(self) -> bool:
        """
        Check if any dependencies are unavailable (circuit breaker open).

        Per PRD Section NFR-6, returns True if any critical dependency is unavailable.
        """
        # Check circuit breaker states (simplified - in production, check actual breaker states)
        # For now, we'll detect degraded mode during actual calls
        return False

    def _emit_decision_receipt(
        self,
        decision: MMMDecision,
        policy_snapshot: Optional[Any],
        degraded_mode: bool,
        policy_stale: bool,
    ) -> bool:
        """
        Emit decision receipt to ERIS synchronously per PRD Section FR-12.

        Receipt must include all ERIS schema fields:
        - receipt_id, gate_id="mmm", schema_version, policy_version_ids, snapshot_hash
        - timestamp_utc, timestamp_monotonic_ms, evaluation_point
        - inputs, decision_status, decision_rationale, decision_badges
        - result, actor_repo_id, actor_machine_fingerprint, actor_type
        - evidence_handles, degraded flag, signature (Ed25519 signed)
        """
        import hashlib
        import asyncio

        try:
            # Generate receipt ID
            receipt_id = f"mmm-{decision.decision_id}"

            # Get policy metadata
            policy_version_ids = (
                policy_snapshot.version_ids if policy_snapshot else [f"pol-{decision.tenant_id[:4]}-v1"]
            )
            snapshot_hash = (
                f"sha256:{hashlib.sha256(policy_snapshot.snapshot_id.encode()).hexdigest()}"
                if policy_snapshot
                else f"sha256:{hashlib.sha256(decision.policy_snapshot_id.encode()).hexdigest()}"
            )

            # Build receipt payload
            now_utc = datetime.now(timezone.utc)
            receipt = {
                "receipt_id": receipt_id,
                "gate_id": "mmm",
                "schema_version": "v1",
                "policy_version_ids": policy_version_ids,
                "snapshot_hash": snapshot_hash,
                "timestamp_utc": now_utc.isoformat() + "Z",
                "timestamp_monotonic_ms": int(time.perf_counter() * 1000),
                "evaluation_point": "pre-commit",  # Default, could be from context
                "inputs": {
                    "tenant_id": decision.tenant_id,
                    "actor_id": decision.actor_id,
                    "actor_type": decision.actor_type.value,
                    "signal_id": decision.context.source_event.get("signal_id") if hasattr(decision.context, "source_event") else None,
                },
                "decision_status": "pass" if decision.actions else "warn",
                "decision_rationale": f"MMM decision: {len(decision.actions)} actions generated",
                "decision_badges": ["mmm_engine"],
                "result": {
                    "action_count": len(decision.actions),
                    "action_types": [a.type.value for a in decision.actions],
                },
                "actor_repo_id": decision.context.repo_id or decision.tenant_id,
                "actor_machine_fingerprint": None,  # Optional
                "actor_type": decision.actor_type.value,
                "evidence_handles": [],
                "degraded": degraded_mode or policy_stale,
                "tenant_id": decision.tenant_id,  # ERIS-specific field
            }

            # Emit receipt synchronously (blocking call) while avoiding unawaited coroutine warnings.
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # Schedule fire-and-forget on the running loop
                task = loop.create_task(self.eris.emit_receipt(receipt))
                task.add_done_callback(lambda t: t.exception() if t.exception() else None)
                receipt_id_result = None
            else:
                # Isolated loop to run the coroutine to completion
                tmp_loop = asyncio.new_event_loop()
                try:
                    receipt_id_result = tmp_loop.run_until_complete(self.eris.emit_receipt(receipt))
                finally:
                    tmp_loop.close()

            if receipt_id_result:
                logger.debug("Decision receipt emitted: %s", receipt_id_result)
                return True
            else:
                logger.warning("Decision receipt emission failed (non-blocking)")
                return False

        except Exception as exc:
            # Log but don't block response per PRD FR-12
            logger.error("Failed to emit decision receipt: %s", exc, exc_info=True)
            return False

    def _evaluate_playbooks(
        self, context: MMMContext, playbooks: list[Playbook], degraded_mode: bool = False
    ) -> list[MMMAction]:
        actions: list[MMMAction] = []
        score_lookup: dict[str, float] = {}
        now = datetime.now(timezone.utc)
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
            playbook_actions = self.action_composer.compose_actions(
                playbook.name, playbook.actions, context, degraded_mode
            )

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

    def _get_actor_preferences_cached(
        self, db: Session, tenant_id: str, actor_id: str
    ) -> Optional[ActorPreferences]:
        """Get actor preferences with 5min TTL cache."""
        cache_key = f"{tenant_id}:{actor_id}"
        now = time.time()

        # Check cache
        if cache_key in self._preference_cache:
            preferences, cached_at = self._preference_cache[cache_key]
            if now - cached_at < self._preference_cache_ttl:
                return preferences

        # Fetch from database
        repo = ActorPreferencesRepository(db)
        preferences = repo.get_preferences(tenant_id, actor_id)

        # Update cache
        self._preference_cache[cache_key] = (preferences, now)

        return preferences

    def get_actor_preferences(
        self, tenant_id: str, actor_id: str, db: Session
    ) -> Optional[ActorPreferences]:
        """Get actor preferences."""
        repo = ActorPreferencesRepository(db)
        return repo.get_preferences(tenant_id, actor_id)

    def update_actor_preferences(
        self,
        tenant_id: str,
        actor_id: str,
        request: ActorPreferencesUpdateRequest,
        db: Session,
    ) -> Optional[ActorPreferences]:
        """Update actor preferences."""
        repo = ActorPreferencesRepository(db)
        updates = request.model_dump(exclude_unset=True)
        preferences = repo.update_preferences(tenant_id, actor_id, updates)
        # Invalidate cache
        cache_key = f"{tenant_id}:{actor_id}"
        self._preference_cache.pop(cache_key, None)
        return preferences

    def snooze_actor_preferences(
        self,
        tenant_id: str,
        actor_id: str,
        request: ActorPreferencesSnoozeRequest,
        db: Session,
    ) -> Optional[ActorPreferences]:
        """Snooze actor preferences."""
        from datetime import datetime, timezone, timedelta
        repo = ActorPreferencesRepository(db)

        # Calculate snooze_until
        if request.until:
            snooze_until = request.until
        elif request.duration_hours:
            snooze_until = datetime.now(timezone.utc) + timedelta(
                hours=request.duration_hours
            )
        else:
            raise ValueError("Either 'until' or 'duration_hours' must be provided")

        updates = {"snooze_until": snooze_until}
        preferences = repo.update_preferences(tenant_id, actor_id, updates)
        # Invalidate cache
        cache_key = f"{tenant_id}:{actor_id}"
        self._preference_cache.pop(cache_key, None)
        return preferences

    def get_tenant_policy(
        self, tenant_id: str, db: Session
    ) -> Optional[TenantMMMPolicy]:
        """Get tenant MMM policy."""
        repo = TenantPolicyRepository(db)
        return repo.get_policy(tenant_id)

    def update_tenant_policy(
        self,
        tenant_id: str,
        request: TenantMMMPolicyUpdateRequest,
        db: Session,
        admin_user_id: Optional[str] = None,
    ) -> Optional[TenantMMMPolicy]:
        """Update tenant MMM policy."""
        repo = TenantPolicyRepository(db)
        before = repo.get_policy(tenant_id)
        updates = request.model_dump(exclude_unset=True)
        policy = repo.update_policy(tenant_id, updates)
        # Emit admin config receipt
        if policy:
            self._emit_admin_config_receipt("tenant_policy_update", tenant_id, policy)
        # Audit logging
        if admin_user_id and policy:
            AuditLogger.log_admin_action(
                admin_user_id=admin_user_id,
                action="tenant_policy_update",
                resource_type="tenant_policy",
                resource_id=tenant_id,
                before_state=before.model_dump() if before else None,
                after_state=policy.model_dump(),
            )
        return policy

    def record_dual_channel_approval(
        self, action_id: str, actor_id: str, is_first: bool, db: Session
    ) -> Optional[DualChannelApproval]:
        """Record dual-channel approval (first or second)."""
        repo = DualChannelApprovalRepository(db)
        if is_first:
            return repo.record_first_approval(action_id, actor_id)
        else:
            return repo.record_second_approval(action_id, actor_id)

    def get_dual_channel_approval_status(
        self, action_id: str, db: Session
    ) -> Optional[DualChannelApproval]:
        """Get dual-channel approval status."""
        repo = DualChannelApprovalRepository(db)
        return repo.get_approval(action_id)

    def list_experiments(
        self, tenant_id: str, status: Optional[str], db: Session
    ) -> List[dict]:
        """List experiments for tenant."""
        repo = ExperimentRepository(db)
        return repo.list_experiments(tenant_id, status)

    def create_experiment(self, experiment: dict, db: Session) -> dict:
        """Create experiment."""
        repo = ExperimentRepository(db)
        return repo.save_experiment(experiment)

    def update_experiment(
        self, tenant_id: str, experiment_id: str, updates: dict, db: Session
    ) -> Optional[dict]:
        """Update experiment."""
        repo = ExperimentRepository(db)
        return repo.update_experiment(tenant_id, experiment_id, updates)

    def activate_experiment(
        self, tenant_id: str, experiment_id: str, db: Session
    ) -> Optional[dict]:
        """Activate experiment."""
        repo = ExperimentRepository(db)
        return repo.activate_experiment(tenant_id, experiment_id)

    def deactivate_experiment(
        self, tenant_id: str, experiment_id: str, db: Session
    ) -> Optional[dict]:
        """Deactivate experiment."""
        repo = ExperimentRepository(db)
        return repo.deactivate_experiment(tenant_id, experiment_id)

    def get_tenant_metrics(
        self,
        tenant_id: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        db: Session,
    ) -> dict:
        """Get summary metrics for tenant (aggregate counts only, no actor-level detail)."""
        from sqlalchemy import func, and_

        # Query decisions
        decision_count = (
            db.query(func.count(DecisionModel.decision_id))
            .filter(DecisionModel.tenant_id == tenant_id)
            .scalar() or 0
        )

        # Query actions by type
        action_counts = (
            db.query(ActionModel.type, func.count(ActionModel.action_id))
            .join(DecisionModel)
            .filter(DecisionModel.tenant_id == tenant_id)
            .group_by(ActionModel.type)
            .all()
        )
        actions_by_type = {action_type: count for action_type, count in action_counts}

        # Query outcomes by result
        outcome_counts = (
            db.query(OutcomeModel.result, func.count(OutcomeModel.outcome_id))
            .join(DecisionModel)
            .filter(DecisionModel.tenant_id == tenant_id)
            .group_by(OutcomeModel.result)
            .all()
        )
        outcomes_by_result = {result: count for result, count in outcome_counts}

        return {
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
            "aggregates": {
                "decisions_total": decision_count,
                "actions_total": sum(actions_by_type.values()),
                "actions_by_type": {
                    "mirror": actions_by_type.get("mirror", 0),
                    "mentor": actions_by_type.get("mentor", 0),
                    "multiplier": actions_by_type.get("multiplier", 0),
                },
                "outcomes_total": sum(outcomes_by_result.values()),
                "outcomes_by_result": {
                    "accepted": outcomes_by_result.get("accepted", 0),
                    "ignored": outcomes_by_result.get("ignored", 0),
                    "dismissed": outcomes_by_result.get("dismissed", 0),
                },
            },
        }

    def _emit_admin_config_receipt(
        self, action: str, tenant_id: str, resource: Any
    ) -> None:
        """Emit admin configuration receipt via ERIS."""
        try:
            receipt = {
                "receipt_id": f"admin-{uuid.uuid4().hex[:16]}",
                "gate_id": "mmm",
                "schema_version": "v1",
                "admin_action": action,
                "tenant_id": tenant_id,
                "resource_id": getattr(resource, "policy_id", None) or getattr(resource, "playbook_id", None),
                "timestamp_utc": datetime.now(timezone.utc).isoformat() + "Z",
            }
            asyncio.run(self.eris.emit_receipt(receipt))
        except Exception as exc:
            logger.warning("Failed to emit admin config receipt: %s", exc)

    def _emit_outcome_receipt(self, outcome: MMMOutcome) -> None:
        try:
            payload = {
                "receipt_id": f"outcome-{outcome.decision_id}-{outcome.action_id}",
                "tenant_id": outcome.tenant_id,
                "gate_id": "mmm",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
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
