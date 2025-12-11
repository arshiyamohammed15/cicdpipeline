"""
Test fixtures for Health Reliability Monitoring with in-memory persistence.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

# Ensure module path present
MODULE_ROOT = Path(__file__).resolve().parents[3] / "src" / "cloud_services" / "shared-services" / "health-reliability-monitoring"
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

# Force in-memory DB for tests
os.environ.setdefault("HEALTH_RELIABILITY_MONITORING_DATABASE_URL", "sqlite:///:memory:")

from health_reliability_monitoring.database import models as db_models  # noqa: E402
from health_reliability_monitoring.database import session as db_session_module  # noqa: E402
import health_reliability_monitoring.service_container as sc  # noqa: E402
from health_reliability_monitoring.dependencies import (
    PolicyClient,
    EdgeAgentClient,
    DeploymentClient,
)  # noqa: E402

# Create shared in-memory engine/session and wire into modules
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = scoped_session(
    sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
)
db_models.Base.metadata.create_all(engine)

db_session_module.engine = engine
db_session_module.SessionLocal = TestingSessionLocal
sc.SessionLocal = TestingSessionLocal


@pytest.fixture
def db_session():
    """Provide a real SQLAlchemy session against isolated in-memory DB per test."""
    db_models.Base.metadata.drop_all(engine)
    db_models.Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        TestingSessionLocal.remove()


@pytest.fixture
def policy_client():
    """Provide a lightweight policy client stub."""
    return PolicyClient(base_url="http://localhost")


@pytest.fixture
def edge_client():
    """Provide edge agent client stub."""
    return EdgeAgentClient()


@pytest.fixture
def deployment_client():
    """Provide deployment client stub for safe-to-act notifications."""
    return DeploymentClient(topic="safe-to-act-test")
