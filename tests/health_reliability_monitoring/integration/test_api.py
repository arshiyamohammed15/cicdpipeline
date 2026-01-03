import asyncio
import time
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
import importlib.util
import sys
from pathlib import Path

# Ensure shim package is used (clear any preloaded modules)
for _mod in [m for m in list(sys.modules) if m.startswith("health_reliability_monitoring")]:
    sys.modules.pop(_mod, None)
shim_path = Path(__file__).resolve().parents[3] / "health_reliability_monitoring" / "main.py"
spec = importlib.util.spec_from_file_location("health_reliability_monitoring.main", shim_path)
shim_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shim_mod)
create_app = shim_mod.create_app
app = create_app()


@pytest.mark.integration
def test_component_registry_and_status_flow(hrm_test_db):
    """Test component registry and status flow with database setup."""
    # hrm_test_db fixture ensures database tables are created
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

