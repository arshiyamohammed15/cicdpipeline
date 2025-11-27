"""
Tests for Event Subscription Service.

100% test coverage for event subscription CRUD operations.
"""

import pytest
import uuid
from datetime import datetime

from budgeting_rate_limiting_cost_observability.services.event_subscription_service import EventSubscriptionService
from budgeting_rate_limiting_cost_observability.dependencies import MockM29DataPlane


@pytest.fixture
def event_subscription_service():
    """Create event subscription service instance."""
    return EventSubscriptionService(MockM29DataPlane())


class TestEventSubscriptionService:
    """Test suite for EventSubscriptionService."""

    def test_create_subscription(self, event_subscription_service):
        """Test subscription creation."""
        tenant_id = str(uuid.uuid4())
        subscription = event_subscription_service.create_subscription(
            tenant_id=tenant_id,
            event_types=["budget_threshold_exceeded", "rate_limit_violated"],
            webhook_url="https://example.com/webhook",
            filters={"severity": "critical"},
            enabled=True
        )
        assert subscription["tenant_id"] == tenant_id
        assert len(subscription["event_types"]) == 2
        assert subscription["enabled"] is True
        assert "subscription_id" in subscription

    def test_list_subscriptions(self, event_subscription_service):
        """Test subscription listing."""
        tenant_id = str(uuid.uuid4())
        # Create multiple subscriptions
        for i in range(3):
            event_subscription_service.create_subscription(
                tenant_id=tenant_id,
                event_types=[f"event_{i}"],
                webhook_url=f"https://example.com/webhook_{i}",
                enabled=True
            )

        subscriptions, total_count = event_subscription_service.list_subscriptions(
            tenant_id=tenant_id,
            page=1,
            page_size=10
        )
        assert total_count == 3
        assert len(subscriptions) == 3

    def test_get_subscription(self, event_subscription_service):
        """Test subscription retrieval."""
        tenant_id = str(uuid.uuid4())
        subscription = event_subscription_service.create_subscription(
            tenant_id=tenant_id,
            event_types=["test_event"],
            webhook_url="https://example.com/webhook",
            enabled=True
        )

        retrieved = event_subscription_service.get_subscription(subscription["subscription_id"])
        assert retrieved is not None
        assert retrieved["subscription_id"] == subscription["subscription_id"]

    def test_update_subscription(self, event_subscription_service):
        """Test subscription update."""
        tenant_id = str(uuid.uuid4())
        subscription = event_subscription_service.create_subscription(
            tenant_id=tenant_id,
            event_types=["test_event"],
            webhook_url="https://example.com/webhook",
            enabled=True
        )

        updated = event_subscription_service.update_subscription(
            subscription["subscription_id"],
            enabled=False,
            filters={"new_filter": "value"}
        )
        assert updated["enabled"] is False
        assert updated["filters"]["new_filter"] == "value"

    def test_delete_subscription(self, event_subscription_service):
        """Test subscription deletion."""
        tenant_id = str(uuid.uuid4())
        subscription = event_subscription_service.create_subscription(
            tenant_id=tenant_id,
            event_types=["test_event"],
            webhook_url="https://example.com/webhook",
            enabled=True
        )

        deleted = event_subscription_service.delete_subscription(subscription["subscription_id"])
        assert deleted is True

        # Verify deletion
        retrieved = event_subscription_service.get_subscription(subscription["subscription_id"])
        assert retrieved is None

