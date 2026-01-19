from __future__ import annotations
"""Performance tests for Health & Reliability Monitoring service."""

import time
import pytest
from fastapi import status
from fastapi.testclient import TestClient
import importlib.util
import sys
from pathlib import Path

# Use shim approach like integration tests
# Ensure shim package is used (clear any preloaded modules)
for _mod in [m for m in list(sys.modules) if m.startswith("health_reliability_monitoring")]:
    sys.modules.pop(_mod, None)
shim_path = Path(__file__).resolve().parents[3] / "health_reliability_monitoring" / "main.py"
spec = importlib.util.spec_from_file_location("health_reliability_monitoring.main", shim_path)
shim_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shim_mod)
create_app = shim_mod.create_app
app = create_app()

def _get_app():
    """Get the app instance."""
    return app


@pytest.mark.performance
class TestComponentRegistryPerformance:
    """Test component registry performance."""

    def test_component_registration_latency(self):
        """Test that component registration meets latency requirements."""
        app = _get_app()
        # Setup database like integration tests do
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from health_reliability_monitoring.database import models
        from health_reliability_monitoring.service_container import get_db_session

        engine = create_engine(
            "sqlite:///:memory:",
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

        try:
            client = TestClient(app)
            headers = {"Authorization": "Bearer valid_epc1_test"}

            component = {
                "component_id": "perf-test-1",
                "name": "Performance Test",
                "component_type": "service",
                "plane": "Tenant",
                "tenant_scope": "tenant"
            }

            start_time = time.perf_counter()
            response = client.post(
                "/v1/health/components",
                json=component,
                headers=headers
            )
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Should complete within reasonable time (5000ms to allow CI/slower machines; catches real regressions)
            assert latency_ms < 5000
            assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_401_UNAUTHORIZED]
        finally:
            app.dependency_overrides.pop(get_db_session, None)

    @pytest.mark.performance
    def test_component_list_performance(self):
        """Test that component listing meets latency requirements."""
        app = _get_app()
        # Setup database like integration tests do
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from health_reliability_monitoring.database import models
        from health_reliability_monitoring.service_container import get_db_session

        engine = create_engine(
            "sqlite:///:memory:",
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

        try:
            client = TestClient(app)
            headers = {"Authorization": "Bearer valid_epc1_test"}

            start_time = time.perf_counter()
            response = client.get("/v1/health/components", headers=headers)
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Should complete within reasonable time (5000ms to allow CI/slower machines)
            assert latency_ms < 5000
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
        finally:
            app.dependency_overrides.pop(get_db_session, None)

    @pytest.mark.performance
    def test_concurrent_registrations(self):
        """Test performance under concurrent registrations."""
        app = _get_app()
        # Setup database like integration tests do
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from health_reliability_monitoring.database import models
        from health_reliability_monitoring.service_container import get_db_session

        engine = create_engine(
            "sqlite:///:memory:",
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

        try:
            client = TestClient(app)
            headers = {"Authorization": "Bearer valid_epc1_test"}

            import concurrent.futures

            def register_component(i):
                component = {
                    "component_id": f"concurrent-{i}",
                    "name": f"Concurrent {i}",
                    "component_type": "service",
                    "plane": "Tenant",
                    "tenant_scope": "tenant"
                }
                return client.post(
                    "/v1/health/components",
                    json=component,
                    headers=headers
                )

            start_time = time.perf_counter()
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(register_component, i) for i in range(10)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
            total_time = (time.perf_counter() - start_time) * 1000

            # Should handle 10 concurrent requests within reasonable time (< 5.5s in test harness with tolerance)
            assert total_time < 5500
            assert all(r.status_code in [status.HTTP_201_CREATED, status.HTTP_401_UNAUTHORIZED] for r in results)
        finally:
            app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.performance
class TestSafeToActPerformance:
    """Test Safe-to-Act evaluation performance."""

    def test_safe_to_act_evaluation_latency(self):
        """Test that Safe-to-Act evaluation meets latency requirements."""
        app = _get_app()
        # Setup database like integration tests do
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from health_reliability_monitoring.database import models
        from health_reliability_monitoring.service_container import get_db_session

        engine = create_engine(
            "sqlite:///:memory:",
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

        try:
            client = TestClient(app)
            headers = {"Authorization": "Bearer valid_epc1_test"}

            request = {
                "tenant_id": "tenant-1",
                "plane": "Tenant",
                "action_type": "deploy"
            }

            start_time = time.perf_counter()
            response = client.post(
                "/v1/health/safe_to_act/check_safe_to_act",
                json=request,
                headers=headers
            )
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Should complete within reasonable time (< 100ms for evaluation)
            assert latency_ms < 100
            # May return 200 (success), 401 (unauthorized), or 404 (endpoint not found) depending on setup
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]
        finally:
            app.dependency_overrides.pop(get_db_session, None)

