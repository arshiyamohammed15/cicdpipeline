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

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src"
MODULE_ROOT = SRC_ROOT / "cloud_services" / "shared-services" / "health-reliability-monitoring"

# Ensure import paths are present
for path_entry in (REPO_ROOT, SRC_ROOT):
    if str(path_entry) not in sys.path:
        sys.path.insert(0, str(path_entry))

import importlib
importlib.invalidate_caches()
# Preload and refresh the canonical package after path adjustments to avoid
# stale module state when workers reuse processes across suites.
import health_reliability_monitoring  # type: ignore  # noqa: E402
import health_reliability_monitoring.models as hrm_models  # type: ignore  # noqa: E402
import health_reliability_monitoring.services.safe_to_act_service as hrm_safe  # type: ignore  # noqa: E402
importlib.reload(hrm_models)
importlib.reload(hrm_safe)

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


@pytest.fixture(autouse=True)
def _log_safe_to_act_class_identity():
    """Record class identity to help diagnose cross-test module drift."""
    from pathlib import Path
    from health_reliability_monitoring.models import SafeToActResponse as TestResp
    import sys

    debug_path = Path("artifacts") / "safe_to_act_debug.log"
    debug_path.parent.mkdir(exist_ok=True, parents=True)
    test_module_cls = None
    candidates = [k for k in sys.modules.keys() if "test_safe_to_act_service" in k]
    test_mod = None
    for name in candidates:
        mod = sys.modules.get(name)
        if mod and hasattr(mod, "SafeToActResponse"):
            test_mod = mod
            test_module_cls = getattr(mod, "SafeToActResponse")
            if test_module_cls is not TestResp:
                setattr(mod, "SafeToActResponse", TestResp)
            break
    with open(debug_path, "a", encoding="utf-8") as fh:
        fh.write(
            f"module_class_id={id(TestResp)} module={TestResp.__module__} "
            f"test_module_class_id={id(test_module_cls) if test_module_cls else 'n/a'} "
            f"test_mod_name={getattr(test_mod, '__name__', 'n/a')} candidates={candidates}\n"
        )
