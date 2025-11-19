"""
Tests for Identity & Actor Provenance (IAPS) with EPC-1 adapter.

Covers PRD section 10.1: Identity deterministic, failure handling, clock skew.
"""

from datetime import datetime, timezone

import pytest

from src.shared_libs.cccs.identity import IdentityConfig, IdentityService
from src.shared_libs.cccs.types import ActorContext
from src.shared_libs.cccs.exceptions import ActorUnavailableError
from tests.cccs.mocks import MockEPC1Adapter
from unittest.mock import patch


def _context(**overrides):
    base = {
        "tenant_id": "tenant-123",
        "device_id": "device-abc",
        "session_id": "sess-1",
        "user_id": "user-9",
        "actor_type": "machine",
        "runtime_clock": datetime.now(timezone.utc),
        "extras": {},
    }
    base.update(overrides)
    return ActorContext(**base)


def test_identity_resolution_deterministic():
    """Test identity resolution is deterministic (stable actor_id given identical inputs)."""
    config = IdentityConfig(
        epc1_base_url="http://localhost:8001",
        epc1_timeout_seconds=5.0,
        epc1_api_version="v1",
    )

    with patch('src.shared_libs.cccs.identity.service.EPC1IdentityAdapter', MockEPC1Adapter):
        service = IdentityService(config)

        result1 = service.resolve_actor(_context())
        result2 = service.resolve_actor(_context())

        assert result1.actor_id == result2.actor_id
        assert result1.provenance_signature == result2.provenance_signature
        assert result1.normalization_version == "v1"


def test_identity_missing_fields():
    """Test identity resolution fails with missing fields."""
    config = IdentityConfig(
        epc1_base_url="http://localhost:8001",
        epc1_timeout_seconds=5.0,
        epc1_api_version="v1",
    )

    with patch('src.shared_libs.cccs.identity.service.EPC1IdentityAdapter', MockEPC1Adapter):
        service = IdentityService(config)

        ctx = _context(user_id="")
        with pytest.raises(ActorUnavailableError, match="Missing actor context fields"):
            service.resolve_actor(ctx)


def test_identity_failure_handling_missing_epc1_metadata():
    """Test identity failure handling when EPC-1 metadata is missing."""
    config = IdentityConfig(
        epc1_base_url="http://localhost:8001",
        epc1_timeout_seconds=5.0,
        epc1_api_version="v1",
    )

    with patch('src.shared_libs.cccs.identity.service.EPC1IdentityAdapter', MockEPC1Adapter):
        service = IdentityService(config)
        service._adapter._fail_verify = True

        with pytest.raises(ActorUnavailableError, match="Identity resolution failed"):
            service.resolve_actor(_context())


def test_identity_clock_skew_detection():
    """Test identity handles clock skew warnings."""
    config = IdentityConfig(
        epc1_base_url="http://localhost:8001",
        epc1_timeout_seconds=5.0,
        epc1_api_version="v1",
    )

    with patch('src.shared_libs.cccs.identity.service.EPC1IdentityAdapter', MockEPC1Adapter):
        service = IdentityService(config)

        ctx = _context(extras={"clock_skew_s": 2.5})  # > 1 second skew
        result = service.resolve_actor(ctx)
        # Clock skew should be detected and handled (warnings may be in provenance)
        assert result.actor_id is not None


def test_identity_deep_copy_context():
    """Test identity service deep-copies context to prevent mutation."""
    config = IdentityConfig(
        epc1_base_url="http://localhost:8001",
        epc1_timeout_seconds=5.0,
        epc1_api_version="v1",
    )

    with patch('src.shared_libs.cccs.identity.service.EPC1IdentityAdapter', MockEPC1Adapter):
        service = IdentityService(config)

        ctx = _context()
        original_user_id = ctx.user_id
        service.resolve_actor(ctx)

        # Context should not be mutated
        assert ctx.user_id == original_user_id


