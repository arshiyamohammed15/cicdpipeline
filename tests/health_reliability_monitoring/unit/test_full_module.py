import asyncio
import importlib
import sys
import types
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from health_reliability_monitoring import config
from health_reliability_monitoring.database import models
from health_reliability_monitoring.dependencies import (
    AlertingClient,
    DeploymentClient,
    ERISClient,
    EdgeAgentClient,
    IAMClient,
    PolicyClient,
)
from health_reliability_monitoring.models import (
    ComponentDefinition,
    DependencyReference,
    SafeToActRequest,
    TelemetryPayload,
)
from health_reliability_monitoring.security import (
    ensure_cross_plane_access,
    ensure_scope,
    ensure_tenant_access,
    require_scope,
)
from health_reliability_monitoring.routes import health as health_routes
from health_reliability_monitoring.routes import registry as registry_routes
from health_reliability_monitoring.routes import safe_to_act as safe_routes
from health_reliability_monitoring.services.audit_service import AuditService
from health_reliability_monitoring.services.evaluation_service import HealthEvaluationService
from health_reliability_monitoring.services.event_bus_service import EventBusService
from health_reliability_monitoring.services.rollup_service import RollupService
from health_reliability_monitoring.services.safe_to_act_service import SafeToActService
from health_reliability_monitoring.services.slo_service import SLOService
from health_reliability_monitoring.services.telemetry_ingestion_service import TelemetryIngestionService
from health_reliability_monitoring.services.telemetry_worker import TelemetryWorker
from health_reliability_monitoring.telemetry.otel_pipeline import TelemetryGuards


@pytest.fixture
def memory_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    models.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    with Session() as session:
        yield session
    engine.dispose()


@pytest.mark.unit
def test_env_list_handles_empty_and_lists(monkeypatch):
    monkeypatch.delenv("HRM_LIST", raising=False)
    assert config._env_list("HRM_LIST") == []
    monkeypatch.setenv("HRM_LIST", "alpha, beta ,, gamma")
    assert config._env_list("HRM_LIST") == ["alpha", "beta", "gamma"]


@pytest.mark.unit
def test_session_scope_commit_and_rollback(tmp_path, monkeypatch):
    from health_reliability_monitoring.database import session as session_module

    db_path = tmp_path / "hrm.db"
    if db_path.exists():
        db_path.unlink()
    monkeypatch.setenv(
        "HEALTH_RELIABILITY_MONITORING_DATABASE_URL",
        f"sqlite:///{db_path}",
    )
    reloaded = importlib.reload(session_module)

    with reloaded.session_scope() as sess:
        sess.execute(text("CREATE TABLE IF NOT EXISTS counter (id INTEGER PRIMARY KEY, value TEXT)"))
        sess.execute(text("DELETE FROM counter"))

    with reloaded.session_scope() as sess:
        sess.execute(text("INSERT INTO counter(value) VALUES ('first')"))

    with pytest.raises(RuntimeError):
        with reloaded.session_scope() as sess:
            sess.execute(text("INSERT INTO counter(value) VALUES ('boom')"))
            raise RuntimeError("fail")

    with reloaded.session_scope() as sess:
        rows = sess.execute(text("SELECT value FROM counter")).scalars().all()
    assert rows == ["first"]


@pytest.mark.unit
def test_session_handles_non_sqlite(monkeypatch):
    from health_reliability_monitoring.database import session as session_module

    monkeypatch.setenv(
        "HEALTH_RELIABILITY_MONITORING_DATABASE_URL",
        "postgresql://user:pass@localhost/db",
    )
    reloaded = importlib.reload(session_module)
    assert "pool_size" in reloaded.engine_kwargs


