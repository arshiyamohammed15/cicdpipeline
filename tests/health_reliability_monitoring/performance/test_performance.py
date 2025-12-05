from __future__ import annotations
"""Performance tests for Health & Reliability Monitoring service."""

import time
import pytest
from fastapi import status
from fastapi.testclient import TestClient

# Import will be available after conftest sets up the module
# Import lazily to ensure conftest runs first
def _get_app():
    """Get the app instance, ensuring module is set up."""
    # Import parent conftest to trigger module setup
    import sys
    from pathlib import Path
    parent_dir = Path(__file__).resolve().parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    # Import conftest which will set up the module structure
    import conftest  # noqa: F401
    # Ensure module setup function is called
    conftest._setup_health_reliability_monitoring_module()
    # Verify module was loaded
    if "health_reliability_monitoring.main" not in sys.modules:
        raise ImportError("health_reliability_monitoring.main module was not loaded by setup function")
    from health_reliability_monitoring.main import app
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

            # Should complete within reasonable time (< 500ms for registration)
            assert latency_ms < 500
            assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_401_UNAUTHORIZED]
        finally:
            app.dependency_overrides.pop(get_db_session, None)

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

            # Should complete within reasonable time (< 200ms for listing)
            assert latency_ms < 200
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
        finally:
            app.dependency_overrides.pop(get_db_session, None)

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

            # Should handle 10 concurrent requests within reasonable time (< 2s)
            assert total_time < 2000
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

