"""
Prometheus metrics for MMM Engine.
"""

from __future__ import annotations

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
    PROM_AVAILABLE = True
except Exception:  # pragma: no cover
    PROM_AVAILABLE = False
    Counter = Histogram = Gauge = None  # type: ignore
    REGISTRY = None  # type: ignore


if PROM_AVAILABLE:
    decisions_total = Counter("mmm_decisions_total", "Total MMM decisions", ["tenant_id", "actor_type"])
    actions_total = Counter("mmm_actions_total", "Total actions proposed", ["tenant_id", "action_type"])
    outcomes_total = Counter("mmm_outcomes_total", "Total outcomes recorded", ["tenant_id", "result"])
    # Enhanced latency histogram with buckets per PRD NFR-1: [0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0, 2.0]
    decision_latency = Histogram(
        "mmm_decision_latency_seconds",
        "Decision latency",
        ["tenant_id"],
        buckets=[0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0, 2.0],
    )
    latency_warning_total = Counter(
        "mmm_decision_latency_warning_total",
        "Latency SLO warnings",
        ["tenant_id", "exceeded_threshold"],
    )
    circuit_state = Gauge("mmm_circuit_state", "Circuit breaker state", ["name"])
    delivery_attempts_total = Counter("mmm_delivery_attempts_total", "Delivery attempts per channel", ["channel", "result"])
    eris_receipt_emission_total = Counter(
        "mmm_eris_receipt_emission_total",
        "ERIS receipt emission results",
        ["tenant_id", "result"],
    )


def record_decision_metrics(
    tenant_id: str,
    actor_type: str,
    actions: int,
    latency_seconds: float,
    surface: str = "ide",
) -> None:
    """
    Record decision metrics with latency SLO monitoring.

    Per PRD NFR-1:
    - IDE calls: 150ms p95 threshold
    - CI calls: 500ms p95 threshold
    """
    if not PROM_AVAILABLE:
        return
    decisions_total.labels(tenant_id, actor_type).inc()
    for _ in range(actions):
        actions_total.labels(tenant_id, "mirror").inc()
    decision_latency.labels(tenant_id).observe(latency_seconds)

    # Latency SLO enforcement
    threshold = 0.150 if surface == "ide" else 0.500  # 150ms for IDE, 500ms for CI
    if latency_seconds > threshold:
        latency_warning_total.labels(tenant_id, f"{threshold}s").inc()


def record_eris_receipt_emission(tenant_id: str, success: bool) -> None:
    """Record ERIS receipt emission result."""
    if not PROM_AVAILABLE:
        return
    result = "success" if success else "failure"
    eris_receipt_emission_total.labels(tenant_id, result).inc()


def record_outcome_metrics(tenant_id: str, result: str) -> None:
    if not PROM_AVAILABLE:
        return
    outcomes_total.labels(tenant_id, result).inc()


def set_circuit_state(name: str, state_value: int) -> None:
    if not PROM_AVAILABLE:
        return
    circuit_state.labels(name).set(state_value)


def record_delivery_attempt(channel: str, success: bool) -> None:
    if not PROM_AVAILABLE:
        return
    delivery_attempts_total.labels(channel, "success" if success else "failure").inc()


def get_metrics_text() -> str:
    if not PROM_AVAILABLE:
        return "# HELP mmm_metrics Metrics disabled\n# TYPE mmm_metrics gauge\nmmm_metrics 0\n"
    return generate_latest(REGISTRY).decode("utf-8")