@pytest.mark.asyncio
async def test_dependencies_cover_all_clients(monkeypatch):
    iam = IAMClient()
    claims = await iam.verify("valid_epc1_token")
    assert claims and iam.authorize(claims, "health_reliability_monitoring.read")
    assert await iam.verify("invalid") is None

    policy = PolicyClient("http://localhost")
    policy_one = await policy.fetch_health_policy("policy-a")
    policy_two = await policy.fetch_health_policy("policy-a")
    assert policy_one is policy_two
    slo = await policy.fetch_slo("slo-a")
    assert slo == await policy.fetch_slo("slo-a")
    safe = await policy.fetch_safe_to_act_policy("deploy")
    assert safe["deny_states"] == ["FAILED"]
    assert safe is await policy.fetch_safe_to_act_policy("deploy")
    await policy.close()

    alerting = AlertingClient("alerts")
    event_id = await alerting.publish({"data": "ok"})
    assert alerting.sent_events[-1]["event_id"] == event_id

    deployment = DeploymentClient("deploy")
    await deployment.notify({"allowed": True})
    assert deployment.safe_to_act_events[-1]["allowed"] is True

    eris = ERISClient("receipts")
    receipt_id = await eris.emit_receipt({"action": "test"})
    assert eris.receipts[receipt_id]["action"] == "test"

    agent = EdgeAgentClient()
    await agent.upsert_profile({"component_id": "pm-4"})


@pytest.mark.asyncio
async def test_security_helpers(monkeypatch):
    iam = IAMClient()
    claims = await require_scope(
        authorization="Bearer valid_epc1_token",
        iam=iam,
    )
    with pytest.raises(HTTPException):
        await require_scope(authorization="Bearer nope", iam=iam)

    ensure_tenant_access(claims, "tenant-default")
    with pytest.raises(HTTPException):
        ensure_tenant_access({"scope": []}, "tenant-x")

    ensure_scope(claims, "health_reliability_monitoring.read")
    with pytest.raises(HTTPException):
        ensure_scope({"scope": []}, "health_reliability_monitoring.read")

    ensure_cross_plane_access({"scope": ["health_reliability_monitoring.cross_tenant"]})
    with pytest.raises(HTTPException):
        ensure_cross_plane_access({"scope": []})


@pytest.mark.unit
def test_main_healthz_and_metrics(monkeypatch):
    import health_reliability_monitoring.main as main

    events = []

    class DummyWorker:
        async def start(self):
            events.append("start")

        async def stop(self):
            events.append("stop")

    monkeypatch.setattr(main, "get_telemetry_worker", lambda: DummyWorker())
    with TestClient(main.app) as client:
        resp = client.get("/healthz")
        assert resp.status_code == 200
        metrics = client.get("/metrics")
        assert metrics.status_code == 200
    assert events == ["start", "stop"]


@pytest.mark.unit
def test_service_container_db_session(monkeypatch, memory_session):
    import health_reliability_monitoring.service_container as container

    monkeypatch.setattr(container, "SessionLocal", lambda: memory_session)
    gen = container.get_db_session()
    session = next(gen)
    session.execute(text("SELECT 1"))
    with pytest.raises(RuntimeError):
        gen.throw(RuntimeError("stop"))

    gen = container.get_db_session()
    session = next(gen)
    session.execute(text("SELECT 1"))
    gen.close()

    assert container.get_alerting_client() is container.get_alerting_client()
    assert container.get_deployment_client() is container.get_deployment_client()
    assert container.get_telemetry_service() is container.get_telemetry_service()

    with pytest.raises(RuntimeError):
        container.get_registry_service()


@pytest.mark.unit
def test_service_container_factories(memory_session):
    import health_reliability_monitoring.service_container as container

    rollup = container.get_rollup_service(memory_session)
    slo = container.get_slo_service(memory_session)
    telemetry = container.get_telemetry_service()
    evaluator = container.get_evaluation_service(memory_session)
    safe = container.get_safe_to_act_service(rollup, telemetry)

    assert isinstance(rollup, RollupService)
    assert isinstance(slo, SLOService)
    assert isinstance(evaluator, HealthEvaluationService)
    assert isinstance(safe, SafeToActService)


