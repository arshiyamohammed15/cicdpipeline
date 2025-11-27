"""
Mock dependencies for Contracts & Schema Registry (M33, M27, M29, M21).

What: Mock implementations of KMS (M33), Evidence Ledger (M27), Data Plane (M29), IAM (M21)
Why: Enables implementation before dependencies are available, will be replaced with real implementations
Reads/Writes: Mock storage (in-memory), mock signing (Ed25519), mock access control
Contracts: Interface contracts for M33, M27, M29, M21 integration
Risks: Mock implementations not production-ready, must be replaced before production deployment
"""

import hashlib
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


class MockM33KMS:
    """
    Mock Key Management Service (M33) for schema signing.

    Per PRD: Schema signing via KMS, signature verification.
    """

    def __init__(self):
        """Initialize mock KMS with Ed25519 key pair."""
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from cryptography.hazmat.primitives import serialization
            self.private_key = Ed25519PrivateKey.generate()
            self.public_key = self.private_key.public_key()
            self.serialization = serialization
        except ImportError:
            logger.warning("cryptography library not available, using mock signing")
            self.private_key = None
            self.public_key = None

    def sign_schema(self, schema_data: Dict[str, Any], tenant_id: str) -> str:
        """
        Sign schema with Ed25519 private key.

        Args:
            schema_data: Schema data dictionary
            tenant_id: Tenant identifier

        Returns:
            Hex-encoded Ed25519 signature
        """
        if not self.private_key:
            return "mock_signature_" + hashlib.sha256(
                json.dumps(schema_data, sort_keys=True, default=str).encode()
            ).hexdigest()[:32]

        schema_json = json.dumps(schema_data, sort_keys=True, default=str)
        schema_bytes = schema_json.encode('utf-8')
        signature = self.private_key.sign(schema_bytes)
        return signature.hex()

    def verify_signature(self, schema_data: Dict[str, Any], signature: str) -> bool:
        """
        Verify schema signature with Ed25519 public key.

        Args:
            schema_data: Schema data dictionary
            signature: Hex-encoded signature

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.public_key:
            return signature.startswith("mock_signature_")

        try:
            schema_json = json.dumps(schema_data, sort_keys=True, default=str)
            schema_bytes = schema_json.encode('utf-8')
            signature_bytes = bytes.fromhex(signature)
            self.public_key.verify(signature_bytes, schema_bytes)
            return True
        except Exception as exc:
            logger.error(f"Signature verification failed: {exc}")
            return False


class MockM27EvidenceLedger:
    """
    Mock Evidence & Audit Ledger (M27) for receipt storage.

    Per PRD: Receipt storage, receipt signing, audit trail.
    """

    def __init__(self):
        """Initialize mock evidence ledger with Ed25519 key pair."""
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from cryptography.hazmat.primitives import serialization
            self.private_key = Ed25519PrivateKey.generate()
            self.public_key = self.private_key.public_key()
            self.serialization = serialization
        except ImportError:
            logger.warning("cryptography library not available, using mock signing")
            self.private_key = None
            self.public_key = None
        self.receipts: Dict[str, Dict[str, Any]] = {}

    def sign_receipt(self, receipt_data: Dict[str, Any]) -> str:
        """
        Sign receipt with Ed25519 private key.

        Args:
            receipt_data: Receipt data dictionary

        Returns:
            Hex-encoded Ed25519 signature
        """
        if not self.private_key:
            return "mock_signature_" + hashlib.sha256(
                json.dumps(receipt_data, sort_keys=True, default=str).encode()
            ).hexdigest()[:32]

        receipt_json = json.dumps(receipt_data, sort_keys=True, default=str)
        receipt_bytes = receipt_json.encode('utf-8')
        signature = self.private_key.sign(receipt_bytes)
        return signature.hex()

    def store_receipt(self, receipt_id: str, receipt_data: Dict[str, Any]) -> None:
        """
        Store receipt in mock ledger.

        Args:
            receipt_id: Receipt identifier
            receipt_data: Receipt data dictionary
        """
        self.receipts[receipt_id] = receipt_data

    def get_receipt(self, receipt_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve receipt from mock ledger.

        Args:
            receipt_id: Receipt identifier

        Returns:
            Receipt data dictionary or None if not found
        """
        return self.receipts.get(receipt_id)


class MockM29DataPlane:
    """
    Mock Data & Memory Plane (M29) for schema storage and caching.

    Per PRD: Schema storage (fallback), cache management, analytics storage.
    """

    def __init__(self):
        """Initialize mock data plane with in-memory storage."""
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.cache: Dict[str, Any] = {}

    def store_schema(self, schema_id: str, schema_data: Dict[str, Any]) -> None:
        """
        Store schema in mock data plane.

        Args:
            schema_id: Schema identifier
            schema_data: Schema data dictionary
        """
        self.schemas[schema_id] = schema_data

    def get_schema(self, schema_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve schema from mock data plane.

        Args:
            schema_id: Schema identifier

        Returns:
            Schema data dictionary or None if not found
        """
        return self.schemas.get(schema_id)

    def cache_set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Set cache value with optional TTL.

        Args:
            key: Cache key
            value: Cache value
            ttl_seconds: Optional TTL in seconds
        """
        from datetime import timedelta
        cache_entry = {
            'value': value,
            'expires_at': (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat() if ttl_seconds else None
        }
        self.cache[key] = cache_entry

    def cache_get(self, key: str) -> Optional[Any]:
        """
        Get cache value if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        entry = self.cache.get(key)
        if not entry:
            return None

        if entry.get('expires_at'):
            expires_at = datetime.fromisoformat(entry['expires_at'])
            if datetime.utcnow() > expires_at:
                del self.cache[key]
                return None

        return entry.get('value')


class MockM21IAM:
    """
    Mock IAM Module (M21) for access control.

    Per PRD: Access control decisions, permission checking, tenant context validation.
    """

    def __init__(self):
        """Initialize mock IAM with in-memory policy store."""
        self.policies: Dict[str, List[str]] = {}  # tenant_id -> list of permissions

    def check_permission(
        self,
        tenant_id: str,
        user_id: str,
        permission: str,
        resource: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Check if user has permission.

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            permission: Permission to check (e.g., "schema_read", "schema_write")
            resource: Optional resource identifier

        Returns:
            Tuple of (is_allowed, reason)
        """
        # Mock: Allow all operations for now
        tenant_permissions = self.policies.get(tenant_id, [])

        # Check if permission is in tenant's allowed permissions
        if permission in tenant_permissions or len(tenant_permissions) == 0:
            return True, "Permission granted"

        return False, f"Permission '{permission}' denied for tenant '{tenant_id}'"

    def get_tenant_context(self, request_headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Extract tenant context from request headers.

        Args:
            request_headers: Request headers dictionary

        Returns:
            Tenant context dictionary or None
        """
        tenant_id = request_headers.get("X-Tenant-ID")
        if tenant_id:
            return {
                "tenant_id": tenant_id,
                "user_id": request_headers.get("X-User-ID", "unknown"),
                "module_id": request_headers.get("X-Module-ID", "M34")
            }
        return None
