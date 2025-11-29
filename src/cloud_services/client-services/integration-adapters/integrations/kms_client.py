"""
M33 (Key Management Service) client for Integration Adapters Module.

What: Client for retrieving secrets from KMS per FR-3
Why: Secure secret management without storing secrets in code
Reads/Writes: KMS API
Contracts: PRD FR-3 (Authentication & Authorization)
Risks: KMS API failures, secret retrieval errors
"""

from __future__ import annotations

import os
from typing import Optional

import httpx


class KMSClient:
    """Client for Key Management Service (M33)."""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize KMS client.
        
        Args:
            base_url: KMS service base URL (defaults to environment variable)
        """
        self.base_url = base_url or os.getenv(
            "KMS_SERVICE_URL",
            "http://localhost:8000"
        ).rstrip("/")
        self.client = httpx.Client(timeout=30.0)

    def get_secret(self, secret_id: str, tenant_id: str) -> Optional[str]:
        """
        Retrieve secret from KMS by secret ID.
        
        Args:
            secret_id: Secret ID (KID/secret_id reference)
            tenant_id: Tenant ID for authorization
            
        Returns:
            Secret value, or None if not found
        """
        try:
            response = self.client.get(
                f"{self.base_url}/v1/secrets/{secret_id}",
                headers={"X-Tenant-ID": tenant_id},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("secret_value")
        except Exception:
            return None

    def refresh_token(self, secret_id: str, tenant_id: str) -> Optional[str]:
        """
        Refresh OAuth token.
        
        Args:
            secret_id: Secret ID
            tenant_id: Tenant ID
            
        Returns:
            New token, or None if refresh failed
        """
        try:
            response = self.client.post(
                f"{self.base_url}/v1/secrets/{secret_id}/refresh",
                headers={"X-Tenant-ID": tenant_id},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("secret_value")
        except Exception:
            return None

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