@pytest.mark.asyncio
async def test_audit_and_event_bus(monkeypatch):
    alerting = AlertingClient("alerts")
    eris = ERISClient("receipts")
    bus = EventBusService(alerting, eris)
    await bus.emit_health_transition({"component_id": "pm-4"})
    receipt = await bus.emit_receipt({"component_id": "pm-4"}, action="meta")
    assert receipt in eris.receipts

    audit = AuditService(bus)
    await audit.record_access({"actor": "tester"}, "tenant:1", "read")
    assert eris.receipts


@pytest.mark.asyncio
async def test_evaluation_service_full_flow(memory_session):
    component = models.Component(
        component_id="pm-4",
        name="Detection",
        component_type="service",
        plane="Tenant",
        environment="prod",
        tenant_scope="tenant",
        metrics_profile=["GOLDEN_SIGNALS"],
        health_policies=["policy-1", "policy-empty"],
        slo_target=99.0,
    )
    memory_session.add(component)
    memory_session.commit()

        class StubPolicy:
            async def fetch_health_policy(self, policy_id: str):
                if policy_id == "policy-empty":
                    return {"thresholds": {}}
                return {
                    "thresholds": {
                        "latency_p95_ms": 200,
                        "error_rate": 0.02,
                        "saturation_pct": 80,
                        "heartbeat_lag_sec": 120,
                    },
                    "hysteresis": {"exit": 2},
                    "window_seconds": 60,
                }

    class StubSLO:
        def __init__(self):
            self.samples = []

        async def update_slo(self, **data):
            self.samples.append(data)

    class StubBus:
        def __init__(self):
            self.events = []

        async def emit_health_transition(self, snapshot):
            self.events.append(snapshot)

    evaluator = HealthEvaluationService(
        memory_session,
        StubPolicy(),
        slo_service=StubSLO(),
        event_bus=StubBus(),
    )
    now = datetime.utcnow()
        payloads = [
        TelemetryPayload(
            component_id="pm-4",
            tenant_id="tenant-default",
            plane="Tenant",
            environment="prod",
            timestamp=now,
            metrics={},
            labels={},
            telemetry_type="metrics",
        ),
        TelemetryPayload(
            component_id="pm-4",
            tenant_id="tenant-default",
            plane="Tenant",
            environment="prod",
            timestamp=now,
                metrics={"sample_window_sec": 10},
            labels={},
            telemetry_type="metrics",
        ),
        TelemetryPayload(
            component_id="pm-4",
            tenant_id="tenant-default",
            plane="Tenant",
            environment="prod",
            timestamp=now,
                metrics={"latency_p95_ms": 250, "saturation_pct": 90, "heartbeat_lag_sec": 200},
                labels={},
                telemetry_type="metrics",
            ),
            TelemetryPayload(
                component_id="pm-4",
                tenant_id="tenant-default",
                plane="Tenant",
                environment="prod",
                timestamp=now,
                metrics={"error_rate": 0.5},
            labels={},
            telemetry_type="metrics",
        ),
            TelemetryPayload(
                component_id="ghost",
                tenant_id="tenant-default",
                plane="Tenant",
                environment="prod",
                timestamp=now,
                metrics={"latency_p95_ms": 10},
                labels={},
                telemetry_type="metrics",
            ),
    ]
    evaluator._state_cache["pm-4"] = ("DEGRADED", datetime.utcnow() - timedelta(minutes=5))
    snapshots = await evaluator.evaluate_batch(payloads)
    assert snapshots[-1].state == "FAILED"
    assert any(evt["state"] == "FAILED" for evt in evaluator._event_bus.events)


