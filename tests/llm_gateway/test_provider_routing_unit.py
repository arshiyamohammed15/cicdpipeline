from __future__ import annotations
"""
Unit tests for ProviderClient multi-tenant routing (FR-10).
"""


import pytest

from cloud_services.llm_gateway.clients import ProviderClient  # type: ignore  # pylint: disable=import-error


@pytest.mark.llm_gateway_unit
def test_provider_routing_is_tenant_specific(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "cloud_services.llm_gateway.clients.provider_client.random.random",
        lambda: 1.0,
    )
    client = ProviderClient()

    # Register explicit routes for tenantA and tenantB
    client.register_route("tenantA", "default_chat", "provider/model-A")
    client.register_route("tenantB", "default_chat", "provider/model-B")

    resp_a = client.invoke(
        tenant_id="tenantA",
        logical_model_id="default_chat",
        prompt="hello from A",
        operation_type="chat",
        fallback=False,
    )
    resp_b = client.invoke(
        tenant_id="tenantB",
        logical_model_id="default_chat",
        prompt="hello from B",
        operation_type="chat",
        fallback=False,
    )

    assert resp_a["model"] == "provider/model-A"
    assert resp_b["model"] == "provider/model-B"
    # Ensure responses contain their own tenant-specific model id
    assert "provider/model-A" in resp_a["content"]
    assert "provider/model-B" in resp_b["content"]

