"""
Configuration models for MMM Engine.

Per PRD Phase 5, includes all service URL environment variables and feature flags.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class MMMSettings(BaseSettings):
    """Service-level configuration with all service URLs and feature flags."""

    # Service metadata
    service_name: str = Field(default="MMM Engine")
    service_version: str = Field(default="0.1.0")
    cors_allow_origins: list[str] = Field(default=["*"])
    observability_mode: str = Field(default="prometheus")

    # Service URLs (Phase 1)
    iam_service_url: str = Field(default="http://localhost:8001/iam/v1")
    eris_service_url: str = Field(default="http://localhost:8007")
    llm_gateway_service_url: str = Field(default="http://localhost:8006")
    policy_service_url: str = Field(default="http://localhost:8003")
    data_governance_service_url: str = Field(default="http://localhost:8002")
    ubi_service_url: str = Field(default="http://localhost:8009")

    # Redis configuration (Phase 3)
    redis_url: str = Field(default="redis://localhost:6379")

    # OpenTelemetry configuration (Phase 3)
    otlp_exporter_endpoint: str = Field(default="")

    # Timeouts (per PRD Section 12)
    iam_timeout_seconds: float = Field(default=2.0)
    eris_timeout_seconds: float = Field(default=2.0)
    llm_gateway_timeout_seconds: float = Field(default=3.0)
    policy_timeout_seconds: float = Field(default=0.5)
    data_governance_timeout_seconds: float = Field(default=0.5)
    ubi_timeout_seconds: float = Field(default=1.0)

    # Circuit breaker configuration
    circuit_breaker_failure_threshold: int = Field(default=5)
    circuit_breaker_recovery_timeout: float = Field(default=60.0)

    # Feature flags
    enable_actor_preferences: bool = Field(default=True)
    enable_experiments: bool = Field(default=True)
    enable_dual_channel: bool = Field(default=True)
    enable_distributed_tracing: bool = Field(default=True)
    enable_redis_fatigue: bool = Field(default=True)

    # Data retention configuration (Phase 3)
    default_decision_retention_days: int = Field(default=90)
    default_outcome_retention_days: int = Field(default=365)

    # Audit logging configuration (Phase 3)
    audit_log_file: str = Field(default="/var/log/mmm_engine/audit.log")

    class Config:
        env_prefix = "MMM_"
        case_sensitive = False


settings = MMMSettings()


