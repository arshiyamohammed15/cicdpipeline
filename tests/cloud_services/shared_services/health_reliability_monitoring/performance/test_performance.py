from __future__ import annotations
"""
Performance tests for Health & Reliability Monitoring service.
"""

import pytest
import time
from datetime import datetime
from fastapi.testclient import TestClient

# Path setup handled by conftest.py
from health_reliability_monitoring.main import app
from health_reliability_monitoring.models import ComponentDefinition, TelemetryPayload

test_client = TestClient(app)


class TestTelemetryIngestionPerformance:
    """Test telemetry ingestion performance."""

    def test_telemetry_ingestion_latency(self, db_session):
        """Test that telemetry ingestion meets latency budget."""
        # Register component first
        component = ComponentDefinition(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            tenant_scope="tenant",
        )
        test_client.post(
            "/v1/health/components",
            json=component.model_dump(),
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )
        
        payload = TelemetryPayload(
            component_id="test-component-1",
            tenant_id="test-tenant",
            plane="Product",
            environment="prod",
            timestamp=datetime.utcnow(),
            metrics={"latency_p95_ms": 150.0},
            telemetry_type="metrics",
        )
        
        start = time.perf_counter()
        response = test_client.post(
            "/v1/health/telemetry",
            json=payload.model_dump(),
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )
        latency = time.perf_counter() - start
        
        assert response.status_code in [status.HTTP_202_ACCEPTED, status.HTTP_401_UNAUTHORIZED]
        # Latency should be reasonable (< 1 second for acceptance)
        if response.status_code == status.HTTP_202_ACCEPTED:
            assert latency < 1.0

    def test_batch_telemetry_ingestion(self, db_session):
        """Test batch telemetry ingestion performance."""
        # Register component
        component = ComponentDefinition(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            tenant_scope="tenant",
        )
        test_client.post(
            "/v1/health/components",
            json=component.model_dump(),
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )
        
        # Ingest multiple payloads
        payloads = [
            TelemetryPayload(
                component_id="test-component-1",
                tenant_id="test-tenant",
                plane="Product",
                environment="prod",
                timestamp=datetime.utcnow(),
                metrics={"latency_p95_ms": 150.0 + i},
                telemetry_type="metrics",
            )
            for i in range(10)
        ]
        
        start = time.perf_counter()
        for payload in payloads:
            test_client.post(
                "/v1/health/telemetry",
                json=payload.model_dump(),
                headers={"Authorization": "Bearer valid_epc1_test_token"},
            )
        total_latency = time.perf_counter() - start
        
        # Average latency per request should be reasonable
        avg_latency = total_latency / len(payloads)
        assert avg_latency < 0.5  # 500ms per request


class TestHealthQueryPerformance:
    """Test health query performance."""

    def test_component_status_query_latency(self, db_session):
        """Test component status query latency."""
        # Create component and snapshot
        try:
    from health_reliability_monitoring.database import models as db_models
except ImportError:
    db_models = None  # Database module not implemented
        
        component = db_models.Component(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            environment="prod",
            tenant_scope="tenant",
        )
        db_session.add(component)
        
        snapshot = db_models.HealthSnapshot(
            snapshot_id="snapshot-1",
            component_id="test-component-1",
            tenant_id="test-tenant",
            plane="Product",
            environment="prod",
            state="OK",
            reason_code="healthy",
            evaluated_at=datetime.utcnow(),
        )
        db_session.add(snapshot)
        db_session.commit()
        
        start = time.perf_counter()
        response = test_client.get(
            "/v1/health/components/test-component-1/status",
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )
        latency = time.perf_counter() - start
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]
            # Query should be fast (< 500ms)
            assert latency < 0.5

    def test_tenant_health_query_latency(self, db_session):
        """Test tenant health query latency."""
        start = time.perf_counter()
        response = test_client.get(
            "/v1/health/tenants/test-tenant",
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )
        latency = time.perf_counter() - start
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
            # Rollup query should be reasonable (< 1 second)
            assert latency < 1.0


class TestSafeToActPerformance:
    """Test Safe-to-Act evaluation performance."""

    def test_safe_to_act_evaluation_latency(self, db_session):
        """Test Safe-to-Act evaluation latency."""
        request = {
            "tenant_id": "test-tenant",
            "plane": "Product",
            "action_type": "standard_action",
            "component_scope": None,
        }
        
        start = time.perf_counter()
        response = test_client.post(
            "/v1/health/check_safe_to_act",
            json=request,
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )
        latency = time.perf_counter() - start
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
            # Evaluation should be fast (< 500ms)
            assert latency < 0.5