@pytest.mark.asyncio
async def test_health_routes_cover_views(monkeypatch, memory_session):
    claims = {"scope": ["health_reliability_monitoring.read"], "tenant_id": "tenant-default"}
    component = models.Component(
        component_id="pm-4",
        name="Detection",
        component_type="service",
        plane="Tenant",
        environment="prod",
        tenant_scope="tenant",
    )
    memory_session.add(component)
    snapshot = models.HealthSnapshot(
        snapshot_id="routesnap",
        component_id="pm-4",
        tenant_id="tenant-default",
        plane="Tenant",
        environment="prod",
        state="OK",
        reason_code="healthy",
        evaluated_at=datetime.utcnow(),
    )
    memory_session.add(snapshot)
    memory_session.commit()

    assert isinstance(health_routes._rollup_service(memory_session), RollupService)
    assert isinstance(health_routes._slo_service(memory_session), SLOService)
    assert isinstance(health_routes._audit_service(), AuditService)

    class StubEvaluator:
        def __init__(self):
            self.called = False

        async def evaluate_batch(self, batch):
            self.called = True

    stub = StubEvaluator()
    monkeypatch.setattr(health_routes, "get_evaluation_service", lambda session: stub)
    telemetry_service = TelemetryIngestionService()
    payload = TelemetryPayload(
        component_id="pm-4",
        tenant_id="tenant-default",
        plane="Tenant",
        environment="prod",
        timestamp=datetime.utcnow(),
        metrics={"latency_p95_ms": 10},
        labels={},
        telemetry_type="metrics",
    )
    await health_routes.ingest_telemetry(payload, telemetry_service, memory_session, True, claims)
    assert stub.called

    result = health_routes.get_component_status("pm-4", session=memory_session, claims=claims)
    assert result.state == "OK"
    with pytest.raises(HTTPException):
        health_routes.get_component_status("ghost", session=memory_session, claims=claims)

    audit = AuditService(EventBusService(AlertingClient("alerts"), ERISClient("receipts")))
    rollup = RollupService(memory_session)
    tenant_view = await health_routes.get_tenant_health("tenant-default", rollup, audit, claims)
    assert tenant_view.tenant_id == "tenant-default"
    plane_view = await health_routes.get_plane_health(
        "Tenant",
        "prod",
        rollup,
        audit,
        {"scope": ["health_reliability_monitoring.cross_tenant"]},
    )
    assert plane_view.plane == "Tenant"

    class StubPolicy:
        async def fetch_slo(self, slo_id: str):
            return {"target_percentage": 50.0, "window_days": 7, "error_budget_minutes": 100}

    slo_service = SLOService(memory_session, StubPolicy())
    await slo_service.update_slo("pm-4", "pm-4-default", success_minutes=0, total_minutes=60)
    health_routes.get_component_slo("pm-4", service=slo_service, claims=claims)
    with pytest.raises(HTTPException):
        health_routes.get_component_slo("ghost", service=slo_service, claims=claims)


@pytest.mark.unit
def test_rollup_service_with_dependencies(memory_session):
    component_a = models.Component(
        component_id="A",
        name="A",
        component_type="service",
        plane="Tenant",
        environment="prod",
        tenant_scope="tenant",
    )
    component_b = models.Component(
        component_id="B",
        name="B",
        component_type="service",
        plane="Tenant",
        environment="prod",
        tenant_scope="tenant",
    )
    component_c = models.Component(
        component_id="C",
        name="C",
        component_type="service",
        plane="Tenant",
        environment="prod",
        tenant_scope="tenant",
    )
    memory_session.add_all([component_a, component_b, component_c])
    memory_session.flush()
    dep = models.ComponentDependency(
        component_id="A",
        dependency_id="B",
        critical=True,
    )
    dep_missing = models.ComponentDependency(
        component_id="C",
        dependency_id="D",
        critical=True,
    )
    memory_session.add_all([dep, dep_missing])
    snapshot_ok = models.HealthSnapshot(
        snapshot_id="snap-ok",
        component_id="B",
        plane="Tenant",
        environment="prod",
        state="FAILED",
        reason_code="error",
        evaluated_at=datetime.utcnow(),
    )
    snapshot_a = models.HealthSnapshot(
        snapshot_id="snap-a",
        component_id="A",
        plane="Tenant",
        environment="prod",
        state="OK",
        reason_code="init",
        evaluated_at=datetime.utcnow(),
    )
    memory_session.add_all([snapshot_ok, snapshot_a])
    memory_session.commit()

    service = RollupService(memory_session)
    latest = service.latest_component_states()
    assert latest["A"].state == "FAILED"
    assert latest["C"].state == "UNKNOWN"
    tenant_view = service.tenant_view("tenant-default")
    assert tenant_view.counts["FAILED"] >= 1
    plane_view = service.plane_view("Tenant", "prod")
    assert plane_view.state == "FAILED"


