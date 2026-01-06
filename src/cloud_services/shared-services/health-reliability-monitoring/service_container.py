"""
Service container wiring global singletons for FastAPI dependency injection.
"""

from __future__ import annotations

from functools import lru_cache
from typing import AsyncGenerator, Generator

from sqlalchemy.orm import Session

from .config import load_settings
from .database.session import SessionLocal
from .dependencies import (
    AlertingClient,
    DeploymentClient,
    EdgeAgentClient,
    ERISClient,
    IAMClient,
    PolicyClient,
)
from .services.audit_service import AuditService
from .services.event_bus_service import EventBusService
from .services.registry_service import ComponentRegistryService
from .services.telemetry_ingestion_service import TelemetryIngestionService
from .services.evaluation_service import HealthEvaluationService
from .services.rollup_service import RollupService
from .services.slo_service import SLOService
from .services.safe_to_act_service import SafeToActService
from .services.telemetry_worker import TelemetryWorker


@lru_cache
def get_settings():
    return load_settings()


@lru_cache
def get_iam_client() -> IAMClient:
    return IAMClient()


@lru_cache
def get_policy_client() -> PolicyClient:
    settings = get_settings()
    return PolicyClient(settings.policy.base_url, timeout_seconds=settings.policy.timeout_seconds)


@lru_cache
def get_alerting_client() -> AlertingClient:
    return AlertingClient(get_settings().events.alert_topic)


@lru_cache
def get_deployment_client() -> DeploymentClient:
    return DeploymentClient(get_settings().events.safe_to_act_topic)


@lru_cache
def get_eris_client() -> ERISClient:
    return ERISClient(get_settings().events.eris_topic)


@lru_cache
def get_edge_client() -> EdgeAgentClient:
    return EdgeAgentClient()


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency for SQLAlchemy session."""
    session = SessionLocal()
    try:
        yield session
        # Commit only if a transaction was started; avoids sqlite "no transaction" errors
        if session.in_transaction():
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@lru_cache
def get_event_bus() -> EventBusService:
    return EventBusService(get_alerting_client(), get_eris_client())


@lru_cache
def get_audit_service() -> AuditService:
    return AuditService(get_event_bus())


@lru_cache
def get_telemetry_service() -> TelemetryIngestionService:
    return TelemetryIngestionService()


@lru_cache
def get_telemetry_worker() -> TelemetryWorker:
    return TelemetryWorker(get_telemetry_service(), get_policy_client(), get_event_bus())


def get_registry_service(db: Session = None) -> ComponentRegistryService:
    if db is None:
        raise RuntimeError("DB session dependency missing")
    return ComponentRegistryService(db, get_policy_client(), get_edge_client())


def get_evaluation_service(db: Session = None) -> HealthEvaluationService:
    if db is None:
        raise RuntimeError("DB session dependency missing")
    return HealthEvaluationService(
        db,
        get_policy_client(),
        slo_service=get_slo_service(db),
        event_bus=get_event_bus(),
    )


def get_rollup_service(db: Session = None) -> RollupService:
    if db is None:
        raise RuntimeError("DB session dependency missing")
    return RollupService(db)


def get_slo_service(db: Session = None) -> SLOService:
    if db is None:
        raise RuntimeError("DB session dependency missing")
    return SLOService(db, get_policy_client())


def get_safe_to_act_service(
    rollup: RollupService,
    telemetry: TelemetryIngestionService,
) -> SafeToActService:
    return SafeToActService(rollup, telemetry, get_deployment_client(), get_policy_client())

