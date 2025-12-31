"""
Domain service orchestrating IAM, policy, safety, provider, and observability
workflows for the LLM Gateway.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

import anyio
from fastapi import HTTPException, status

from shared_libs.error_recovery import (
    ErrorClassifier,
    RecoveryReport,
    RetryPolicy,
    call_with_recovery_async,
)
from shared_libs.token_budget import BudgetManager, BudgetSpec
from shared_libs.token_counter import ConservativeTokenEstimator, TokenCounter

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
from ..clients.policy_client import (
    _extract_recovery,
    _extract_token_bounds,
    _load_local_policy,
)
from ..models import (
    Decision,
    DryRunDecision,
    LLMRequest,
    LLMResponse,
    OperationType,
    ResponseOutput,
    RiskClass,
    Severity,
    Tokens,
)
from ..telemetry.emitter import TelemetryEmitter
from .incident_store import SafetyIncidentStore
from .safety_pipeline import SafetyPipeline

_DEFAULT_ERROR_CLASSIFIER = ErrorClassifier()


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
        token_counter: TokenCounter,
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
        self.token_counter = token_counter

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
        await self._run_sync(self.iam_client.validate_actor, request.actor, scope)

        policy_snapshot = await self._run_sync(self._fetch_policy_snapshot, request)

        sanitized_prompt, redaction_counts = await self._run_sync(
            self.data_governance_client.redact,
            request.user_prompt,
            request.tenant.tenant_id,
        )
        pipeline_result = self.safety_pipeline.run_input_checks(request)

        # Meta-prompt enforcement (FR-6): prepend a policy/system prompt so
        # user content cannot overwrite core safety instructions.
        meta_prefix = f"[META:{request.system_prompt_id}][TENANT:{request.tenant.tenant_id}] "
        effective_prompt = f"{meta_prefix}{sanitized_prompt}"

        estimated_input_tokens = self.token_counter.count_input(effective_prompt)
        requested_output_tokens = request.budget.max_tokens
        estimated_output_tokens = self.token_counter.estimate_output(
            requested_output_tokens
        )
        budget_spec = self._resolve_budget_spec(request, policy_snapshot)
        budget_spec_payload = {
            "max_input_tokens": budget_spec.max_input_tokens,
            "max_output_tokens": budget_spec.max_output_tokens,
            "max_total_tokens": budget_spec.max_total_tokens,
            "max_tool_tokens_optional": budget_spec.max_tool_tokens_optional,
        }
        budget_decision = BudgetManager(
            estimated_input_tokens,
            estimated_output_tokens,
            budget_spec,
        )
        event_type = "llm_gateway_decision"
        trace_id = (
            request.telemetry_context.trace_id
            if request.telemetry_context is not None
            else None
        )
        if budget_decision.decision == "DENY":
            receipt_payload = {
                "receipt_id": f"rcpt-{request.request_id}",
                "request_id": request.request_id,
                "event_type": event_type,
                "decision": "deny",
                "reason_code": budget_decision.reason_code,
                "policy_snapshot_id": policy_snapshot.snapshot_id,
                "policy_version_ids": policy_snapshot.version_ids,
                "fail_open": policy_snapshot.fail_open_allowed,
                "tenant_id": request.tenant.tenant_id,
                "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
                "estimated_input_tokens": estimated_input_tokens,
                "requested_output_tokens": requested_output_tokens,
                "budget_spec": budget_spec_payload,
            }
            if trace_id:
                receipt_payload["trace_id"] = trace_id
            self.eris_client.emit_receipt(receipt_payload)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "decision": "deny",
                    "reason_code": budget_decision.reason_code,
                    "message": budget_decision.human_message,
                },
            )

        await self._run_sync(
            self.budget_client.assert_within_budget,
            request.tenant.tenant_id,
            estimated_input_tokens,
            request.workspace_id,
            request.actor.actor_id,
        )

        if request.dry_run:
            return self._build_dry_run_decision(
                request,
                pipeline_result.risk_flags,
                policy_snapshot.snapshot_id,
                policy_snapshot.version_ids,
            )


        (
            provider_response,
            degradation_stage,
            fallback_chain,
            recovery_info,
        ) = await self._call_provider(request, effective_prompt, policy_snapshot)
        pipeline_result = self.safety_pipeline.run_output_checks(
            provider_response["content"], pipeline_result
        )
        decision = self.safety_pipeline.final_decision(pipeline_result)

        tokens = Tokens(
            tokens_in=estimated_input_tokens,
            tokens_out=estimated_input_tokens // 2,
            model_cost_estimate=0.0001 * estimated_input_tokens,
        )
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

        receipt_payload = {
            "receipt_id": response.receipt_id,
            "request_id": request.request_id,
            "event_type": event_type,
            "decision": response.decision.value,
            "reason_code": budget_decision.reason_code,
            "policy_snapshot_id": response.policy_snapshot_id,
            "policy_version_ids": response.policy_version_ids,
            "risk_flags": [flag.model_dump() for flag in response.risk_flags],
            "fail_open": response.fail_open,
            "tenant_id": request.tenant.tenant_id,
            "timestamp_utc": response.timestamp_utc.isoformat(),
            "estimated_input_tokens": estimated_input_tokens,
            "requested_output_tokens": requested_output_tokens,
            "budget_spec": budget_spec_payload,
            "recovery": recovery_info,
        }
        if trace_id:
            receipt_payload["trace_id"] = trace_id
        self.eris_client.emit_receipt(receipt_payload)

        return response

    async def _run_sync(self, func, *args, **kwargs):
        if os.getenv("PYTEST_CURRENT_TEST") and os.getenv(
            "USE_REAL_SERVICES", "false"
        ).lower() != "true":
            return func(*args, **kwargs)
        return await anyio.to_thread.run_sync(func, *args, **kwargs)

    async def _call_provider(
        self,
        request: LLMRequest,
        sanitized_prompt: str,
        policy_snapshot: PolicySnapshot,
    ) -> Tuple[Dict[str, str], Optional[str], Optional[list], Dict[str, dict]]:
        fallback_chain = []
        primary_report = RecoveryReport()
        recovery_policy = self._resolve_recovery_policy(policy_snapshot)
        recovery_timeout_ms = self._resolve_recovery_timeout_ms(
            request,
            policy_snapshot,
        )

        async def invoke_primary() -> Dict[str, str]:
            return await anyio.to_thread.run_sync(
                self.provider_client.invoke,
                request.tenant.tenant_id,
                request.logical_model_id,
                sanitized_prompt,
                request.operation_type.value,
            )

        try:
            result = await call_with_recovery_async(
                invoke_primary,
                policy=recovery_policy,
                classifier=_DEFAULT_ERROR_CLASSIFIER,
                timeout_ms=recovery_timeout_ms,
                report=primary_report,
            )
            recovery_info = {"primary": primary_report.to_receipt_fields()}
            return result, "NONE", fallback_chain, recovery_info
        except ProviderUnavailableError:
            self.telemetry.record_degradation("DETECTED", request.tenant.tenant_id)
            fallback_chain.append(
                {
                    "logical_model_id": request.logical_model_id,
                    "outcome": "failed",
                    "reason": "primary_unavailable",
                }
            )
            fallback_logical_model = (
                "fallback_embedding"
                if request.operation_type is OperationType.EMBEDDING
                else "fallback_chat"
            )
            fallback_report = RecoveryReport()

            async def invoke_fallback() -> Dict[str, str]:
                return await anyio.to_thread.run_sync(
                    self.provider_client.invoke,
                    request.tenant.tenant_id,
                    fallback_logical_model,
                    sanitized_prompt,
                    request.operation_type.value,
                    fallback=True,
                )

            fallback_result = await call_with_recovery_async(
                invoke_fallback,
                policy=recovery_policy,
                classifier=_DEFAULT_ERROR_CLASSIFIER,
                timeout_ms=recovery_timeout_ms,
                report=fallback_report,
            )
            fallback_chain.append(
                {
                    "logical_model_id": fallback_logical_model,
                    "outcome": "success",
                    "reason": "fallback_invoked",
                }
            )
            recovery_info = {
                "primary": primary_report.to_receipt_fields(),
                "fallback": fallback_report.to_receipt_fields(),
            }
            return fallback_result, "REROUTED", fallback_chain, recovery_info

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

    def _resolve_budget_spec(
        self, request: LLMRequest, policy_snapshot: PolicySnapshot
    ) -> BudgetSpec:
        fallback_tokens = request.budget.max_tokens
        policy_max_tokens = policy_snapshot.bounds.get("max_tokens", fallback_tokens)
        max_input_tokens = policy_snapshot.bounds.get(
            "max_input_tokens", policy_max_tokens
        )
        max_output_tokens = policy_snapshot.bounds.get(
            "max_output_tokens", policy_max_tokens
        )
        max_total_tokens = policy_snapshot.bounds.get(
            "max_total_tokens", max_input_tokens + max_output_tokens
        )
        return BudgetSpec(
            max_input_tokens=max_input_tokens,
            max_output_tokens=max_output_tokens,
            max_total_tokens=max_total_tokens,
        )

    def _resolve_recovery_policy(self, policy_snapshot: PolicySnapshot) -> RetryPolicy:
        recovery = policy_snapshot.recovery
        max_attempts = recovery.get("max_attempts")
        base_delay_ms = recovery.get("base_delay_ms")
        max_delay_ms = recovery.get("max_delay_ms")
        if not (
            isinstance(max_attempts, int)
            and isinstance(base_delay_ms, int)
            and isinstance(max_delay_ms, int)
        ):
            local_policy = _load_local_policy()
            fallback = _extract_recovery(local_policy)
            max_attempts = fallback.get("max_attempts")
            base_delay_ms = fallback.get("base_delay_ms")
            max_delay_ms = fallback.get("max_delay_ms")
            if not (
                isinstance(max_attempts, int)
                and isinstance(base_delay_ms, int)
                and isinstance(max_delay_ms, int)
            ):
                return RetryPolicy(max_attempts=1, base_delay_ms=0, max_delay_ms=0)
        return RetryPolicy(
            max_attempts=max_attempts,
            base_delay_ms=base_delay_ms,
            max_delay_ms=max_delay_ms,
        )

    def _resolve_recovery_timeout_ms(
        self,
        request: LLMRequest,
        policy_snapshot: PolicySnapshot,
    ) -> int:
        policy_timeout = policy_snapshot.recovery.get("timeout_ms")
        if not isinstance(policy_timeout, int):
            local_policy = _load_local_policy()
            fallback = _extract_recovery(local_policy)
            policy_timeout = fallback.get("timeout_ms")
        if isinstance(policy_timeout, int):
            return min(request.budget.timeout_ms, policy_timeout)
        return request.budget.timeout_ms

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
            local_policy = _load_local_policy()
            bounds = _extract_token_bounds(local_policy)
            recovery = _extract_recovery(local_policy)
            # Minimal snapshot satisfying FR‑3 contract for tests.
            return PolicySnapshot(
                snapshot_id=f"{tenant_id}-snapshot-test",
                version_ids=[f"pol-{tenant_id[:4]}-v1"],
                tenant_id=tenant_id,
                fail_open_allowed=False,
                degradation_mode="prefer_backup",
                fetched_at=0.0,
                bounds=bounds,
                recovery=recovery,
            )

    class _TestDataGovernanceClient:
        """In-process redaction stub to avoid network calls in unit tests."""

        def redact(self, content: str, tenant_id: str = "default"):
            # Return content unchanged with empty counts; EPC-2 behavior is
            # covered by contract tests.
            return content, {}

    policy_client = _TestPolicyClient()
    policy_cache = PolicyCache(policy_client)  # type: ignore[arg-type]
    return LLMGatewayService(
        iam_client=_TestIAMClient(),
        policy_cache=policy_cache,
        policy_client=policy_client,
        data_governance_client=_TestDataGovernanceClient(),
        provider_client=ProviderClient(),
        budget_client=BudgetClient(),
        telemetry=TelemetryEmitter(),
        safety_pipeline=SafetyPipeline(),
        incident_store=SafetyIncidentStore(),
        alerting_client=AlertingClient(),
        eris_client=ErisClient(),
        token_counter=ConservativeTokenEstimator(),
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
        token_counter=ConservativeTokenEstimator(),
    )
