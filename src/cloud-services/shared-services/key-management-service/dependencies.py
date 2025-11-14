"""
Mock dependencies for KMS service (M27, M29, M32, M21).

What: Mock implementations of Evidence & Audit Ledger (M27), Data & Memory Plane (M29),
      Identity & Trust Plane (M32), and IAM (M21)
Why: Enables KMS implementation before dependencies are available, will be replaced with real implementations
Reads/Writes: Mock storage (in-memory), mock signing (Ed25519), mock trust verification
Contracts: Interface contracts for M27, M29, M32, M21 integration
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

    Per KMS spec: Receipts are Ed25519-signed, verification public keys distributed via trust store.
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
    Mock Data & Memory Plane (M29) for key metadata storage and caches.

    Per KMS spec: Key metadata storage with versioning, immutable releases, SHA-256 snapshot_id.
    """

    def __init__(self):
        """Initialize mock data plane with in-memory storage."""
        self.key_metadata: Dict[str, Dict[str, Any]] = {}
        self.key_versions: Dict[str, List[Dict[str, Any]]] = {}
        self.cache: Dict[str, Any] = {}
        self.usage_tracking: Dict[str, Dict[str, int]] = {}  # key_id -> {date: count}

    def store_key_metadata(self, key_id: str, metadata: Dict[str, Any]) -> str:
        """
        Store key metadata with versioning and generate SHA-256 snapshot_id.

        Args:
            key_id: Key identifier
            metadata: Key metadata dictionary

        Returns:
            SHA-256 snapshot_id
        """
        metadata_json = json.dumps(metadata, sort_keys=True, default=str)
        snapshot_id = hashlib.sha256(metadata_json.encode('utf-8')).hexdigest()

        metadata['snapshot_id'] = f"sha256:{snapshot_id}"
        metadata['created_at'] = datetime.utcnow().isoformat()

        self.key_metadata[key_id] = metadata

        if key_id not in self.key_versions:
            self.key_versions[key_id] = []
        self.key_versions[key_id].append(metadata)

        return snapshot_id

    def get_key_metadata(self, key_id: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve key metadata from storage.

        Args:
            key_id: Key identifier
            version: Optional version identifier

        Returns:
            Key metadata dictionary or None if not found
        """
        if version:
            versions = self.key_versions.get(key_id, [])
            for v in versions:
                if v.get('version') == version:
                    return v
            return None
        return self.key_metadata.get(key_id)

    def list_keys(self, tenant_id: Optional[str] = None, environment: Optional[str] = None,
                  plane: Optional[str] = None) -> List[str]:
        """
        List all key identifiers, optionally filtered by tenant, environment, plane.

        Args:
            tenant_id: Optional tenant filter
            environment: Optional environment filter
            plane: Optional plane filter

        Returns:
            List of key identifiers
        """
        keys = list(self.key_metadata.keys())
        if tenant_id or environment or plane:
            filtered = []
            for key_id in keys:
                metadata = self.key_metadata[key_id]
                if tenant_id and metadata.get('tenant_id') != tenant_id:
                    continue
                if environment and metadata.get('environment') != environment:
                    continue
                if plane and metadata.get('plane') != plane:
                    continue
                filtered.append(key_id)
            return filtered
        return keys

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

    def increment_usage(self, key_id: str, date: str) -> int:
        """
        Increment usage count for a key on a specific date.

        Args:
            key_id: Key identifier
            date: Date string (YYYY-MM-DD)

        Returns:
            New usage count for the date
        """
        if key_id not in self.usage_tracking:
            self.usage_tracking[key_id] = {}
        if date not in self.usage_tracking[key_id]:
            self.usage_tracking[key_id][date] = 0
        self.usage_tracking[key_id][date] += 1
        return self.usage_tracking[key_id][date]

    def get_usage_count(self, key_id: str, date: str) -> int:
        """
        Get usage count for a key on a specific date.

        Args:
            key_id: Key identifier
            date: Date string (YYYY-MM-DD)

        Returns:
            Usage count for the date
        """
        return self.usage_tracking.get(key_id, {}).get(date, 0)


class MockM32TrustPlane:
    """
    Mock Identity & Trust Plane (M32) for certificate validation and service identity verification.

    Per KMS spec: mTLS between internal services, device/service identities, certificate validation.
    """

    def __init__(self):
        """Initialize mock trust plane with in-memory identity and certificate store."""
        self.identities: Dict[str, Dict[str, Any]] = {}
        self.certificates: Dict[str, bytes] = {}
        self.trust_anchors: Dict[str, Dict[str, Any]] = {}
        self.revoked_certificates: set = set()

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

    def validate_certificate(self, certificate: bytes) -> tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Validate certificate and extract identity information.

        Args:
            certificate: Certificate bytes

        Returns:
            Tuple of (is_valid, error_message, identity_info)
        """
        cert_hash = hashlib.sha256(certificate).hexdigest()
        if cert_hash in self.revoked_certificates:
            return False, "Certificate revoked", None

        # Mock validation - in production would parse X.509 and validate chain
        identity_info = {
            'tenant_id': 'mock-tenant',
            'environment': 'dev',
            'plane': 'shared',
            'module_id': 'M21'
        }
        return True, None, identity_info

    def extract_identity_from_certificate(self, certificate: bytes) -> Optional[Dict[str, Any]]:
        """
        Extract identity information from certificate.

        Args:
            certificate: Certificate bytes

        Returns:
            Identity information dictionary or None
        """
        is_valid, error, identity_info = self.validate_certificate(certificate)
        if is_valid:
            return identity_info
        return None

    def register_identity(self, identity_id: str, identity_data: Dict[str, Any]) -> None:
        """
        Register service or device identity.

        Args:
            identity_id: Identity identifier
            identity_data: Identity data dictionary
        """
        self.identities[identity_id] = identity_data

    def add_trust_anchor(self, anchor_id: str, anchor_data: Dict[str, Any]) -> None:
        """
        Add trust anchor (CA certificate, root certificate).

        Args:
            anchor_id: Trust anchor identifier
            anchor_data: Trust anchor data (certificate, type, etc.)
        """
        self.trust_anchors[anchor_id] = anchor_data

    def revoke_certificate(self, certificate: bytes) -> None:
        """
        Revoke a certificate.

        Args:
            certificate: Certificate bytes
        """
        cert_hash = hashlib.sha256(certificate).hexdigest()
        self.revoked_certificates.add(cert_hash)


class MockM21IAM:
    """
    Mock IAM Module (M21) for JWT verification.

    Per KMS spec: JWT verification for optional authentication augmentation.
    """

    def __init__(self):
        """Initialize mock IAM with in-memory token store."""
        self.valid_tokens: Dict[str, Dict[str, Any]] = {}
        self.revoked_tokens: set = set()

    def verify_jwt(self, token: str) -> tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Verify JWT token.

        Args:
            token: JWT token string

        Returns:
            Tuple of (is_valid, claims_dict, error_message)
        """
        if token in self.revoked_tokens:
            return False, None, "Token revoked"

        # Mock verification - in production would verify signature and claims
        if token in self.valid_tokens:
            return True, self.valid_tokens[token], None

        # Mock token parsing
        try:
            import jwt
            decoded = jwt.decode(token, options={"verify_signature": False})
            required_claims = ["sub", "module_id", "tenant_id", "environment"]
            missing_claims = [claim for claim in required_claims if claim not in decoded]
            if missing_claims:
                return False, None, f"Missing required claims: {', '.join(missing_claims)}"
            return True, decoded, None
        except ImportError:
            return False, None, "JWT library not available"
        except Exception as exc:
            return False, None, f"Token verification failed: {str(exc)}"

    def register_token(self, token: str, claims: Dict[str, Any]) -> None:
        """
        Register a valid token (for testing).

        Args:
            token: Token string
            claims: Token claims dictionary
        """
        self.valid_tokens[token] = claims

    def revoke_token(self, token: str) -> None:
        """
        Revoke a token.

        Args:
            token: Token string
        """
        self.revoked_tokens.add(token)
