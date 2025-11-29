"""
GitHub webhook signature verification.

What: HMAC-SHA256 signature verification for GitHub webhooks per FR-4
Why: Ensure webhook authenticity
Reads/Writes: Webhook payloads and signatures
Contracts: PRD FR-4 (Webhook Ingestion)
Risks: Signature verification failures, replay attacks
"""

from __future__ import annotations

import hmac
import hashlib
from typing import Dict, Optional


class GitHubWebhookVerifier:
    """Verifies GitHub webhook signatures using HMAC-SHA256."""

    @staticmethod
    def verify_signature(
        payload: bytes, signature: str, secret: str
    ) -> bool:
        """
        Verify GitHub webhook signature.
        
        Args:
            payload: Raw webhook payload bytes
            signature: X-Hub-Signature-256 header value (format: sha256=<hash>)
            secret: Webhook secret
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not signature or not secret:
            return False
        
        # Extract hash from signature header
        # Format: sha256=<hash>
        if not signature.startswith("sha256="):
            return False
        
        expected_hash = signature[7:]  # Remove "sha256=" prefix
        
        # Calculate HMAC-SHA256
        computed_hash = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(computed_hash, expected_hash)

    @staticmethod
    def extract_signature(headers: Dict[str, str]) -> Optional[str]:
        """
        Extract signature from headers.
        
        Args:
            headers: HTTP headers
            
        Returns:
            Signature value, or None if not found
        """
        # GitHub uses X-Hub-Signature-256 for HMAC-SHA256
        return headers.get("X-Hub-Signature-256") or headers.get("x-hub-signature-256")