@pytest.mark.unit
def test_registry_routes_cover_paths(memory_session):
    class StubPolicy:
        async def fetch_health_policy(self, policy_id: str):
            return {}

    service = ComponentRegistryService(memory_session, StubPolicy(), EdgeAgentClient())
    component = ComponentDefinition(
        component_id="pm-4",
        name="Detection",
        component_type="service",
        plane="Tenant",
        environment="prod",
        tenant_scope="tenant",
        dependencies=[DependencyReference(component_id="B", critical=True)],
        metrics_profile=["GOLDEN_SIGNALS"],
        health_policies=["policy-1"],
    )
    write_claims = {"scope": ["health_reliability_monitoring.write"]}
    read_claims = {"scope": ["health_reliability_monitoring.read"]}
    registry_routes.register_component(component, service=service, claims=write_claims)
    component.name = "Detection Updated"
    registry_routes.register_component(component, service=service, claims=write_claims)
    fetched = registry_routes.get_component("pm-4", service=service, claims=read_claims)
    assert fetched.name.endswith("Updated")
    listing = registry_routes.list_components(service=service, claims=read_claims)
    assert listing
    with pytest.raises(HTTPException):
        registry_routes.get_component("ghost", service=service, claims=read_claims)


@pytest.mark.asyncio
async def test_safe_to_act_service_component_scope(memory_session):
    component = models.Component(
        component_id="pm-4",
        name="Detection",
        component_type="service",
        plane="Tenant",
        environment="prod",
        tenant_scope="tenant",
    )
    memory_session.add(component)
    snapshot = models.HealthSnapshot(
        snapshot_id="snap",
        component_id="pm-4",
        tenant_id="tenant-default",
        plane="Tenant",
        environment="prod",
        state="OK",
        reason_code="test",
        evaluated_at=datetime.utcnow(),
    )
    memory_session.add(snapshot)
    memory_session.commit()

    rollup = RollupService(memory_session)

    class FreshTelemetry(TelemetryIngestionService):
        def last_ingest_age(self) -> float:
            return 0.0

    telemetry = FreshTelemetry()
    deployment = DeploymentClient("topic")
    policy_client = PolicyClient("http://localhost")
    service = SafeToActService(rollup, telemetry, deployment, policy_client)
    request = SafeToActRequest(
        tenant_id="tenant-default",
        plane="Tenant",
        action_type="rollout",
        component_scope=["missing-component"],
    )
    response = await service.evaluate(request)
    await policy_client.close()
    assert response.allowed is False
    assert "missing-component" in response.reason_codes[0]


