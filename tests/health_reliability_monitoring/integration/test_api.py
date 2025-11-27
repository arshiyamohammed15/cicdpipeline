import asyncio
import time
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from health_reliability_monitoring.main import app
from health_reliability_monitoring.database import models
from health_reliability_monitoring.service_container import get_db_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(autouse=True)
def setup_db():
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    models.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)

    def get_test_session():
        session = Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = get_test_session
    yield engine
    app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.integration
def test_component_registry_and_status_flow():
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

