from __future__ import annotations

import asyncio
import json

import importlib.util
from pathlib import Path
import sys

import pytest

from tests.shared_harness import assert_enforcement_receipt_fields


@pytest.mark.alerting_regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_guard_max_events_stops_stream(session, monkeypatch):
    repo_root = Path(__file__).resolve().parents[5]
    src_root = repo_root / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    module_root = src_root / "cloud_services" / "shared-services" / "alerting-notification-service"
    spec = importlib.util.spec_from_loader("alerting_notification_service", loader=None, is_package=True)
    module = importlib.util.module_from_spec(spec)
    module.__path__ = [str(module_root)]
    sys.modules["alerting_notification_service"] = module

    from alerting_notification_service.config import get_settings
    from alerting_notification_service.dependencies import RequestContext
    from alerting_notification_service.routes import v1 as v1_routes

    monkeypatch.setenv("ALERT_STREAM_HEARTBEAT_SECONDS", "0.01")
    get_settings.cache_clear()
    settings = get_settings()
    settings.notifications.agent_stream_max_events = 1

    ctx = RequestContext(
        tenant_id="tenant-integration",
        actor_id="tester",
        roles=["global_admin"],
        allowed_tenants=["tenant-integration"],
        token_sub="tester",
    )

    receipts: list[dict] = []

    async def _capture_receipt(payload: dict) -> None:
        receipts.append(payload)

    monkeypatch.setattr(v1_routes._evidence_service.eris, "emit_receipt", _capture_receipt)

    response = await v1_routes.stream_alerts(session=session, ctx=ctx)

    try:
        chunk = await asyncio.wait_for(response.body_iterator.__anext__(), timeout=1.0)
        payload = chunk.decode() if isinstance(chunk, bytes) else chunk
        assert "data:" in payload

        with pytest.raises(StopAsyncIteration):
            await asyncio.wait_for(response.body_iterator.__anext__(), timeout=0.5)
    finally:
        aclose = getattr(response.body_iterator, "aclose", None)
        if callable(aclose):
            await aclose()
        get_settings.cache_clear()

    assert receipts
    receipt = next(item for item in receipts if item.get("type") == "sse_guard_terminated")
    assert_enforcement_receipt_fields(receipt, require_correlation=True)
    metadata = receipt.get("metadata", {})
    assert metadata.get("reason_code") == "SSE_MAX_EVENTS"
    assert metadata.get("stream_id", "").startswith("sub-")
    assert metadata.get("limits", {}).get("max_events") == 1
    assert metadata.get("observed", {}).get("events") == 1


@pytest.mark.alerting_regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_guard_limits_from_policy_bundle(session, monkeypatch, tmp_path):
    repo_root = Path(__file__).resolve().parents[5]
    src_root = repo_root / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    module_root = src_root / "cloud_services" / "shared-services" / "alerting-notification-service"
    spec = importlib.util.spec_from_loader("alerting_notification_service", loader=None, is_package=True)
    module = importlib.util.module_from_spec(spec)
    module.__path__ = [str(module_root)]
    sys.modules["alerting_notification_service"] = module

    from alerting_notification_service.config import get_settings
    from alerting_notification_service.dependencies import RequestContext
    from alerting_notification_service.routes import v1 as v1_routes
    from alerting_notification_service.clients import policy_client as policy_module

    async def _run_with_limit(max_events: int) -> int:
        policy_path = tmp_path / f"policy_{max_events}.json"
        policy_path.write_text(
            json.dumps({"sse_limits": {"max_events": max_events}}),
            encoding="utf-8",
        )
        monkeypatch.setenv("ALERT_STREAM_HEARTBEAT_SECONDS", "0.01")
        get_settings.cache_clear()
        settings = get_settings()
        settings.policy.policy_bundle_path = policy_path
        policy_module.settings = settings
        settings.notifications.agent_stream_max_events = None
        settings.notifications.agent_stream_max_bytes = None
        settings.notifications.agent_stream_max_duration_ms = None
        assert policy_module.PolicyClient().get_stream_limits().get("max_events") == max_events

        ctx = RequestContext(
            tenant_id="tenant-integration",
            actor_id="tester",
            roles=["global_admin"],
            allowed_tenants=["tenant-integration"],
            token_sub="tester",
        )

        receipts: list[dict] = []

        async def _capture_receipt(payload: dict) -> None:
            receipts.append(payload)

        monkeypatch.setattr(v1_routes._evidence_service.eris, "emit_receipt", _capture_receipt)
        response = await v1_routes.stream_alerts(session=session, ctx=ctx)

        try:
            for _ in range(max_events):
                await asyncio.wait_for(response.body_iterator.__anext__(), timeout=1.0)
            with pytest.raises(StopAsyncIteration):
                await asyncio.wait_for(response.body_iterator.__anext__(), timeout=0.5)
        finally:
            aclose = getattr(response.body_iterator, "aclose", None)
            if callable(aclose):
                await aclose()
            get_settings.cache_clear()

        receipt = next(item for item in receipts if item.get("type") == "sse_guard_terminated")
        observed = receipt.get("metadata", {}).get("observed", {}).get("events", 0)
        return int(observed)

    observed_one = await _run_with_limit(1)
    observed_two = await _run_with_limit(2)

    assert observed_one == 1
    assert observed_two == 2
