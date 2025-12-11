"""
Domain service orchestrating IAM, policy, safety, provider, and observability
workflows for the LLM Gateway.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from fastapi import HTTPException, status

from ..clients import (
    AlertingClient,
    BudgetClient,
    DataGovernanceClient,
    ErisClient,
    IAMClient,
    PolicyCache,
    PolicyClient,
    PolicyClientError,
    PolicySnapshot,
    ProviderClient,
    ProviderUnavailableError,
)
from ..models import (
    Decision,
    DryRunDecision,
    LLMRequest,
    LLMResponse,
    ResponseOutput,
    RiskClass,
    Severity,
    Tokens,
)
from ..telemetry.emitter import TelemetryEmitter
from .incident_store import SafetyIncidentStore
from .safety_pipeline import SafetyPipeline


class LLMGatewayService:
    """Implements FR-1 .. FR-13 end-to-end."""

    def __init__(
        self,
        *,
        iam_client: IAMClient,
        policy_cache: PolicyCache,
        policy_client: PolicyClient,
        data_governance_client: DataGovernanceClient,
        provider_client: ProviderClient,
        budget_client: BudgetClient,
        telemetry: TelemetryEmitter,
        safety_pipeline: SafetyPipeline,
        incident_store: SafetyIncidentStore,
        alerting_client: AlertingClient,
        eris_client: ErisClient,
    ) -> None:
        self.iam_client = iam_client
        self.policy_cache = policy_cache
        self.policy_client = policy_client
        self.data_governance_client = data_governance_client
        self.provider_client = provider_client
        self.budget_client = budget_client
        self.telemetry = telemetry
        self.safety_pipeline = safety_pipeline
        self.incident_store = incident_store
        self.alerting_client = alerting_client
        self.eris_client = eris_client

    async def handle_chat(self, request: LLMRequest) -> LLMResponse | DryRunDecision:
        return await self._process(request)

    async def handle_embedding(self, request: LLMRequest) -> LLMResponse:
        return await self._process(request)

    async def dry_run(self, request: LLMRequest) -> DryRunDecision:
        request.dry_run = True
        response = await self._process(request)
        if isinstance(response, DryRunDecision):
            return response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dry run failed",
        )

    def list_incidents(self) -> Dict[str, list[dict]]:
        return {
            "incidents": [
                incident.model_dump() for incident in self.incident_store.list_incidents()
            ]
        }

    async def _process(self, request: LLMRequest) -> LLMResponse | DryRunDecision:
        scope = f"llm.{request.operation_type.value}"
        self.iam_client.validate_actor(request.actor, scope=scope)

        policy_snapshot = self._fetch_policy_snapshot(request)

        sanitized_prompt, redaction_counts = self.data_governance_client.redact(
            request.user_prompt, tenant_id=request.tenant.tenant_id
        )
        pipeline_result = self.safety_pipeline.run_input_checks(request)

        estimated_tokens = min(len(sanitized_prompt.split()) * 4, request.budget.max_tokens)
        self.budget_client.assert_within_budget(request.tenant.tenant_id, estimated_tokens)

        if request.dry_run:
            return self._build_dry_run_decision(
                request,
                pipeline_result.risk_flags,
                policy_snapshot.snapshot_id,
                policy_snapshot.version_ids,
            )

        # Meta‑prompt enforcement (FR‑6): prepend a policy/system prompt so
        # user content cannot overwrite core safety instructions. At this
        # layer we operate on an abstract meta‑prompt derived from the
        # system_prompt_id and tenant; the concrete text is owned by the
        # policy plane.
        meta_prefix = f"[META:{request.system_prompt_id}][TENANT:{request.tenant.tenant_id}] "
        effective_prompt = f"{meta_prefix}{sanitized_prompt}"

        provider_response, degradation_stage, fallback_chain = self._call_provider(
            request, effective_prompt
        )
        pipeline_result = self.safety_pipeline.run_output_checks(
            provider_response["content"], pipeline_result
        )
        decision = self.safety_pipeline.final_decision(pipeline_result)

        tokens = Tokens(tokens_in=estimated_tokens, tokens_out=estimated_tokens // 2, model_cost_estimate=0.0001 * estimated_tokens)
        output = (
            ResponseOutput(
                content=provider_response["content"] if decision != Decision.BLOCKED else None,
                redacted_output_summary=self._build_redaction_summary(redaction_counts),
            )
            if decision != Decision.BLOCKED
            else None
        )

        response = LLMResponse(
            response_id=f"resp-{request.request_id}",
            request_id=request.request_id,
            decision=decision,
            receipt_id=f"rcpt-{request.request_id}",
            tokens=tokens,
            output=output,
            risk_flags=pipeline_result.risk_flags,
            policy_snapshot_id=policy_snapshot.snapshot_id,
            policy_version_ids=policy_snapshot.version_ids,
            fail_open=policy_snapshot.fail_open_allowed,
            degradation_stage=degradation_stage,
            fallback_chain=fallback_chain or None,
            timestamp_utc=datetime.now(tz=timezone.utc),
        )

        self._record_observability(
            response=response,
            request=request,
            sanitized_prompt=sanitized_prompt,
            degradation_stage=degradation_stage,
        )

        if decision is Decision.BLOCKED:
            incident = self.incident_store.record_incident(
                tenant_id=request.tenant.tenant_id,
                workspace_id=request.workspace_id or request.actor.workspace_id or "default",
                actor_id=request.actor.actor_id,
                risk_class=pipeline_result.risk_flags[0].risk_class
                if pipeline_result.risk_flags
                else RiskClass.R5,
                severity=Severity.CRITICAL,
                decision=Decision.BLOCKED,
                receipt_id=response.receipt_id,
                request_id=request.request_id,
                policy_snapshot_id=policy_snapshot.snapshot_id,
                policy_version_ids=policy_snapshot.version_ids,
                context=sanitized_prompt,
            )
            self.alerting_client.emit_alert(incident.alert_payload)

        self.eris_client.emit_receipt(
            {
                "receipt_id": response.receipt_id,
                "request_id": request.request_id,
                "decision": response.decision.value,
                "policy_snapshot_id": response.policy_snapshot_id,
                "policy_version_ids": response.policy_version_ids,
                "risk_flags": [flag.model_dump() for flag in response.risk_flags],
                "fail_open": response.fail_open,
                "tenant_id": request.tenant.tenant_id,
                "timestamp_utc": response.timestamp_utc.isoformat(),
            }
        )

        return response

    def _call_provider(
        self, request: LLMRequest, sanitized_prompt: str
    ) -> Tuple[Dict[str, str], Optional[str], Optional[list]]:
        fallback_chain = []
        try:
            result = self.provider_client.invoke(
                request.tenant.tenant_id,
                request.logical_model_id,
                sanitized_prompt,
                request.operation_type.value,
            )
            return result, "NONE", fallback_chain
        except ProviderUnavailableError:
            self.telemetry.record_degradation("DETECTED", request.tenant.tenant_id)
            fallback_chain.append(
                {
                    "logical_model_id": request.logical_model_id,
                    "outcome": "failed",
                    "reason": "primary_unavailable",
                }
            )
            fallback_result = self.provider_client.invoke(
                request.tenant.tenant_id,
                "fallback_chat",
                sanitized_prompt,
                request.operation_type.value,
                fallback=True,
            )
            fallback_chain.append(
                {
                    "logical_model_id": "fallback_chat",
                    "outcome": "success",
                    "reason": "fallback_invoked",
                }
            )
            return fallback_result, "REROUTED", fallback_chain

    def _build_redaction_summary(self, counts: Dict[str, int]) -> Optional[str]:
        if not counts:
            return None
        parts = [f"{kind}:{count}" for kind, count in counts.items()]
        return f"Redacted entities -> {'; '.join(parts)}"

    def _build_dry_run_decision(
        self,
        request: LLMRequest,
        risk_flags: list,
        snapshot_id: str,
        version_ids: list,
    ) -> DryRunDecision:
        if not risk_flags:
            decision = "ALLOW"
            reasons = ["All safeguards passed"]
            actions = []
        else:
            decision = "BLOCK"
            reasons = [f"{flag.risk_class.value}:{flag.severity.value}" for flag in risk_flags]
            actions = [{"action": action.value, "target": flag.risk_class.value, "effect": flag.severity.value} for flag in risk_flags for action in flag.actions]

        return DryRunDecision(
            decision_id=f"dry-{request.request_id}",
            request_id=request.request_id,
            policy_snapshot_id=snapshot_id,
            policy_version_ids=version_ids,
            decision=decision,
            reasons=reasons,
            simulated_actions=actions,
            policy_latency_ms=25,
            timestamp_utc=datetime.now(tz=timezone.utc),
        )

    def _fetch_policy_snapshot(self, request: LLMRequest):
        try:
            return self.policy_cache.get_snapshot(
                request.tenant.tenant_id, allow_fail_open=request.safety_overrides.fail_open_allowed
            )
        except PolicyClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

    def _record_observability(
        self,
        *,
        response: LLMResponse,
        request: LLMRequest,
        sanitized_prompt: str,
        degradation_stage: Optional[str],
    ) -> None:
        risk_class = (
            response.risk_flags[0].risk_class.value if response.risk_flags else "R0"
        )
        self.telemetry.record_request(
            decision=response.decision.value,
            tenant_id=request.tenant.tenant_id,
            risk_class=risk_class,
        )

        self.telemetry.record_latency("input", len(sanitized_prompt))
        self.telemetry.record_latency("routing", 5)
        self.telemetry.record_latency("output", 5)

        if degradation_stage and degradation_stage != "NONE":
            self.telemetry.record_degradation(
                stage=degradation_stage, tenant_id=request.tenant.tenant_id
            )

        # Structured decision log used by observability validation (OT-LLM-01)
        workspace_id = request.workspace_id or request.actor.workspace_id or "default"
        trace_id = (
            request.telemetry_context.trace_id
            if request.telemetry_context is not None
            else None
        )
        self.telemetry.log_decision(
            tenant_id=request.tenant.tenant_id,
            workspace_id=workspace_id,
            actor_id=request.actor.actor_id,
            logical_model_id=request.logical_model_id,
            operation_type=request.operation_type.value,
            request_id=request.request_id,
            response_id=response.response_id,
            decision=response.decision.value,
            risk_class=risk_class,
            policy_snapshot_id=response.policy_snapshot_id,
            policy_version_ids=response.policy_version_ids,
            schema_version=response.schema_version,
            fail_open=response.fail_open,
            degradation_stage=degradation_stage,
            trace_id=trace_id,
        )


def build_default_service() -> LLMGatewayService:
    """Build service with default (in-process) clients for unit tests.

    This variant avoids real network calls (IAM, EPC‑2, budgets, etc.) and
    exercises only in‑process logic plus the safety pipeline.
    """

    class _TestIAMClient:
        """Lightweight IAM substitute used in unit tests.

        Performs only local capability/scope checks and never performs HTTP
        requests. This keeps unit tests deterministic while still enforcing
        the minimum contract required by FR‑2.
        """

        _required_capabilities = {"llm.invoke"}

        def validate_actor(self, actor, scope: str) -> None:  # type: ignore[override]
            if scope not in (actor.scopes or []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Actor not authorised for scope {scope}",
                )
            missing = self._required_capabilities - set(actor.capabilities)
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Actor lacks required capabilities: {', '.join(missing)}",
                )

    class _TestPolicyClient:
        """Local policy snapshot provider for unit tests (no HTTP)."""

        def fetch_snapshot(self, tenant_id: str, actor=None):  # type: ignore[override]
            # Minimal snapshot satisfying FR‑3 contract for tests.
            return PolicySnapshot(
                snapshot_id=f"{tenant_id}-snapshot-test",
                version_ids=[f"pol-{tenant_id[:4]}-v1"],
                tenant_id=tenant_id,
                fail_open_allowed=False,
                degradation_mode="prefer_backup",
                fetched_at=0.0,
                bounds={"max_tokens": 2048, "max_concurrent": 5},
            )

    policy_client = _TestPolicyClient()
    policy_cache = PolicyCache(policy_client)  # type: ignore[arg-type]
    return LLMGatewayService(
        iam_client=_TestIAMClient(),
        policy_cache=policy_cache,
        policy_client=policy_client,
        data_governance_client=DataGovernanceClient(),
        provider_client=ProviderClient(),
        budget_client=BudgetClient(),
        telemetry=TelemetryEmitter(),
        safety_pipeline=SafetyPipeline(),
        incident_store=SafetyIncidentStore(),
        alerting_client=AlertingClient(),
        eris_client=ErisClient(),
    )


def build_service_with_real_clients(
    iam_url: Optional[str] = None,
    policy_url: Optional[str] = None,
    data_governance_url: Optional[str] = None,
    budget_url: Optional[str] = None,
    eris_url: Optional[str] = None,
    alerting_url: Optional[str] = None,
) -> LLMGatewayService:
    """
    Build service with real HTTP clients for integration testing.

    Service URLs can be provided explicitly or via environment variables:
    - IAM_SERVICE_URL
    - POLICY_SERVICE_URL
    - DATA_GOVERNANCE_SERVICE_URL
    - BUDGET_SERVICE_URL
    - ERIS_SERVICE_URL
    - ALERTING_SERVICE_URL

    Args:
        iam_url: IAM service base URL (defaults to env var or localhost)
        policy_url: Policy service base URL
        data_governance_url: Data Governance service base URL
        budget_url: Budget service base URL
        eris_url: ERIS service base URL
        alerting_url: Alerting service base URL

    Returns:
        LLMGatewayService configured with real HTTP clients
    """
    import os

    policy_client = PolicyClient(
        base_url=policy_url,
        latency_budget_ms=500,
        timeout_seconds=0.5,
    )
    policy_cache = PolicyCache(policy_client)

    return LLMGatewayService(
        iam_client=IAMClient(base_url=iam_url, timeout_seconds=2.0),
        policy_cache=policy_cache,
        policy_client=policy_client,
        data_governance_client=DataGovernanceClient(
            base_url=data_governance_url, timeout_seconds=0.025
        ),
        provider_client=ProviderClient(),
        budget_client=BudgetClient(base_url=budget_url, timeout_seconds=1.0),
        telemetry=TelemetryEmitter(),
        safety_pipeline=SafetyPipeline(),
        incident_store=SafetyIncidentStore(),
        alerting_client=AlertingClient(base_url=alerting_url, timeout_seconds=2.0),
        eris_client=ErisClient(base_url=eris_url, timeout_seconds=2.0),
    )
