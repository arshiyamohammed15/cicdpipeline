"""
Runbooks for ZeroUI Observability Layer.

Phase 4 - OBS-16: Runbooks RB-1..RB-5 + On-call Playbook

Operational runbooks for error spikes, latency regression, retrieval quality,
bias detection, and alert flood control.
"""

from .oncall_playbook import OnCallPlaybook
from .runbook_executor import RunbookExecutor
from .runbook_rb1_error_spike import RunbookRB1ErrorSpike
from .runbook_rb2_latency_regression import RunbookRB2LatencyRegression
from .runbook_rb3_retrieval_quality import RunbookRB3RetrievalQuality
from .runbook_rb4_bias_spike import RunbookRB4BiasSpike
from .runbook_rb5_alert_flood import RunbookRB5AlertFlood

__all__ = [
    "RunbookExecutor",
    "RunbookRB1ErrorSpike",
    "RunbookRB2LatencyRegression",
    "RunbookRB3RetrievalQuality",
    "RunbookRB4BiasSpike",
    "RunbookRB5AlertFlood",
    "OnCallPlaybook",
]
