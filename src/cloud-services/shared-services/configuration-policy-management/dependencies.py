"""
Mock dependencies for Configuration & Policy Management service (M21, M27, M29, M33, M34, M32).

What: Mock implementations of IAM (M21), Evidence Ledger (M27), Data Plane (M29), Key Management (M33), Schema Registry (M34), Trust Plane (M32)
Why: Enables M23 implementation before dependencies are available, will be replaced with real implementations
Reads/Writes: Mock storage (in-memory), mock signing (Ed25519), mock validation
Contracts: Interface contracts for M21, M27, M29, M33, M34, M32 integration per PRD
Risks: Mock implementations not production-ready, must be replaced before production deployment
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class MockM21IAM:
    """
    Mock Identity & Access Management (M21) for access control.

    Per PRD: JWT token validation, access decision evaluation, policy bundles.
    """

    def __init__(self):
        """Initialize mock IAM with in-memory storage."""
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.policies: Dict[str, Dict[str, Any]] = {}

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token and return claims.

        Args:
            token: JWT token string

        Returns:
            Token claims dictionary or None if invalid
        """
        # Mock token verification
        if token.startswith("valid_"):
            return {
                "sub": "user-123",
                "scope": ["read", "write"],
                "tenant_id": "tenant-123",
                "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp())
            }
        return None

    def evaluate_access(self, subject: Dict[str, Any], action: str, resource: str) -> Dict[str, Any]:
        """
        Evaluate access decision.

        Args:
            subject: Subject information
            action: Action to perform
            resource: Resource to access

        Returns:
            Access decision dictionary
        """
        # Mock access evaluation - always allow for now
        return {
            "decision": "ALLOW",
            "reason": "Mock IAM - always allow",
            "receipt_id": str(hashlib.sha256(f"{subject}{action}{resource}".encode()).hexdigest()[:32])
        }

    def get_policy_bundle(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get policy bundle for tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Policy bundle dictionary or None
        """
        return self.policies.get(tenant_id)


class MockM27EvidenceLedger:
    """
    Mock Evidence & Audit Ledger (M27) for receipt signing and storage.

    Per PRD: Receipts are Ed25519-signed, stored in audit ledger.
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
            return "mock_signature_" + hashlib.sha256(json.dumps(receipt_data, sort_keys=True, default=str).encode()).hexdigest()[:32]

        receipt_json = json.dumps(receipt_data, sort_keys=True, default=str)
        receipt_bytes = receipt_json.encode('utf-8')
        signature = self.private_key.sign(receipt_bytes)
        return signature.hex()

    def verify_receipt(self, receipt_data: Dict[str, Any], signature: str) -> bool:
        """
        Verify receipt signature with Ed25519 public key.

        Args:
            receipt_data: Receipt data dictionary
            signature: Hex-encoded signature

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.public_key:
            return signature.startswith("mock_signature_")

        try:
            receipt_json = json.dumps(receipt_data, sort_keys=True, default=str)
            receipt_bytes = receipt_json.encode('utf-8')
            signature_bytes = bytes.fromhex(signature)
            self.public_key.verify(signature_bytes, receipt_bytes)
            return True
        except Exception as exc:
            logger.error(f"Receipt verification failed: {exc}")
            return False

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
    Mock Data & Memory Plane (M29) for policy storage and caches.

    Per PRD: Policy store with versioning, immutable releases, SHA-256 snapshot_id.
    """

    def __init__(self):
        """Initialize mock data plane with in-memory storage."""
        self.policies: Dict[str, Dict[str, Any]] = {}
        self.policy_versions: Dict[str, List[Dict[str, Any]]] = {}
        self.cache: Dict[str, Any] = {}

    def store_policy(self, policy_id: str, policy_data: Dict[str, Any]) -> str:
        """
        Store policy with versioning and generate SHA-256 snapshot_id.

        Args:
            policy_id: Policy identifier
            policy_data: Policy data dictionary

        Returns:
            SHA-256 snapshot_id
        """
        policy_json = json.dumps(policy_data, sort_keys=True, default=str)
        snapshot_id = hashlib.sha256(policy_json.encode('utf-8')).hexdigest()

        policy_data['snapshot_id'] = f"sha256:{snapshot_id}"
        policy_data['created_at'] = datetime.utcnow().isoformat()

        self.policies[policy_id] = policy_data

        if policy_id not in self.policy_versions:
            self.policy_versions[policy_id] = []
        self.policy_versions[policy_id].append(policy_data)

        return snapshot_id

    def get_policy(self, policy_id: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve policy from storage.

        Args:
            policy_id: Policy identifier
            version: Optional version identifier

        Returns:
            Policy data dictionary or None if not found
        """
        if version:
            versions = self.policy_versions.get(policy_id, [])
            for v in versions:
                if v.get('version') == version:
                    return v
            return None
        return self.policies.get(policy_id)

    def cache_set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Set cache value with optional TTL.

        Args:
            key: Cache key
            value: Cache value
            ttl_seconds: Optional TTL in seconds
        """
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


class MockM33KeyManagement:
    """
    Mock Key Management Service (M33) for cryptographic operations.

    Per PRD: Ed25519 signing for receipts, key rotation support.
    """

    def __init__(self):
        """Initialize mock key management."""
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            self.private_key = Ed25519PrivateKey.generate()
            self.public_key = self.private_key.public_key()
        except ImportError:
            logger.warning("cryptography library not available, using mock keys")
            self.private_key = None
            self.public_key = None

    def sign_data(self, data: bytes) -> str:
        """
        Sign data with Ed25519 private key.

        Args:
            data: Data bytes to sign

        Returns:
            Hex-encoded signature
        """
        if not self.private_key:
            return "mock_signature_" + hashlib.sha256(data).hexdigest()[:32]

        signature = self.private_key.sign(data)
        return signature.hex()

    def verify_signature(self, data: bytes, signature: str) -> bool:
        """
        Verify signature with Ed25519 public key.

        Args:
            data: Data bytes
            signature: Hex-encoded signature

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.public_key:
            return signature.startswith("mock_signature_")

        try:
            signature_bytes = bytes.fromhex(signature)
            self.public_key.verify(signature_bytes, data)
            return True
        except Exception:
            return False

    def get_public_key(self) -> bytes:
        """
        Get public key for verification.

        Returns:
            Public key bytes
        """
        if not self.public_key:
            return b"mock_public_key"
        return self.public_key.public_bytes_raw()


class MockM34SchemaRegistry:
    """
    Mock Schema Registry (M34) for schema validation.

    Per PRD: Schema validation for policies, configurations, compliance rules.
    """

    def __init__(self):
        """Initialize mock schema registry."""
        self.schemas: Dict[str, Dict[str, Any]] = {}

    def validate_schema(self, schema_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data against schema.

        Args:
            schema_type: Schema type (policy_definition, config_definition, compliance_rule)
            data: Data to validate

        Returns:
            Validation result dictionary
        """
        # Mock validation - always pass for now
        return {
            "valid": True,
            "errors": [],
            "schema_version": "1.0"
        }

    def register_schema(self, schema_id: str, schema_definition: Dict[str, Any]) -> None:
        """
        Register schema in registry.

        Args:
            schema_id: Schema identifier
            schema_definition: Schema definition
        """
        self.schemas[schema_id] = schema_definition

    def get_schema(self, schema_id: str) -> Optional[Dict[str, Any]]:
        """
        Get schema from registry.

        Args:
            schema_id: Schema identifier

        Returns:
            Schema definition or None if not found
        """
        return self.schemas.get(schema_id)


class MockM32TrustPlane:
    """
    Mock Identity & Trust Plane (M32) for device/service identities and mTLS.

    Per PRD: mTLS between internal services, device/service identities.
    """

    def __init__(self):
        """Initialize mock trust plane with in-memory identity store."""
        self.identities: Dict[str, Dict[str, Any]] = {}
        self.device_postures: Dict[str, str] = {}

    def verify_service_identity(self, service_id: str, certificate: Optional[bytes] = None) -> bool:
        """
        Verify service identity for mTLS.

        Args:
            service_id: Service identifier
            certificate: Optional client certificate

        Returns:
            True if identity is valid, False otherwise
        """
        return service_id in self.identities

    def get_device_posture(self, device_id: str) -> str:
        """
        Get device posture.

        Args:
            device_id: Device identifier

        Returns:
            Device posture (secure, unknown, insecure)
        """
        return self.device_postures.get(device_id, "unknown")

    def enrich_identity(self, user_id: str) -> Dict[str, Any]:
        """
        Enrich user identity with additional attributes.

        Args:
            user_id: User identifier

        Returns:
            Enriched identity dictionary
        """
        return {
            "user_id": user_id,
            "roles": ["user"],
            "attributes": {}
        }
