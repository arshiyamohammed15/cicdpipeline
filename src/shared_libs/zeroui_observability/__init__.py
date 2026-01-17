"""
ZeroUI Observability Layer

This module provides the complete observability layer for ZeroUI, including:
- Phase 0: Contracts & Correlation (event envelope, schemas, trace propagation)
- Phase 1: Telemetry Backbone (SLI calculator, dashboards, collector)
- Phase 2: Alerting & Noise Control (burn-rate alerts, noise control)
- Phase 3: Forecast & Prevent-First (time-to-breach forecasting, prevent-first actions)
- Phase 4: Replay & Continuous Improvement (replay bundles, runbooks, acceptance tests)

Agents:
- OBS-A1: Telemetry Emitter Agent (contracts, schemas, trace propagation)
- OBS-A2: Telemetry Contract Guardian Agent (schema validation, redaction)
- OBS-A3: Telemetry Store Router (storage routing)
- OBS-A4: SLI & Evaluation Builder Agent (SLI computation)
- OBS-A5: Burn-Rate Alert & Noise Control Agent (alerting)
- OBS-A6: Forecast & Prevent Agent (forecasting and prevent-first)
"""

__version__ = "0.4.0"