@pytest.mark.asyncio
async def test_safe_route_execution(memory_session):
    component = models.Component(
        component_id="pm-4",
        name="Detection",
        component_type="service",
        plane="Tenant",
        environment="prod",
        tenant_scope="tenant",
    )
    snapshot = models.HealthSnapshot(
        snapshot_id="route-safe",
        component_id="pm-4",
        tenant_id="tenant-default",
        plane="Tenant",
        environment="prod",
        state="OK",
        reason_code="healthy",
        evaluated_at=datetime.utcnow(),
    )
    memory_session.add_all([component, snapshot])
    memory_session.commit()

    request = SafeToActRequest(
        tenant_id="tenant-default",
        plane="Tenant",
        action_type="rollout",
        component_scope=None,
    )
    base_rollup = RollupService(memory_session)
    telemetry = TelemetryIngestionService()
    assert isinstance(safe_routes._rollup(memory_session), RollupService)
    assert isinstance(safe_routes._telemetry(), TelemetryIngestionService)
    safe_service = safe_routes._safe_service(base_rollup, telemetry)
    assert isinstance(safe_service, SafeToActService)

    service = SafeToActService(
        RollupService(memory_session),
        telemetry,
        DeploymentClient("topic"),
        PolicyClient("http://localhost"),
    )
    claims = {"scope": ["health_reliability_monitoring.read"], "tenant_id": "tenant-default"}
    response = await safe_routes.check_safe_to_act(request, service=service, claims=claims)
    await service._policy_client.close()
    assert isinstance(response.allowed, bool)


@pytest.mark.asyncio
async def test_safe_to_act_service_stale_telemetry():
    class StubRollup:
        def tenant_view(self, tenant_id: str):
            return types.SimpleNamespace(tenant_id=tenant_id, plane_states={"Tenant": "OK"})

        def latest_component_states(self):
            return {}

    class StaleTelemetry(TelemetryIngestionService):
        def last_ingest_age(self) -> float:
            return 9999.0

    deployment = DeploymentClient("topic")
    policy_client = PolicyClient("http://localhost")
    service = SafeToActService(StubRollup(), StaleTelemetry(), deployment, policy_client)
    request = SafeToActRequest(
        tenant_id="tenant-default",
        plane="Tenant",
        action_type="rollout",
        component_scope=None,
    )
    response = await service.evaluate(request)
    await policy_client.close()
    assert response.allowed is False
    assert "health_system_unavailable" in response.reason_codes


@pytest.mark.unit
def test_slo_service_updates(memory_session):
    class StubPolicy:
        async def fetch_slo(self, slo_id: str):
            return {"target_percentage": 99.0, "window_days": 7, "error_budget_minutes": 10}

    service = SLOService(memory_session, StubPolicy())
    result = asyncio.run(
        service.update_slo(
            component_id="pm-4",
            slo_id="pm-4-default",
            success_minutes=60,
            total_minutes=60,
        )
    )
    assert result.state == "within_budget"
    latest = service.latest_slo("pm-4")
    assert latest is not None


@pytest.mark.unit
def test_slo_service_state_transitions(memory_session):
    class StubPolicy:
        async def fetch_slo(self, slo_id: str):
            return {"target_percentage": 99.0, "window_days": 7, "error_budget_minutes": 10}

    service = SLOService(memory_session, StubPolicy())
    result = asyncio.run(
        service.update_slo(
            component_id="pm-5",
            slo_id="pm-5-default",
            success_minutes=50,
            total_minutes=60,
        )
    )
    assert result.state == "approaching"
    result = asyncio.run(
        service.update_slo(
            component_id="pm-5",
            slo_id="pm-5-default",
            success_minutes=0,
            total_minutes=60,
        )
    )
    assert result.state == "breached"


@pytest.mark.unit
def test_telemetry_ingestion_age_defaults():
    service = TelemetryIngestionService()
    assert service.last_ingest_age() == float("inf")


@pytest.mark.unit
def test_telemetry_guards_validation_errors():
    guards = TelemetryGuards(max_labels=1)
    with pytest.raises(ValueError):
        guards.validate_labels({"a": "1", "b": "2"})
    with pytest.raises(ValueError):
        guards.validate_metrics({str(i): float(i) for i in range(70)})


@pytest.mark.asyncio
async def test_telemetry_ingestion_service_warns(monkeypatch):
    guards = TelemetryGuards(max_labels=5)
    service = TelemetryIngestionService(guards=guards)
    payload = TelemetryPayload(
        component_id="pm-4",
        tenant_id="tenant-default",
        plane="Tenant",
        environment="prod",
        timestamp=datetime.utcnow(),
        metrics={"latency_p95_ms": 10},
        labels={},
        telemetry_type="metrics",
    )
    for _ in range(config.load_settings().telemetry.ingestion_batch_size * 2 + 1):
        await service.ingest(payload)
    drained = await service.drain()
    assert drained
    assert service.last_ingest_age() >= 0.0
    assert service.last_ingest_age() != float("inf")


