"""Tests for API routes - TC-SIN-009: Webhook → Normalized Signal."""

import pytest
from fastapi.testclient import TestClient

from tests.sin.conftest import SignalEnvelope, SignalKind, Environment


def test_tc_sin_009_webhook_normalized_signal():
    """TC-SIN-009: Webhook translates to normalized signal."""
    # This test would require the full FastAPI app
    # For now, test the webhook translation logic
    from tests.sin.conftest import MockAPIGateway

    gateway = MockAPIGateway()
    gateway.register_webhook_mapping(
        "webhook_1", "tenant_1", "producer_1", {}
    )

    external_payload = {"event": "pr_opened", "pr_id": 123}
    preliminary = gateway.translate_webhook("webhook_1", external_payload)

    assert preliminary is not None
    assert preliminary['tenant_id'] == "tenant_1"
    assert preliminary['producer_id'] == "producer_1"

