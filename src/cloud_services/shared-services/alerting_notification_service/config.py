"""Configuration helpers for Alerting & Notification Service."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings

from config.constitution.path_utils import resolve_alerting_db_path


class ServiceSettings(BaseSettings):
    name: str = Field(default="Alerting & Notification Service")
    version: str = Field(default="1.0.0")
    environment: str = Field(default="dev")
    log_level: str = Field(default="INFO")
    allowed_origins: List[str] = Field(default_factory=list)


class PolicySettings(BaseSettings):
    config_service_url: HttpUrl = Field(default="https://config-service.local")
    iam_service_url: HttpUrl = Field(default="https://iam-service.local")
    eris_service_url: Optional[HttpUrl] = Field(default=None)  # None = stub mode
    default_dedup_minutes: int = Field(default=15, ge=1)
    default_correlation_minutes: int = Field(default=10, ge=1)
    cache_ttl_seconds: int = Field(default=60, ge=5)
    policy_bundle_path: Path = Field(default=Path("config/policies/alerting_policy.json"))
    use_api_refresh: bool = Field(default=False)  # If True, use API-based policy refresh


class NotificationSettings(BaseSettings):
    email_sender: str = Field(default="alerts@zeroui.local")
    max_retry_attempts: int = Field(default=5, ge=1)
    retry_backoff_seconds: int = Field(default=30, ge=1)
    agent_stream_buffer: int = Field(default=1024, ge=1)


class DatabaseSettings(BaseSettings):
    url: str = Field(default_factory=lambda: f"sqlite+aiosqlite:///{resolve_alerting_db_path()}")
    echo: bool = Field(default=False)


class ObservabilitySettings(BaseSettings):
    enable_tracing: bool = Field(default=True)
    metrics_namespace: str = Field(default="alerting_service")


class DependencySettings(BaseSettings):
    graph_service_url: Optional[HttpUrl] = None


class Settings(BaseSettings):
    service: ServiceSettings = ServiceSettings()
    policy: PolicySettings = PolicySettings()
    notifications: NotificationSettings = NotificationSettings()
    database: DatabaseSettings = DatabaseSettings()
    observability: ObservabilitySettings = ObservabilitySettings()
    dependency: DependencySettings = DependencySettings()


@lru_cache
def get_settings() -> Settings:
    return Settings()
