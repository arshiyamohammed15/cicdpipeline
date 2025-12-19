"""
EPC-13 (Budgeting, Rate-Limiting & Cost Observability) client for Integration Adapters Module.

What: Client for budget checking and rate limit enforcement per FR-9
Why: Enforce budgets and rate limits before making API calls
Reads/Writes: EPC-13 API
Contracts: PRD FR-9 (Rate Limiting & Budgeting Integration)
Risks: Budget API failures, rate limit violations
"""

from __future__ import annotations

import os
from typing import Dict, Optional

import httpx


class BudgetClient:
    """Client for Budgeting & Rate-Limiting service (EPC-13)."""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize budget client.
        
        Args:
            base_url: EPC-13 service base URL (defaults to environment variable)
        """
        self.base_url = base_url or os.getenv(
            "BUDGET_SERVICE_URL",
            "http://localhost:8000"
        ).rstrip("/")
        self.client = httpx.Client(timeout=30.0)

    def check_budget(
        self,
        tenant_id: str,
        provider_id: str,
        connection_id: str,
        cost: float = 1.0,
    ) -> tuple[bool, Optional[Dict]]:
        """
        Check if budget allows the operation.
        
        Args:
            tenant_id: Tenant ID
            provider_id: Provider identifier
            connection_id: Connection ID
            cost: Cost of the operation (default: 1.0)
            
        Returns:
            Tuple of (allowed, budget_info)
        """
        try:
            response = self.client.post(
                f"{self.base_url}/v1/budgets/check",
                json={
                    "tenant_id": tenant_id,
                    "provider_id": provider_id,
                    "connection_id": connection_id,
                    "cost": cost,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("allowed", False), data.get("budget_info")
        except Exception:
            # On error, allow the operation (fail open)
            return True, None

    def check_rate_limit(
        self,
        tenant_id: str,
        provider_id: str,
        connection_id: str,
    ) -> tuple[bool, Optional[Dict]]:
        """
        Check if rate limit allows the operation.
        
        Args:
            tenant_id: Tenant ID
            provider_id: Provider identifier
            connection_id: Connection ID
            
        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        try:
            response = self.client.post(
                f"{self.base_url}/v1/rate-limits/check",
                json={
                    "tenant_id": tenant_id,
                    "provider_id": provider_id,
                    "connection_id": connection_id,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("allowed", False), data.get("rate_limit_info")
        except Exception:
            # On error, allow the operation (fail open)
            return True, None

    def record_usage(
        self,
        tenant_id: str,
        provider_id: str,
        connection_id: str,
        cost: float = 1.0,
    ) -> bool:
        """
        Record usage for budget tracking.
        
        Args:
            tenant_id: Tenant ID
            provider_id: Provider identifier
            connection_id: Connection ID
            cost: Cost of the operation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.client.post(
                f"{self.base_url}/v1/budgets/record",
                json={
                    "tenant_id": tenant_id,
                    "provider_id": provider_id,
                    "connection_id": connection_id,
                    "cost": cost,
                },
            )
            response.raise_for_status()
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

