"""
Mock dependency implementations for Data Governance & Privacy Module (M22).

What: In-memory mocks for IAM (M21), Evidence Ledger (M27), Data Plane (M29),
      Key Management (M33), and Policy Management (M23)
Why: Allows M22 development and testing before upstream services are available
Reads/Writes: Stores data in memory only; no external side effects
Risks: Mocks are NOT production ready; replace with real integrations before launch
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


class MockM21IAM:
    """
    Mock Identity & Access Management (EPC-1) module.
    Note: Class name uses legacy M21 identifier for backward compatibility.

    Responsibilities:
        - Permission checks for privacy operations
        - Tenant context extraction from headers
        - Break-glass style overrides for emergency actions
    """

    def __init__(self) -> None:
        self.permissions: Dict[str, Dict[str, List[str]]] = {}
        self.override_tokens: Dict[str, Dict[str, Any]] = {}

    def register_permission(self, tenant_id: str, user_id: str, permission: str) -> None:
        """Grant a permission to a user for a tenant."""
        tenant_permissions = self.permissions.setdefault(tenant_id, {})
        user_permissions = tenant_permissions.setdefault(user_id, [])
        if permission not in user_permissions:
            user_permissions.append(permission)

    def register_override_token(self, token: str, metadata: Dict[str, Any]) -> None:
        """Register a temporary override token (e.g., break-glass approval)."""
        self.override_tokens[token] = metadata

    def check_permission(
        self,
        tenant_id: str,
        user_id: str,
        permission: str,
        resource: Optional[str] = None,
        override_token: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Evaluate permission for a given user.

        Returns:
            Tuple of (allowed, reason)
        """
        tenant_permissions = self.permissions.get(tenant_id, {})
        user_permissions = tenant_permissions.get(user_id, [])

        if permission in user_permissions:
            return True, "Permission granted"

        if override_token:
            metadata = self.override_tokens.get(override_token)
            if metadata and metadata.get("expires_at", datetime.utcnow()) > datetime.utcnow():
                return True, "Override token accepted"

        logger.debug(
            "Permission denied | tenant=%s user=%s permission=%s resource=%s",
            tenant_id,
            user_id,
            permission,
            resource,
        )
        return False, "Permission denied"

    @staticmethod
    def extract_tenant_context(headers: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Extract tenant context from HTTP headers.

        Expected headers:
            - X-Tenant-ID
            - X-User-ID
            - X-Module-ID (optional)
        """
        tenant_id = headers.get("X-Tenant-ID")
        if not tenant_id:
            return None
        return {
            "tenant_id": tenant_id,
            "user_id": headers.get("X-User-ID", "unknown-user"),
            "module_id": headers.get("X-Module-ID", "M22"),
        }


class MockM27EvidenceLedger:
    """
    Mock Evidence & Audit Ledger (M27).

    Provides Ed25519 signing when cryptography library is available, with in-memory storage.
    """

    def __init__(self) -> None:
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from cryptography.hazmat.primitives import serialization

            self.private_key = Ed25519PrivateKey.generate()
            self.public_key = self.private_key.public_key()
            self.serialization = serialization
        except ImportError:  # pragma: no cover - optional dependency
            logger.warning("cryptography not available; using deterministic mock signatures")
            self.private_key = None
            self.public_key = None
            self.serialization = None
        self.receipts: Dict[str, Dict[str, Any]] = {}

    def sign_receipt(self, payload: Dict[str, Any]) -> str:
        """Return signature for payload."""
        serialized = json.dumps(payload, sort_keys=True, default=str)
        if not self.private_key:
            return "mock_signature_" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        signature = self.private_key.sign(serialized.encode("utf-8"))
        return signature.hex()

    def store_receipt(self, receipt_id: str, payload: Dict[str, Any]) -> None:
        """Persist receipt data (in-memory)."""
        self.receipts[receipt_id] = payload

    def get_receipts_by_tenant(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Return all receipts for a given tenant."""
        return [
            receipt
            for receipt in self.receipts.values()
            if receipt.get("tenant_id") == tenant_id
        ]


class MockM29DataPlane:
    """
    Mock Data & Memory Plane (M29).

    Stores classification results, consent records, lineage entries, retention policies, and rights requests.
    Provides lightweight querying utilities required by services.
    """

    def __init__(self) -> None:
        self.classifications: Dict[str, Dict[str, Any]] = {}
        self.consents: Dict[str, Dict[str, Any]] = {}
        self.lineage_entries: Dict[str, Dict[str, Any]] = {}
        self.retention_policies: Dict[str, Dict[str, Any]] = {}
        self.rights_requests: Dict[str, Dict[str, Any]] = {}

    # Classification storage -------------------------------------------------
    def store_classification(self, record: Dict[str, Any]) -> str:
        data_id = record.get("data_id") or str(uuid4())
        record["data_id"] = data_id
        record["classified_at"] = record.get("classified_at") or datetime.utcnow().isoformat()
        self.classifications[data_id] = record
        return data_id

    def get_classification(self, data_id: str) -> Optional[Dict[str, Any]]:
        return self.classifications.get(data_id)

    # Consent storage -------------------------------------------------------
    def store_consent(self, record: Dict[str, Any]) -> str:
        consent_id = record.get("consent_id") or str(uuid4())
        record["consent_id"] = consent_id
        self.consents[consent_id] = record
        return consent_id

    def get_consent(self, consent_id: str) -> Optional[Dict[str, Any]]:
        return self.consents.get(consent_id)

    def list_consents(self, tenant_id: str, data_subject_id: str) -> List[Dict[str, Any]]:
        return [
            record
            for record in self.consents.values()
            if record.get("tenant_id") == tenant_id
            and record.get("data_subject_id") == data_subject_id
        ]

    # Lineage storage -------------------------------------------------------
    def store_lineage(self, record: Dict[str, Any]) -> str:
        lineage_id = record.get("lineage_id") or str(uuid4())
        record["lineage_id"] = lineage_id
        self.lineage_entries[lineage_id] = record
        return lineage_id

    def query_lineage(self, tenant_id: str, data_id: str) -> List[Dict[str, Any]]:
        return [
            entry
            for entry in self.lineage_entries.values()
            if entry.get("tenant_id") == tenant_id
            and (entry.get("source_data_id") == data_id or entry.get("target_data_id") == data_id)
        ]

    # Retention policy storage ----------------------------------------------
    def store_retention_policy(self, policy: Dict[str, Any]) -> str:
        policy_id = policy.get("policy_id") or str(uuid4())
        policy["policy_id"] = policy_id
        self.retention_policies[policy_id] = policy
        return policy_id

    def get_retention_policy(self, tenant_id: str, data_category: str) -> Optional[Dict[str, Any]]:
        for policy in self.retention_policies.values():
            if policy.get("tenant_id") == tenant_id and policy.get("data_category") == data_category:
                return policy
        return None

    # Rights requests -------------------------------------------------------
    def store_rights_request(self, request: Dict[str, Any]) -> str:
        request_id = request.get("request_id") or str(uuid4())
        request["request_id"] = request_id
        request["status"] = request.get("status", "pending")
        request["submitted_at"] = request.get("submitted_at") or datetime.utcnow().isoformat()
        self.rights_requests[request_id] = request
        return request_id

    def update_rights_request(self, request_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = self.rights_requests.get(request_id)
        if not existing:
            return None
        existing.update(updates)
        return existing


class MockM33KeyManagement:
    """
    Mock Key Management Service (EPC-11).
    Note: Class name uses legacy M33 identifier for backward compatibility.

    Provides deterministic encryption/decryption/tokenization using symmetric secrets.
    """

    def __init__(self) -> None:
        self.secret = os.environ.get("M33_MOCK_SECRET", "zero-ui-data-privacy")

    def encrypt(self, plaintext: str) -> str:
        """Return base64 encoded ciphertext (mock)."""
        pad = hashlib.sha256(self.secret.encode("utf-8")).digest()
        xor_bytes = bytes([b ^ pad[i % len(pad)] for i, b in enumerate(plaintext.encode("utf-8"))])
        return base64.b64encode(xor_bytes).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """Return decrypted plaintext (mock)."""
        pad = hashlib.sha256(self.secret.encode("utf-8")).digest()
        data = base64.b64decode(ciphertext.encode("utf-8"))
        plain_bytes = bytes([b ^ pad[i % len(pad)] for i, b in enumerate(data)])
        return plain_bytes.decode("utf-8")

    @staticmethod
    def hash_payload(payload: Dict[str, Any]) -> str:
        """Return SHA-256 hash of payload."""
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class MockM23PolicyManagement:
    """
    Mock Policy Management Module (M23).

    Evaluates privacy policies using simple rule expressions.
    """

    def __init__(self) -> None:
        self.policies: Dict[str, Dict[str, Any]] = {}

    def register_policy(self, policy_id: str, policy: Dict[str, Any]) -> None:
        self.policies[policy_id] = policy

    def evaluate(
        self,
        policy_id: str,
        context: Dict[str, Any],
        data_classification: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate a policy and return outcome.

        Returns:
            {
                "allowed": bool,
                "violations": [str],
                "evidence": {...}
            }
        """
        policy = self.policies.get(policy_id, {})
        violations: List[str] = []

        required_level = policy.get("min_classification_level")
        if required_level and data_classification:
            if data_classification.get("classification_level") not in required_level:
                violations.append("classification_level_not_allowed")

        required_consent = policy.get("requires_consent")
        if required_consent and not context.get("consent_granted"):
            violations.append("consent_missing")

        allowed = len(violations) == 0
        return {
            "allowed": allowed,
            "violations": violations,
            "evidence": {
                "evaluated_at": datetime.utcnow().isoformat(),
                "policy": policy_id,
                "context_snapshot": context,
            },
        }
