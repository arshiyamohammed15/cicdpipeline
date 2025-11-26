"""
Telemetry emitter that simulates observability counters defined in §14.4.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import json
import logging
import os
from typing import Dict, Iterable

try:  # Optional Prometheus client; used in production environments.
    from prometheus_client import Counter as PromCounter, Histogram
except ImportError:  # pragma: no cover - not required for unit tests
    PromCounter = None  # type: ignore[assignment]
    Histogram = None  # type: ignore[assignment]


REQUESTS_TOTAL_METRIC = (
    PromCounter(
        "epc6_requests_total",
        "LLM Gateway decisions per tenant and risk class",
        ["decision", "tenant_id", "risk_class"],
    )
    if PromCounter is not None
    else None
)
LATENCY_MS_METRIC = (
    Histogram(
        "epc6_latency_ms",
        "LLM Gateway internal latency by workflow stage (ms)",
        ["workflow"],
    )
    if Histogram is not None
    else None
)
DEGRADATION_TOTAL_METRIC = (
    PromCounter(
        "epc6_degradation_total",
        "LLM Gateway degradation events by stage and tenant",
        ["stage", "tenant_id"],
    )
    if PromCounter is not None
    else None
)
ALERTS_TOTAL_METRIC = (
    PromCounter(
        "epc6_alerts_total",
        "LLM Gateway safety alerts emitted",
        ["risk_class", "severity"],
    )
    if PromCounter is not None
    else None
)


class TelemetryEmitter:
    """
    Telemetry sink used for both tests and production.

    - In all modes it keeps an in-memory view for unit tests and tools.
    - When `LLM_GATEWAY_OBSERVABILITY_MODE=prometheus`, it also exports to
      Prometheus metrics via `prometheus_client` and emits structured JSON logs
      suitable for the observability validator.
    """

    def __init__(self) -> None:
        self.requests_total: Counter = Counter()
        self.degradation_total: Counter = Counter()
        self.alerts_total: Counter = Counter()
        self.latency_ms: Dict[str, list[int]] = defaultdict(list)
        self._use_prometheus = (
            os.getenv("LLM_GATEWAY_OBSERVABILITY_MODE", "").lower() == "prometheus"
            and REQUESTS_TOTAL_METRIC is not None
        )
        self._logger = logging.getLogger("llm_gateway")

    def record_request(self, decision: str, tenant_id: str, risk_class: str) -> None:
        key = (decision, tenant_id, risk_class)
        self.requests_total[key] += 1
        if self._use_prometheus and REQUESTS_TOTAL_METRIC is not None:
            REQUESTS_TOTAL_METRIC.labels(
                decision=decision, tenant_id=tenant_id, risk_class=risk_class
            ).inc()

    def record_latency(self, workflow: str, latency_ms: int) -> None:
        self.latency_ms[workflow].append(latency_ms)
        if self._use_prometheus and LATENCY_MS_METRIC is not None:
            # Histogram expects seconds; keep milliseconds but name makes units explicit.
            LATENCY_MS_METRIC.labels(workflow=workflow).observe(latency_ms)

    def record_degradation(self, stage: str, tenant_id: str) -> None:
        key = (stage, tenant_id)
        self.degradation_total[key] += 1
        if self._use_prometheus and DEGRADATION_TOTAL_METRIC is not None:
            DEGRADATION_TOTAL_METRIC.labels(stage=stage, tenant_id=tenant_id).inc()

    def record_alert(self, risk_class: str, severity: str) -> None:
        key = (risk_class, severity)
        self.alerts_total[key] += 1
        if self._use_prometheus and ALERTS_TOTAL_METRIC is not None:
            ALERTS_TOTAL_METRIC.labels(risk_class=risk_class, severity=severity).inc()

    # ------------------------------------------------------------------
    # Structured logging helpers
    # ------------------------------------------------------------------

    def log_decision(
        self,
        *,
        tenant_id: str,
        workspace_id: str,
        actor_id: str,
        logical_model_id: str,
        operation_type: str,
        request_id: str,
        response_id: str,
        decision: str,
        risk_class: str,
        policy_snapshot_id: str,
        policy_version_ids: list[str],
        schema_version: str,
        fail_open: bool,
        degradation_stage: str | None,
        trace_id: str | None = None,
    ) -> None:
        """
        Emit a structured JSON log entry for a gateway decision.

        Fields are aligned with §14.4 so the observability validator can
        assert coverage and detect any raw sensitive content.
        """
        payload = {
            "schema_version": schema_version,
            "tenant_id": tenant_id,
            "workspace_id": workspace_id,
            "actor_id": actor_id,
            "request_id": request_id,
            "response_id": response_id,
            "decision": decision,
            "risk_class": risk_class,
            "policy_snapshot_id": policy_snapshot_id,
            "policy_version_ids": policy_version_ids,
            "fail_open": fail_open,
            "degradation_stage": degradation_stage or "NONE",
            # Trace-style attributes for OT-LLM-01
            "logical_model_id": logical_model_id,
            "operation_type": operation_type,
            "trace_id": trace_id,
            # Convenience aliases for validator patterns (`tenant`, `actor`)
            "tenant": tenant_id,
            "actor": actor_id,
        }

        # NOTE: scrubbing of PII/secrets is expected to have been done earlier
        # in the pipeline (EPC-2 redaction + log guard). Here we just ensure
        # payload is JSON and contains the required keys.
        self._logger.info("%s", json.dumps(payload))

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def iter_prometheus_metrics(self) -> Iterable[str]:
        """
        Yield metrics lines in Prometheus text format.

        This is primarily used by observability tests and CI jobs to
        generate a log/metrics file that `validate_llm_gateway_observability.py`
        can parse. It covers the metrics defined in §14.4:
        - epc6_requests_total{decision,tenant_id,risk_class}
        - epc6_latency_ms{workflow}
        - epc6_degradation_total{stage,tenant_id}
        - epc6_alerts_total{risk_class,severity}
        """

        # Request decisions
        for (decision, tenant_id, risk_class), value in self.requests_total.items():
            yield (
                f'epc6_requests_total{{decision="{decision}",'
                f'tenant_id="{tenant_id}",risk_class="{risk_class}"}} {value}'
            )

        # Latency (export simple average per workflow for now)
        for workflow, samples in self.latency_ms.items():
            if not samples:
                continue
            avg = sum(samples) / max(len(samples), 1)
            yield f'epc6_latency_ms{{workflow="{workflow}"}} {avg:.2f}'

        # Degradation counters
        for (stage, tenant_id), value in self.degradation_total.items():
            yield (
                f'epc6_degradation_total{{stage="{stage}",tenant_id="{tenant_id}"}} {value}'
            )

        # Alerts emitted
        for (risk_class, severity), value in self.alerts_total.items():
            yield (
                f'epc6_alerts_total{{risk_class="{risk_class}",severity="{severity}"}} {value}'
            )

    def to_prometheus_text(self) -> str:
        """Return all metrics as a newline‑separated Prometheus text blob."""
        return "\n".join(self.iter_prometheus_metrics()) + "\n"

