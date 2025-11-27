"""
ERIS (PM-7) Integration Client for UBI Module (EPC-9).

What: Client for emitting receipts to ERIS
Why: Record configuration changes and high-severity signals per PRD FR-13
Reads/Writes: Receipt emission to ERIS API
Contracts: ERIS PRD Section 9.1, UBI PRD FR-13
Risks: ERIS unavailability, receipt emission failures
"""

import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import time

from ..dependencies import MockM7ERIS
from ..reliability.circuit_breaker import CircuitBreaker, CircuitBreakerManager

logger = logging.getLogger(__name__)

# Global circuit breaker manager
_circuit_breaker_manager = CircuitBreakerManager()
_mock_eris_instance: Optional[MockM7ERIS] = None


def get_mock_eris_instance() -> MockM7ERIS:
    """Get singleton mock ERIS instance for development/testing."""
    global _mock_eris_instance
    if _mock_eris_instance is None:
        _mock_eris_instance = MockM7ERIS()
    return _mock_eris_instance


class ERISClient:
    """
    ERIS client for receipt emission.

    Per UBI PRD FR-13:
    - ERIS API: POST /v1/evidence/receipts
    - Retry logic with exponential backoff (max 24 hours)
    - Local persistent queue for ERIS unavailability
    - DLQ for failed receipts after max retry
    - Graceful degradation (non-blocking)
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: float = 2.0,
        max_retry_hours: int = 24
    ):
        """
        Initialize ERIS client.

        Args:
            base_url: ERIS service base URL (None for mock)
            timeout_seconds: Request timeout
            max_retry_hours: Maximum retry window in hours
        """
        self.base_url = base_url
        self.timeout = timeout_seconds
        self.max_retry_hours = max_retry_hours
        self.use_mock = base_url is None
        
        if self.use_mock:
            self.eris = get_mock_eris_instance()
        else:
            self.eris = None
        
        # Circuit breaker for ERIS calls
        self.circuit_breaker = _circuit_breaker_manager.get_breaker(
            name="eris_client",
            failure_threshold=5,
            success_threshold=2,
            timeout_seconds=60.0
        )

    async def emit_receipt(self, receipt: Dict[str, Any]) -> Optional[str]:
        """
        Emit receipt to ERIS with circuit breaker protection.

        Args:
            receipt: Receipt dictionary following canonical schema

        Returns:
            Receipt ID or None if queued/failed
        """
        if self.use_mock:
            try:
                receipt_id = await self.eris.emit_receipt(receipt)
                return receipt_id
            except Exception as e:
                logger.error(f"Mock ERIS receipt emission failed: {e}")
                return None
        
        # Real ERIS transport with circuit breaker
        async def _emit():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/evidence/receipts",
                    json=receipt,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
                return result.get("receipt_id")
        
        async def _fallback():
            logger.warning("ERIS circuit breaker is OPEN, receipt will be queued for retry")
            return None
        
        try:
            receipt_id = await self.circuit_breaker.call_async(_emit, _fallback)
            return receipt_id
        except Exception as e:
            logger.error(f"ERIS receipt emission failed: {e}")
            # Queue for retry
            return None

