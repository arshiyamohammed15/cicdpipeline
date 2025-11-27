"""
Mock dependencies for IAM service (M27, M29, M32).

What: Mock implementations of Evidence & Audit Ledger (M27), Data & Memory Plane (M29), Identity & Trust Plane (M32)
Why: Enables IAM implementation before dependencies are available, will be replaced with real implementations
Reads/Writes: Mock storage (in-memory), mock signing (Ed25519), mock trust verification
Contracts: Interface contracts for M27, M29, M32 integration
Risks: Mock implementations not production-ready, must be replaced before production deployment
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class MockM27EvidenceLedger:
    """
    Mock Evidence & Audit Ledger (M27) for receipt signing and verification.

    Per IAM spec: Receipts are Ed25519-signed, verification public keys distributed via trust store.
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

    def get_public_key(self) -> bytes:
        """
        Get public key for receipt verification.

        Returns:
            Public key bytes (Ed25519)
        """
        if not self.public_key:
            return b"mock_public_key"
        return self.public_key.public_bytes(
            encoding=self.serialization.Encoding.Raw,
            format=self.serialization.PublicFormat.Raw
        )


class MockM29DataPlane:
    """
    Mock Data & Memory Plane (M29) for policy storage and caches.

    Per IAM spec: Policy store with versioning, immutable releases, SHA-256 snapshot_id.
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

    def list_policies(self) -> List[str]:
        """
        List all policy identifiers.

        Returns:
            List of policy identifiers
        """
        return list(self.policies.keys())

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


class MockM32TrustPlane:
    """
    Mock Identity & Trust Plane (M32) for device/service identities and mTLS.

    Per IAM spec: mTLS between internal services, device/service identities.
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
        Get device posture (secure, unknown, insecure).

        Args:
            device_id: Device identifier

        Returns:
            Device posture string
        """
        return self.device_postures.get(device_id, "unknown")

    def register_identity(self, identity_id: str, identity_data: Dict[str, Any]) -> None:
        """
        Register service or device identity.

        Args:
            identity_id: Identity identifier
            identity_data: Identity data dictionary
        """
        self.identities[identity_id] = identity_data

    def register_device_posture(self, device_id: str, posture: str) -> None:
        """
        Register device posture.

        Args:
            device_id: Device identifier
            posture: Device posture (secure, unknown, insecure)
        """
        if posture not in ["secure", "unknown", "insecure"]:
            raise ValueError(f"Invalid device posture: {posture}")
        self.device_postures[device_id] = posture
