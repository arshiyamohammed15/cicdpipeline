"""
ZeroUI Observability Layer - Alerting & Noise Control (Phase 2).

Implements:
- OBS-10: Alert Config Contract + Loader
- OBS-11: Burn-rate Alert Engine (Multi-window) - Ticket Mode
- OBS-12: Noise Control (Dedup, Rate-limit, Suppression) + FPR SLI
"""

from .alert_config import AlertConfig, AlertConfigLoader, load_alert_config
from .burn_rate_engine import AlertEvaluationResult, BurnRateAlertEngine, BurnRateResult
from .integration import ObservabilityAlertingService
from .noise_control import AlertFingerprint, NoiseControlProcessor

__all__ = [
    "AlertConfig",
    "AlertConfigLoader",
    "load_alert_config",
    "BurnRateAlertEngine",
    "BurnRateResult",
    "AlertEvaluationResult",
    "NoiseControlProcessor",
    "AlertFingerprint",
    "ObservabilityAlertingService",
]
