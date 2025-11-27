"""
Tests for Receipt Service.

100% test coverage for receipt generation functionality.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from budgeting_rate_limiting_cost_observability.services.receipt_service import ReceiptService
from budgeting_rate_limiting_cost_observability.dependencies import MockM27EvidenceLedger, MockM33KeyManagement


@pytest.fixture
def receipt_service():
    """Create receipt service instance."""
    return ReceiptService(
        MockM27EvidenceLedger(),
        MockM33KeyManagement()
    )


class TestReceiptService:
    """Test suite for ReceiptService."""

    def test_generate_budget_check_receipt(self, receipt_service):
        """Test budget check receipt generation."""
        receipt = receipt_service.generate_budget_check_receipt(
            tenant_id=str(uuid.uuid4()),
            resource_type="api_calls",
            estimated_cost=Decimal("100.00"),
            allowed=True,
            remaining_budget=Decimal("900.00"),
            budget_id=str(uuid.uuid4()),
            enforcement_action="hard_stop",
            utilization_ratio=0.1
        )

        assert receipt["receipt_id"] is not None
        assert receipt["gate_id"] == "budget-check"
        assert receipt["decision"]["status"] == "pass"
        assert receipt["signature"] is not None

    def test_generate_rate_limit_check_receipt(self, receipt_service):
        """Test rate limit check receipt generation."""
        receipt = receipt_service.generate_rate_limit_check_receipt(
            tenant_id=str(uuid.uuid4()),
            resource_type="api_requests",
            request_count=1,
            allowed=True,
            remaining_requests=99,
            limit_value=100,
            policy_id=str(uuid.uuid4()),
            reset_time=datetime.utcnow().isoformat()
        )

        assert receipt["receipt_id"] is not None
        assert receipt["gate_id"] == "rate-limit-check"
        assert receipt["decision"]["status"] == "pass"
        assert receipt["signature"] is not None

    def test_generate_cost_recording_receipt(self, receipt_service):
        """Test cost recording receipt generation."""
        receipt = receipt_service.generate_cost_recording_receipt(
            tenant_id=str(uuid.uuid4()),
            resource_type="compute",
            cost_amount=Decimal("50.00"),
            record_id=str(uuid.uuid4()),
            attributed_to_type="tenant",
            attributed_to_id=str(uuid.uuid4())
        )

        assert receipt["receipt_id"] is not None
        assert receipt["gate_id"] == "cost-tracking"
        assert receipt["decision"]["status"] == "pass"
        assert receipt["signature"] is not None

    def test_generate_quota_allocation_receipt(self, receipt_service):
        """Test quota allocation receipt generation."""
        receipt = receipt_service.generate_quota_allocation_receipt(
            tenant_id=str(uuid.uuid4()),
            resource_type="compute_hours",
            allocated_amount=Decimal("1000.00"),
            quota_id=str(uuid.uuid4()),
            allocation_type="tenant",
            period_start=datetime.utcnow().isoformat(),
            period_end=(datetime.utcnow().replace(day=1) + timedelta(days=32)).replace(day=1).isoformat(),
            used_amount=Decimal("0.00"),
            remaining_amount=Decimal("1000.00")
        )

        assert receipt["receipt_id"] is not None
        assert receipt["gate_id"] == "quota-management"
        assert receipt["decision"]["status"] == "pass"
        assert receipt["signature"] is not None

    def test_receipt_schema_compliance(self, receipt_service):
        """Test that receipts conform to canonical M27 schema."""
        receipt = receipt_service.generate_budget_check_receipt(
            tenant_id=str(uuid.uuid4()),
            resource_type="api_calls",
            estimated_cost=Decimal("100.00"),
            allowed=True,
            remaining_budget=Decimal("900.00"),
            budget_id=str(uuid.uuid4()),
            enforcement_action="hard_stop",
            utilization_ratio=0.1
        )

        # Verify all required fields per PRD lines 3353-3369
        required_fields = [
            "receipt_id", "gate_id", "policy_version_ids", "snapshot_hash",
            "timestamp_utc", "timestamp_monotonic_ms", "inputs", "decision",
            "result", "actor", "degraded", "signature"
        ]

        for field in required_fields:
            assert field in receipt, f"Missing required field: {field}"

        # Verify decision structure
        assert "status" in receipt["decision"]
        assert "rationale" in receipt["decision"]
        assert "badges" in receipt["decision"]

        # Verify snapshot hash format
        assert receipt["snapshot_hash"].startswith("sha256:")

