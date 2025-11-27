"""
Configuration helpers for the Health & Reliability Monitoring service.

Provides strongly-typed settings with sane defaults while allowing overrides via
environment variables to align with ZeroUI deployment standards.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List


def _env(key: str, default: str) -> str:
    """Read environment variable with default fallback."""
    return os.getenv(key, default)


def _env_list(key: str, default: str = "") -> List[str]:
    """Split comma-delimited environment variable into list."""
    raw = os.getenv(key, default)
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class ServiceSettings:
    """Static service metadata."""

    name: str = "health-reliability-monitoring"
    version: str = _env("HEALTH_RELIABILITY_MONITORING_VERSION", "0.1.0")
    environment: str = _env("ENVIRONMENT", "development")
    host: str = _env("HOSTNAME", os.getenv("COMPUTERNAME", "localhost"))
    port: int = int(_env("HEALTH_RELIABILITY_MONITORING_HTTP_PORT", "8095"))


@dataclass(frozen=True)
class DatabaseSettings:
    """Database configuration for component registry & health snapshots."""

    url: str = _env("HEALTH_RELIABILITY_MONITORING_DATABASE_URL", "sqlite:///./health_reliability_monitoring.db")
    echo_sql: bool = _env("HEALTH_RELIABILITY_MONITORING_DB_ECHO", "false").lower() == "true"
    pool_size: int = int(_env("HEALTH_RELIABILITY_MONITORING_DB_POOL_SIZE", "10"))
    max_overflow: int = int(_env("HEALTH_RELIABILITY_MONITORING_DB_MAX_OVERFLOW", "20"))


@dataclass(frozen=True)
class TelemetrySettings:
    """Telemetry ingestion & export configuration."""

    otel_exporter_endpoint: str = _env("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    ingestion_topics: List[str] = field(
        default_factory=lambda: _env_list(
            "HEALTH_RELIABILITY_MONITORING_INGEST_TOPICS",
            "ccp4.metrics,ccp4.probes,ccp4.heartbeats",
        )
    )
    ingestion_batch_size: int = int(_env("HEALTH_RELIABILITY_MONITORING_INGEST_BATCH_SIZE", "500"))
    ingestion_interval_ms: int = int(_env("HEALTH_RELIABILITY_MONITORING_INGEST_INTERVAL_MS", "1000"))
    label_cardinality_limit: int = int(_env("HEALTH_RELIABILITY_MONITORING_LABEL_CARDINALITY_LIMIT", "100"))


@dataclass(frozen=True)
class PolicySettings:
    """Configuration & Policy (EPC-3) integration settings."""

    base_url: str = _env("EPC3_BASE_URL", "http://localhost:8083")
    timeout_seconds: int = int(_env("EPC3_TIMEOUT_SECONDS", "5"))
    cache_ttl_seconds: int = int(_env("EPC3_CACHE_TTL_SECONDS", "60"))


@dataclass(frozen=True)
class EventSettings:
    """Eventing targets for EPC-4, PM-7, and other consumers."""

    alert_topic: str = _env("EPC4_ALERT_TOPIC", "alerts.health_state")
    eris_topic: str = _env("PM7_ERIS_TOPIC", "evidence.health_receipts")
    safe_to_act_topic: str = _env("EPC8_SAFE_TO_ACT_TOPIC", "deployment.safe_to_act")


@dataclass(frozen=True)
class SafeToActSettings:
    """Safe-to-Act policy behavior."""

    default_mode: str = _env("HEALTH_RELIABILITY_MONITORING_SAFE_DEFAULT_MODE", "read_only")
    telemetry_stale_seconds: int = int(_env("HEALTH_RELIABILITY_MONITORING_SAFE_STALE_SECONDS", "120"))
    deny_on_unknown: bool = (
        _env("HEALTH_RELIABILITY_MONITORING_SAFE_DENY_ON_UNKNOWN", "true").lower() == "true"
    )


@dataclass(frozen=True)
class Settings:
    """Aggregate service settings."""

    service: ServiceSettings = ServiceSettings()
    database: DatabaseSettings = DatabaseSettings()
    telemetry: TelemetrySettings = TelemetrySettings()
    policy: PolicySettings = PolicySettings()
    events: EventSettings = EventSettings()
    safe_to_act: SafeToActSettings = SafeToActSettings()


def load_settings() -> Settings:
    """Factory helper to construct Settings lazily."""
    return Settings()

