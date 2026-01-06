import asyncio
import time
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
import importlib.util
import sys
import importlib
from pathlib import Path


@pytest.mark.integration
def test_component_registry_and_status_flow(hrm_test_db):
    """Test component registry and status flow with database setup."""
    # hrm_test_db fixture ensures database tables are created
    # Get app instance - it should use the test database session set up by the fixture
    shim_path = Path(__file__).resolve().parents[3] / "health_reliability_monitoring" / "main.py"
    spec = importlib.util.spec_from_file_location("health_reliability_monitoring.main", shim_path)
    shim_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shim_mod)
    create_app = shim_mod.create_app
    app = create_app()
    
    # Ensure the app uses the test database session by overriding the dependency
    # The fixture sets db_session.SessionLocal and sc.SessionLocal, but we also need to
    # override the FastAPI dependency to ensure it uses the test session
    import health_reliability_monitoring.service_container as sc
    from health_reliability_monitoring.database import models
    
    # Get the test session factory and engine from the fixture setup
    import health_reliability_monitoring.database.session as db_session
    test_session_factory = db_session.SessionLocal
    test_engine = db_session.engine
    
    # Verify the session factory is bound to the test engine
    # Create a test session and verify it uses the test engine
    test_session = test_session_factory()
    try:
        # Verify the session's bind is the test engine
        assert test_session.bind is test_engine or test_session.bind.url == test_engine.url, \
            f"Session bound to wrong engine: {test_session.bind.url} != {test_engine.url}"
    finally:
        test_session.close()
    
    # Ensure tables are created on the test engine
    models.Base.metadata.create_all(test_engine)
    
    def get_test_db_session():
        """FastAPI dependency that returns a test database session."""
        session = test_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    # Override the FastAPI dependency
    app.dependency_overrides[sc.get_db_session] = get_test_db_session
    
    try:
        client = TestClient(app)
        headers = {"Authorization": "Bearer valid_epc1_test"}
        component = {
            "component_id": "pm-4",
            "name": "Detection",
            "component_type": "service",
            "plane": "Tenant",
            "environment": "prod",
            "tenant_scope": "tenant",
            "dependencies": [],
            "metrics_profile": [],
            "health_policies": [],
        }
        assert client.post("/v1/health/components", json=component, headers=headers).status_code == 201

        telemetry = {
            "component_id": "pm-4",
            "tenant_id": "tenant-default",
            "plane": "Tenant",
            "environment": "prod",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {"latency_p95_ms": 100},
            "labels": {},
            "telemetry_type": "metrics",
        }
        assert (
            client.post("/v1/health/telemetry", params={"sync": "true"}, json=telemetry, headers=headers).status_code
            == 202
        )

        status = None
        for _ in range(10):
            status = client.get("/v1/health/components/pm-4/status", headers=headers)
            if status.status_code == 200:
                break
            time.sleep(0.2)
        assert status is not None and status.status_code == 200
        assert status.json()["component_id"] == "pm-4"
    finally:
        # Clean up dependency override
        app.dependency_overrides.pop(sc.get_db_session, None)

