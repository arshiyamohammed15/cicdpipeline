"""
EPC-1 (Identity & Access Management) client for Integration Adapters Module.

What: Client for IAM token validation per PRD Section 11
Why: Authenticate and authorize API requests
Reads/Writes: IAM API
Contracts: PRD Section 11 (Authentication requirements)
Risks: IAM API failures, token validation errors
"""

from __future__ import annotations

import os
from typing import Dict, Optional

import httpx


class IAMClient:
    """Client for Identity & Access Management service (EPC-1)."""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize IAM client.
        
        Args:
            base_url: IAM service base URL (defaults to environment variable)
        """
        self.base_url = base_url or os.getenv(
            "IAM_SERVICE_URL",
            "http://localhost:8000"
        ).rstrip("/")
        self.client = httpx.Client(timeout=30.0)

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify IAM token.
        
        Args:
            token: IAM token to verify
            
        Returns:
            Token claims if valid, None otherwise
        """
        try:
            response = self.client.post(
                f"{self.base_url}/v1/auth/verify",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    def get_tenant_id(self, token: str) -> Optional[str]:
        """
        Extract tenant ID from token.
        
        Args:
            token: IAM token
            
        Returns:
            Tenant ID, or None if token is invalid
        """
        claims = self.verify_token(token)
        if claims:
            return claims.get("tenant_id")
        return None

    def check_role(self, token: str, role: str) -> bool:
        """
        Check if token has required role.
        
        Args:
            token: IAM token
            role: Required role
            
        Returns:
            True if token has role, False otherwise
        """
        claims = self.verify_token(token)
        if claims:
            roles = claims.get("roles", [])
            return role in roles
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

