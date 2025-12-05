"""
Resilience test: ERIS Dependency (RF-UBI-02).

Per PRD Section 13.8: Test graceful degradation during ERIS unavailability.
"""


# Imports handled by conftest.py
import pytest
from user_behaviour_intelligence.integrations.eris_client import ERISClient
from user_behaviour_intelligence.reliability.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
)


class TestERISDependency:
    """Test ERIS dependency handling."""

    @pytest.mark.asyncio
    async def test_receipt_queuing_on_eris_failure(self):
        """Test that receipts are queued when ERIS is unavailable."""
        # Use mock ERIS that simulates unavailability
        eris_client = ERISClient(base_url=None)  # Mock mode
        
        # Simulate ERIS unavailability
        eris_client.eris.set_available(False)
        
        receipt = {
            "receipt_id": "test-receipt-1",
            "gate_id": "ubi",
            "tenant_id": "test-tenant"
        }
        
        # Attempt to emit receipt
        receipt_id = await eris_client.emit_receipt(receipt)
        
        # Should return None (queued for retry)
        assert receipt_id is None

    def test_circuit_breaker_opens_on_failures(self):
        """Test that circuit breaker opens after threshold failures."""
        breaker = CircuitBreaker(
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=60.0,
            name="test_breaker"
        )
        
        # Simulate failures
        for _ in range(3):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))
            except:
                pass
        
        # Circuit should be open
        assert breaker.state == CircuitState.OPEN

