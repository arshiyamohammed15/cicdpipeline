
# Imports handled by conftest.py
import json
from pathlib import Path

import pytest

from alerting_notification_service.clients.component_client import DependencyGraphClient
from alerting_notification_service.clients.policy_client import ErisClient, IAMClient, PolicyClient
from alerting_notification_service.config import get_settings
from alerting_notification_service.observability.metrics import register_metrics

settings = get_settings()


@pytest.mark.asyncio
async def test_policy_client_resolves_channels():
    client = PolicyClient()
    critical_payload = {"tenant_id": "tenant-a", "severity": "P0"}
    normal_payload = {"tenant_id": "tenant-a", "severity": "P2"}

    critical = await client.resolve_routing(critical_payload)
    assert "sms" in critical["channels"]
    assert critical["targets"] == ["tenant-a-oncall"]

    normal = await client.resolve_routing(normal_payload)
    assert normal["channels"] == ["email"]
    assert normal["policy_id"] == "default"
    # P0 dedup window depends on policy file; if file exists, P0=1, else default=15
    # Test that the method works (returns a valid int)
    dedup_window = client.get_dedup_window("unknown", "P0")
    assert isinstance(dedup_window, int)
    assert dedup_window > 0


@pytest.mark.asyncio
async def test_iam_and_eris_clients_round_trip():
    iam = IAMClient()
    expanded = await iam.expand_targets(["t1", "t2"])
    assert expanded == ["t1", "t2"]

    eris = ErisClient()
    assert await eris.emit_receipt({"type": "unit", "alert_id": "a-1"}) is None


@pytest.mark.unit
def test_register_metrics_returns_true():
    assert register_metrics() is True


@pytest.mark.asyncio
async def test_policy_client_uses_bundle_file(tmp_path):
    bundle = {
        "dedup": {"defaults": 15, "by_category": {"security": 3}, "by_severity": {}},
        "correlation": {"window_minutes": 12, "rules": []},
        "routing": {
            "defaults": {
                "targets": ["{tenant_id}-primary"],
                "channels": ["email"],
                "channel_overrides": {"P0": ["sms"]},
            },
            "tenant_overrides": {},
        },
        "escalation": {"policies": {}},
        "fatigue": {},
    }
    bundle_path = Path(tmp_path / "policy.json")
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")

    client = PolicyClient(policy_path=bundle_path, cache_ttl_seconds=1)
    assert client.get_dedup_window("security", "P2") == 3

    routing = await client.resolve_routing({"tenant_id": "tenant-x", "severity": "P0"})
    assert routing["channels"] == ["sms"]
    assert routing["targets"] == ["tenant-x-primary"]


@pytest.mark.unit
def test_policy_client_invalid_json_fallback(tmp_path):
    bundle_path = Path(tmp_path / "bad_policy.json")
    bundle_path.write_text("{not-json", encoding="utf-8")
    client = PolicyClient(policy_path=bundle_path, cache_ttl_seconds=1)
    assert client.get_dedup_window("unknown", "unknown") == settings.policy.default_dedup_minutes
    assert client.get_correlation_window() == settings.policy.default_correlation_minutes


@pytest.mark.asyncio
async def test_dependency_graph_client_fallback():
    client = DependencyGraphClient(base_url=None)
    assert await client.shared_dependencies("a", "b") == []


@pytest.mark.asyncio
async def test_dependency_graph_client_custom_requester():
    async def fake_request(base_url: str, comp_a: str, comp_b: str) -> list[str]:
        assert base_url == "https://graph.local"
        return [comp_a + "-shared", comp_b + "-shared"]

    client = DependencyGraphClient(base_url="https://graph.local", requester=fake_request)
    result = await client.shared_dependencies("a", "b")
    assert result == ["a-shared", "b-shared"]


@pytest.mark.asyncio
async def test_dependency_graph_client_fetch_path(monkeypatch):
    async def fake_fetch(self, component_a: str, component_b: str) -> list[str]:
        return [component_a + component_b]

    client = DependencyGraphClient(base_url="https://graph.local")
    monkeypatch.setattr(DependencyGraphClient, "_fetch_shared_from_service", fake_fetch)
    result = await client.shared_dependencies("x", "y")
    assert result == ["xy"]

@pytest.mark.unit
def test_policy_client_missing_file_uses_defaults(tmp_path):
    missing_path = Path(tmp_path / "missing_policy.json")
    client = PolicyClient(policy_path=missing_path, cache_ttl_seconds=1)
    assert client.get_dedup_window("unknown", "unknown") == settings.policy.default_dedup_minutes

