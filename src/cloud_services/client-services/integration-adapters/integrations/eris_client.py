"""
ERIS (Evidence & Receipt Indexing Service) client for Integration Adapters Module.

What: Client for emitting ERIS receipts per FR-13
Why: Audit trail for integration actions
Reads/Writes: ERIS API
Contracts: PRD FR-13 (Evidence & Receipts)
Risks: ERIS API failures, receipt emission errors
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx


class ERISClient:
    """Client for Evidence & Receipt Indexing Service (ERIS)."""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize ERIS client.
        
        Args:
            base_url: ERIS service base URL (defaults to environment variable)
        """
        self.base_url = base_url or os.getenv(
            "ERIS_SERVICE_URL",
            "http://localhost:8000"
        ).rstrip("/")
        self.client = httpx.Client(timeout=30.0)

    def emit_receipt(
        self,
        tenant_id: str,
        connection_id: str,
        provider_id: str,
        operation_type: str,
        request_metadata: Dict[str, Any],
        result: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> bool:
        """
        Emit ERIS receipt for integration action.
        
        Args:
            tenant_id: Tenant ID
            connection_id: Connection ID
            provider_id: Provider identifier
            operation_type: Operation type (e.g., "integration.action.github.create_comment")
            request_metadata: Request metadata (redacted)
            result: Operation result (success/failure, status codes)
            correlation_id: Optional correlation ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            receipt = {
                "tenant_id": tenant_id,
                "connection_id": connection_id,
                "provider_id": provider_id,
                "operation_type": operation_type,
                "request_metadata": request_metadata,
                "result": result,
                "correlation_id": correlation_id,
            }
            
            response = self.client.post(
                f"{self.base_url}/v1/receipts",
                json=receipt,
            )
            response.raise_for_status()
            return True
        except Exception:
            return False

    def emit_receipts(self, receipts: list[Dict[str, Any]]) -> int:
        """
        Emit multiple ERIS receipts (batch).
        
        Args:
            receipts: List of receipt dictionaries
            
        Returns:
            Number of successfully emitted receipts
        """
        if not receipts:
            return 0
        
        try:
            response = self.client.post(
                f"{self.base_url}/v1/receipts/batch",
                json={"receipts": receipts},
            )
            response.raise_for_status()
            return len(receipts)
        except Exception:
            return 0

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

