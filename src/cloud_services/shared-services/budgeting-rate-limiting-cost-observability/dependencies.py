"""
Mock dependencies for EPC-13 (Budgeting, Rate-Limiting & Cost Observability) service (PM-7, CCP-6, EPC-4, EPC-11, EPC-1).

What: Mock implementations of Evidence & Receipt Indexing Service (PM-7 / ERIS), Data & Memory Plane (CCP-6),
      Alerting & Notification Service (EPC-4), Key & Trust Management (EPC-11), and IAM (EPC-1)
Why: Enables EPC-13 implementation before dependencies are available, will be replaced with real implementations
Reads/Writes: Mock storage (in-memory), mock signing (Ed25519), mock event publishing
Contracts: Interface contracts for PM-7, CCP-6, EPC-4, EPC-11, EPC-1 integration
Risks: Mock implementations not production-ready, must be replaced before production deployment

Note: Class names use legacy M27/M29/M31/M33/M21 identifiers for backward compatibility. Comments reference new module IDs (PM-7, CCP-6, EPC-4, EPC-11, EPC-1).
"""

import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class MockM27EvidenceLedger:
    """
    Mock Evidence & Receipt Indexing Service (PM-7 / ERIS) for receipt signing and storage.

    Per EPC-13 PRD: Receipts are Ed25519-signed, stored in audit ledger using canonical receipt schema.
    Note: Class name uses legacy M27 identifier for backward compatibility. Module is PM-7 (ERIS).
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
        Sign receipt with Ed25519 private key via M33.

        Args:
            receipt_data: Receipt data dictionary (canonical M27 format)

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
    Mock Data & Memory Plane (CCP-6) for persistent storage.

    Per EPC-13 PRD: Persistent storage for budgets, rate limits, costs, and quotas.
    Note: Class name uses legacy M29 identifier for backward compatibility. Module is CCP-6 (Data & Memory Plane).
    """

    def __init__(self):
        """Initialize mock data plane with in-memory storage."""
        self.storage: Dict[str, Dict[str, Any]] = {}
        self.cache: Dict[str, Any] = {}

    def store(self, key: str, value: Dict[str, Any]) -> None:
        """
        Store data in mock data plane.

        Args:
            key: Storage key
            value: Data dictionary
        """
        self.storage[key] = value

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from mock data plane.

        Args:
            key: Storage key

        Returns:
            Data dictionary or None if not found
        """
        return self.storage.get(key)

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


class MockM31NotificationEngine:
    """
    Mock Alerting & Notification Service (EPC-4) for event delivery.

    Per EPC-13 PRD: EPC-13 emits logical alert events for EPC-4 to deliver.
    Note: Class name uses legacy M31 identifier for backward compatibility. Module is EPC-4 (Alerting & Notification Service).
    """

    def __init__(self):
        """Initialize mock notification engine with in-memory event store."""
        self.events: List[Dict[str, Any]] = []

    def publish_event(self, event: Dict[str, Any]) -> str:
        """
        Publish event to notification engine.

        Args:
            event: Event dictionary with common envelope

        Returns:
            Event ID
        """
        event_id = str(uuid.uuid4())
        event['event_id'] = event_id
        event['published_at'] = datetime.utcnow().isoformat()
        self.events.append(event)
        logger.info(f"Published event {event.get('event_type')} with ID {event_id}")
        return event_id

    def get_events(self, tenant_id: Optional[str] = None, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get events from notification engine.

        Args:
            tenant_id: Optional tenant filter
            event_type: Optional event type filter

        Returns:
            List of events
        """
        events = self.events
        if tenant_id:
            events = [e for e in events if e.get('tenant_id') == tenant_id]
        if event_type:
            events = [e for e in events if e.get('event_type') == event_type]
        return events


class MockM33KeyManagement:
    """
    Mock Key & Trust Management (EPC-11) for receipt signing.

    Per EPC-13 PRD: Receipts are signed with Ed25519 via EPC-11.
    Note: Class name uses legacy M33 identifier for backward compatibility. Module is EPC-11 (Key & Trust Management).
    """

    def __init__(self):
        """Initialize mock key management."""
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            self.private_key = Ed25519PrivateKey.generate()
        except ImportError:
            logger.warning("cryptography library not available, using mock signing")
            self.private_key = None

    def sign(self, data: bytes) -> str:
        """
        Sign data with Ed25519 private key.

        Args:
            data: Data bytes to sign

        Returns:
            Hex-encoded Ed25519 signature
        """
        if not self.private_key:
            return "mock_signature_" + hashlib.sha256(data).hexdigest()[:32]

        signature = self.private_key.sign(data)
        return signature.hex()


class MockM21IAM:
    """
    Mock IAM Module (EPC-1) for access control.

    Per EPC-13 PRD: JWT verification for authentication and authorization.
    Note: Class name uses legacy M21 identifier for backward compatibility. Module is EPC-1 (Identity & Access Management).
    """

    def __init__(self):
        """Initialize mock IAM with in-memory token and role store."""
        self.valid_tokens: Dict[str, Dict[str, Any]] = {}
        self.revoked_tokens: set = set()
        self.user_roles: Dict[str, List[str]] = {}  # user_id -> [roles]

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

        if token in self.valid_tokens:
            return True, self.valid_tokens[token], None

        # Strict verification: require shared secret and signature validation
        secret = os.getenv("M35_JWT_SECRET")
        if not secret:
            return False, None, "JWT secret not configured"

        try:
            import jwt
            decoded = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                options={"require": ["sub", "tenant_id", "exp"]},
            )
            return True, decoded, None
        except ImportError:
            return False, None, "JWT library not available"
        except Exception as exc:
            return False, None, f"Token verification failed: {str(exc)}"

    def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """
        Check if user has permission for resource and action.

        Args:
            user_id: User identifier
            resource: Resource identifier
            action: Action (view, modify, approve, etc.)

        Returns:
            True if permission granted, False otherwise
        """
        roles = self.user_roles.get(user_id, [])
        # Mock permission check based on roles
        if "tenant_admin" in roles:
            return True
        if "financial_controller" in roles and resource in ["budget", "cost"]:
            return action in ["view", "modify", "approve"]
        if "system_architect" in roles and resource == "rate_limit":
            return action in ["view", "modify", "override"]
        return False

    def register_token(self, token: str, claims: Dict[str, Any]) -> None:
        """
        Register a valid token (for testing).

        Args:
            token: Token string
            claims: Token claims dictionary
        """
        self.valid_tokens[token] = claims

    def assign_role(self, user_id: str, role: str) -> None:
        """
        Assign role to user (for testing).

        Args:
            user_id: User identifier
            role: Role name
        """
        if user_id not in self.user_roles:
            self.user_roles[user_id] = []
        if role not in self.user_roles[user_id]:
            self.user_roles[user_id].append(role)