@pytest.mark.asyncio
async def test_telemetry_worker_processes_batch(monkeypatch):
    class DummySession:
        def __init__(self):
            self.flushed = False

        def close(self):
            pass

        def commit(self):
            self.flushed = True

        def rollback(self):
            self.flushed = False

    class DummySessionFactory:
        def __call__(self):
            return DummySession()

    class DummySLO:
        pass

    class DummyEvaluator:
        def __init__(self, session, policy_client, slo_service=None, event_bus=None):
            self.session = session
            self.batches = []

        async def evaluate_batch(self, batch):
            self.batches.append(batch)

    class DummyPolicy:
        pass

    class DummyEventBus:
        pass

    worker_module = importlib.import_module("health_reliability_monitoring.services.telemetry_worker")
    monkeypatch.setattr(worker_module, "SessionLocal", DummySessionFactory())
    monkeypatch.setattr(worker_module, "SLOService", lambda *args, **kwargs: DummySLO())
    monkeypatch.setattr(worker_module, "HealthEvaluationService", lambda *args, **kwargs: DummyEvaluator(*args, **kwargs))

    telemetry_service = TelemetryIngestionService()
    worker = TelemetryWorker(telemetry_service, DummyPolicy(), DummyEventBus())
    payload = TelemetryPayload(
        component_id="pm-4",
        tenant_id="tenant-default",
        plane="Tenant",
        environment="prod",
        timestamp=datetime.utcnow(),
        metrics={"latency_p95_ms": 10},
        labels={},
        telemetry_type="metrics",
    )
    await telemetry_service.ingest(payload)
    await worker.start()
    await asyncio.sleep(0.05)
    await worker.stop()
    idle_worker = TelemetryWorker(TelemetryIngestionService(), DummyPolicy(), DummyEventBus())
    await idle_worker.start()
    await asyncio.sleep(0.02)
    await idle_worker.stop()


@pytest.mark.unit
def test_otel_pipeline_handles_imports(monkeypatch):
    module_name = "health_reliability_monitoring.telemetry.otel_pipeline"
    original = sys.modules.pop(module_name, None)

    base = types.ModuleType("opentelemetry")
    metrics_mod = types.ModuleType("metrics")
    captured = {}

    def set_meter_provider(provider):
        captured["provider"] = provider

    metrics_mod.set_meter_provider = set_meter_provider
    exporter_module = types.ModuleType("opentelemetry.exporter.otlp.proto.grpc.metric_exporter")
    exporter_module.OTLPMetricExporter = lambda endpoint: endpoint
    reader_module = types.ModuleType("opentelemetry.sdk.metrics.export")
    class FakeReader:
        def __init__(self, exporter):
            self.exporter = exporter
    reader_module.PeriodicExportingMetricReader = FakeReader
    sdk_metrics_module = types.ModuleType("opentelemetry.sdk.metrics")
    class FakeProvider:
        def __init__(self, metric_readers):
            self.metric_readers = metric_readers
    sdk_metrics_module.MeterProvider = FakeProvider

    base.metrics = metrics_mod
    sys.modules["opentelemetry"] = base
    sys.modules["opentelemetry.metrics"] = metrics_mod
    sys.modules["opentelemetry.exporter.otlp.proto.grpc.metric_exporter"] = exporter_module
    sys.modules["opentelemetry.sdk.metrics"] = sdk_metrics_module
    sys.modules["opentelemetry.sdk.metrics.export"] = reader_module

    reloaded = importlib.reload(importlib.import_module(module_name))
    reloaded.configure_meter_provider()
    assert "provider" in captured

    if original:
        sys.modules[module_name] = original

