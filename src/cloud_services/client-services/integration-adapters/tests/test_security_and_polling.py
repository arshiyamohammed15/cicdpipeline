import importlib
import importlib.util
import pathlib
import sys
from datetime import datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest


PACKAGE_DIR = pathlib.Path(__file__).resolve().parents[1]


def _ensure_package_alias() -> None:
    """
    The package directory is named with a hyphen; create an import alias
    so modules can be imported as `integration_adapters.*` for testing.
    """
    if "integration_adapters" in sys.modules:
        return

    spec = importlib.util.spec_from_file_location(
        "integration_adapters", PACKAGE_DIR / "__init__.py"
    )
    module = importlib.util.module_from_spec(spec)
    module.__path__ = [str(PACKAGE_DIR)]
    sys.modules["integration_adapters"] = module
    if spec.loader:
        spec.loader.exec_module(module)


_ensure_package_alias()

integration_service_mod = importlib.import_module(
    "integration_adapters.services.integration_service"
)
webhook_service_mod = importlib.import_module(
    "integration_adapters.services.webhook_service"
)
polling_service_mod = importlib.import_module(
    "integration_adapters.services.polling_service"
)
models_mod = importlib.import_module("integration_adapters.database.models")

IntegrationService = integration_service_mod.IntegrationService
WebhookService = webhook_service_mod.WebhookService
PollingService = polling_service_mod.PollingService
PollingCursor = models_mod.PollingCursor
IntegrationConnection = models_mod.IntegrationConnection


class _DummyMetrics:
    def __init__(self):
        self.received = []
        self.normalized = []
        self.errors = []

    def increment_webhook_received(self, provider_id, connection_id):
        self.received.append((provider_id, connection_id))

    def increment_event_normalized(self, provider_id, connection_id):
        self.normalized.append((provider_id, connection_id))

    def increment_webhook_error(self, provider_id, connection_id):
        self.errors.append((provider_id, connection_id))


def test_webhook_service_blocks_replay_before_processing(monkeypatch):
    integration_service = SimpleNamespace(process_webhook=lambda *_, **__: True)
    session = SimpleNamespace()
    service = WebhookService(integration_service, session)

    # Force replay protection to fail
    def fake_validate_webhook(**kwargs):
        return False, "duplicate"

    service.replay_protection.validate_webhook = fake_validate_webhook

    success, error = service.process_webhook(
        provider_id="github",
        connection_token=str(uuid4()),
        payload={"timestamp": datetime.utcnow().isoformat()},
        headers={},
    )

    assert success is False
    assert error == "duplicate"


def test_integration_service_requires_active_registration_and_provider_match(monkeypatch):
    connection_id = uuid4()
    registration_id = uuid4()
    connection = IntegrationConnection(
        tenant_id="tenant-1",
        provider_id="github",
        display_name="c1",
        auth_ref="secret-ref",
    )
    connection.connection_id = connection_id

    class _Repo:
        def __init__(self, obj):
            self.obj = obj

        def get_active_by_registration(self, reg_id, tenant_id=None):
            return self.obj if reg_id == registration_id else None

        def get_active_by_connection(self, conn_id, tenant_id=None):
            return [self.obj] if conn_id == connection_id else []

    registration = SimpleNamespace(
        registration_id=registration_id,
        connection_id=connection_id,
        status="active",
        secret_ref="wh-secret",
        connection=connection,
    )

    class _ConnectionRepo:
        def get_by_id(self, conn_id, tenant_id=None):
            if conn_id == connection_id and (tenant_id in (None, "tenant-1")):
                return connection
            return None

    class _Adapter:
        def __init__(self):
            self.webhook_secret = None

        def process_webhook(self, payload, headers):
            return {"event_type": "push", "payload": payload}

    class _Registry:
        def get_adapter(self, provider_id, conn_id, tenant_id):
            if provider_id == "github" and conn_id == connection_id:
                return _Adapter()
            return None

    metrics = _DummyMetrics()
    signal_mapper = SimpleNamespace(
        map_provider_event_to_signal_envelope=lambda **kwargs: SimpleNamespace(
            model_dump=lambda: {}, provider_id=kwargs.get("provider_id")
        )
    )

    service = IntegrationService(
        session=None,
        kms_client=SimpleNamespace(get_secret=lambda *_: "wh-secret"),
        budget_client=None,
        pm3_client=SimpleNamespace(ingest_signal=lambda *_: True),
        eris_client=None,
    )
    service.webhook_repo = _Repo(registration)
    service.connection_repo = _ConnectionRepo()
    service.adapter_registry = _Registry()
    service.metrics = metrics
    service.signal_mapper = signal_mapper

    assert service.process_webhook(
        provider_id="github",
        connection_token=str(registration_id),
        payload={"id": "evt1"},
        headers={},
    ) is True
    assert metrics.received == [("github", connection_id)]
    assert metrics.normalized == [("github", connection_id)]
    assert not metrics.errors

    # Provider mismatch should be rejected
    assert (
        service.process_webhook(
            provider_id="gitlab",
            connection_token=str(registration_id),
            payload={"id": "evt1"},
            headers={},
        )
        is False
    )


def test_polling_service_unpacks_poll_events_and_updates_cursor(monkeypatch):
    connection_id = uuid4()
    connection = IntegrationConnection(
        tenant_id="tenant-1",
        provider_id="github",
        display_name="c1",
        auth_ref="secret-ref",
        status="active",
    )
    connection.connection_id = connection_id

    class _ConnectionRepo:
        def get_by_id(self, conn_id, tenant_id):
            return connection

    created_cursors = []

    class _PollingRepo:
        def get_by_connection(self, conn_id):
            return None

        def create(self, cursor):
            created_cursors.append(cursor)
            return cursor

        def update(self, cursor):
            created_cursors.append(cursor)
            return cursor

    class _Adapter:
        def poll_events(self, cursor=None):
            return (
                [
                    {
                        "payload": {"foo": "bar"},
                        "event_type": "push",
                        "cursor_position": "cursor-1",
                        "id": "evt-1",
                        "occurred_at": datetime.utcnow(),
                    }
                ],
                "cursor-1",
            )

    class _Registry:
        def get_adapter(self, provider_id, conn_id, tenant_id):
            return _Adapter()

    metrics = _DummyMetrics()
    signal_mapper = SimpleNamespace(
        map_provider_event_to_signal_envelope=lambda **kwargs: SimpleNamespace()
    )

    service = PollingService(session=None, budget_client=None, pm3_client=SimpleNamespace(ingest_signal=lambda *_: True))
    service.connection_repo = _ConnectionRepo()
    service.polling_repo = _PollingRepo()
    service.adapter_registry = _Registry()
    service.signal_mapper = signal_mapper
    service.metrics = metrics
    service.audit = SimpleNamespace(log_error=lambda **kwargs: None)

    assert service.poll_connection(connection_id, "tenant-1", poll_interval_minutes=0) is True
    assert created_cursors, "Cursor should be created or updated after polling"

