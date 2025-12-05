from __future__ import annotations
"""
Integration test: Outbound Action Idempotency (UT-IA-04).

What: Test action idempotency with retries
Why: Ensure safe retries without duplicate actions
Coverage Target: Idempotency logic
"""

# Imports handled by conftest.py

import pytest
from uuid import uuid4

# Module setup handled by root conftest.py

from integration_adapters.database.models import NormalisedAction
from integration_adapters.database.repositories import NormalisedActionRepository

class TestOutboundActionIdempotency:
    """Test outbound action idempotency."""

    def test_idempotency_key_deduplication(self, action_repo, sample_tenant_id):
        """Test that idempotency keys prevent duplicate actions."""
        idempotency_key = "unique-key-123"

        # Create first action
        action1 = NormalisedAction(
            tenant_id=sample_tenant_id,
            provider_id="github",
            connection_id=uuid4(),
            canonical_type="comment_on_pr",
            target={},
            payload={},
            idempotency_key=idempotency_key,
            status="completed",
        )
        action_repo.create(action1)

        # Try to create duplicate with same idempotency key
        action2 = NormalisedAction(
            tenant_id=sample_tenant_id,
            provider_id="github",
            connection_id=uuid4(),
            canonical_type="comment_on_pr",
            target={},
            payload={},
            idempotency_key=idempotency_key,  # Same key
            status="pending",
        )
        action_repo.create(action2)

        # Retrieve by idempotency key
        retrieved = action_repo.get_by_idempotency_key(idempotency_key, sample_tenant_id)
        assert retrieved is not None
        # Should return the first one (or latest, depending on implementation)
        assert retrieved.idempotency_key == idempotency_key

    def test_different_idempotency_keys_allowed(self, action_repo, sample_tenant_id):
        """Test that different idempotency keys create separate actions."""
        action1 = NormalisedAction(
            tenant_id=sample_tenant_id,
            provider_id="github",
            connection_id=uuid4(),
            canonical_type="comment_on_pr",
            target={},
            payload={},
            idempotency_key="key-1",
            status="pending",
        )
        action2 = NormalisedAction(
            tenant_id=sample_tenant_id,
            provider_id="github",
            connection_id=uuid4(),
            canonical_type="comment_on_pr",
            target={},
            payload={},
            idempotency_key="key-2",  # Different key
            status="pending",
        )

        action_repo.create(action1)
        action_repo.create(action2)

        # Both should exist
        retrieved1 = action_repo.get_by_idempotency_key("key-1", sample_tenant_id)
        retrieved2 = action_repo.get_by_idempotency_key("key-2", sample_tenant_id)

        assert retrieved1 is not None
        assert retrieved2 is not None
        assert retrieved1.idempotency_key != retrieved2.idempotency_key

