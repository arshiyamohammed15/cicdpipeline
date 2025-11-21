"""
Mock dependencies for SIN service (M21, M32, M35, M29, M34, API Gateway).

What: Mock implementations of IAM (M21), Trust (M32), Budgeting & Rate-Limiting (M35),
      Data Governance (M29), Contracts Schema Registry (M34), and API Gateway
Why: Enables SIN implementation before dependencies are available, will be replaced with real implementations
Reads/Writes: Mock storage (in-memory), mock signing (Ed25519), mock event publishing
Contracts: Interface contracts for M21, M32, M35, M29, M34, API Gateway integration
Risks: Mock implementations not production-ready, must be replaced before production deployment
"""

import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class MockM21IAM:
    """
    Mock IAM (M21) for authentication and authorization.

    Per PRD: All ingestion endpoints require valid tenant/producer credentials.
    """

    def __init__(self):
        """Initialize mock IAM with in-memory storage."""
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.permissions: Dict[str, Dict[str, List[str]]] = {}
        self.tenants: Dict[str, Dict[str, Any]] = {}

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify IAM token and return claims.

        Args:
            token: IAM token

        Returns:
            Token claims dictionary or None if invalid
        """
        if token in self.tokens:
            claims = self.tokens[token]
            # Check expiration
            if claims.get('expires_at') and datetime.utcnow() > claims['expires_at']:
                return None
            return claims
        return None

    def check_permission(self, tenant_id: str, producer_id: str, action: str, resource: str) -> bool:
        """
        Check if producer has permission for action on resource.

        Args:
            tenant_id: Tenant ID
            producer_id: Producer ID
            action: Action (e.g., 'ingest', 'register')
            resource: Resource (e.g., 'signal', 'producer')

        Returns:
            True if permitted, False otherwise
        """
        key = f"{tenant_id}:{producer_id}"
        if key in self.permissions:
            resource_perms = self.permissions[key].get(resource, [])
            return action in resource_perms
        # Default: allow if token was valid
        return True

    def register_token(self, token: str, claims: Dict[str, Any], expires_in_seconds: int = 3600):
        """Register a token for testing."""
        claims['expires_at'] = datetime.utcnow() + timedelta(seconds=expires_in_seconds)
        self.tokens[token] = claims

    def register_permissions(self, tenant_id: str, producer_id: str, permissions: Dict[str, List[str]]):
        """Register permissions for testing."""
        key = f"{tenant_id}:{producer_id}"
        self.permissions[key] = permissions


class MockM32Trust:
    """
    Mock Trust (M32) for DecisionReceipt emission.

    Per PRD F8: SIN SHALL emit DecisionReceipts for governance violations and DLQ threshold crossings.
    """

    def __init__(self):
        """Initialize mock trust with in-memory storage."""
        self.receipts: Dict[str, Dict[str, Any]] = {}
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

    def emit_receipt(self, receipt_data: Dict[str, Any]) -> str:
        """
        Emit DecisionReceipt for governance event.

        Args:
            receipt_data: Receipt data dictionary

        Returns:
            Receipt ID
        """
        receipt_id = f"receipt_{uuid.uuid4().hex[:16]}"
        receipt_data['receipt_id'] = receipt_id
        receipt_data['timestamp'] = datetime.utcnow().isoformat()

        # Sign receipt
        if self.private_key:
            receipt_json = json.dumps(receipt_data, sort_keys=True, default=str)
            receipt_bytes = receipt_json.encode('utf-8')
            signature = self.private_key.sign(receipt_bytes)
            receipt_data['signature'] = signature.hex()
        else:
            receipt_data['signature'] = "mock_signature_" + hashlib.sha256(
                json.dumps(receipt_data, sort_keys=True, default=str).encode()
            ).hexdigest()[:32]

        self.receipts[receipt_id] = receipt_data
        return receipt_id

    def get_receipt(self, receipt_id: str) -> Optional[Dict[str, Any]]:
        """Get receipt by ID."""
        return self.receipts.get(receipt_id)


class MockM35Budgeting:
    """
    Mock Budgeting & Rate-Limiting (M35) for quota enforcement.

    Per PRD F2.1: max_rate and quotas SHALL be sourced from Budgeting & Rate-Limiting configuration.
    """

    def __init__(self):
        """Initialize mock budgeting with in-memory storage."""
        self.quotas: Dict[str, Dict[str, Any]] = {}
        self.usage: Dict[str, Dict[str, Any]] = {}

    def check_quota(self, tenant_id: str, producer_id: str, signal_type: str) -> tuple[bool, Optional[str]]:
        """
        Check if producer has quota remaining.

        Args:
            tenant_id: Tenant ID
            producer_id: Producer ID
            signal_type: Signal type

        Returns:
            (allowed, error_message) tuple
        """
        key = f"{tenant_id}:{producer_id}"
        if key not in self.quotas:
            return True, None  # No quota limit

        quota = self.quotas[key]
        max_rate = quota.get('max_rate_per_minute')
        if max_rate is None:
            return True, None

        # Check current usage (simplified: per-minute window)
        now = datetime.utcnow()
        minute_key = f"{key}:{now.strftime('%Y%m%d%H%M')}"
        current_usage = self.usage.get(minute_key, {}).get('count', 0)

        if current_usage >= max_rate:
            return False, f"Rate limit exceeded: {current_usage}/{max_rate} per minute"

        # Increment usage
        if minute_key not in self.usage:
            self.usage[minute_key] = {'count': 0, 'timestamp': now}
        self.usage[minute_key]['count'] += 1

        return True, None

    def set_quota(self, tenant_id: str, producer_id: str, quota: Dict[str, Any]):
        """Set quota for testing."""
        key = f"{tenant_id}:{producer_id}"
        self.quotas[key] = quota


class MockM29DataGovernance:
    """
    Mock Data Governance (M29) for privacy rules and redaction.

    Per PRD F10: Privacy rules, redaction policies, classification.
    """

    def __init__(self):
        """Initialize mock data governance with in-memory rules."""
        self.rules: Dict[str, Dict[str, Any]] = {}
        self.disallowed_fields: Dict[str, List[str]] = {}
        self.redaction_rules: Dict[str, Dict[str, str]] = {}

    def get_disallowed_fields(self, tenant_id: str, producer_id: str, signal_type: str) -> List[str]:
        """
        Get disallowed fields for producer/signal type.

        Args:
            tenant_id: Tenant ID
            producer_id: Producer ID
            signal_type: Signal type

        Returns:
            List of disallowed field names
        """
        key = f"{tenant_id}:{producer_id}:{signal_type}"
        return self.disallowed_fields.get(key, [])

    def get_redaction_rules(self, tenant_id: str, producer_id: str, signal_type: str) -> Dict[str, str]:
        """
        Get redaction rules for producer/signal type.

        Args:
            tenant_id: Tenant ID
            producer_id: Producer ID
            signal_type: Signal type

        Returns:
            Dictionary of field -> redaction action
        """
        key = f"{tenant_id}:{producer_id}:{signal_type}"
        return self.redaction_rules.get(key, {})

    def get_classification(self, tenant_id: str, signal_type: str) -> Optional[str]:
        """
        Get classification for signal type.

        Args:
            tenant_id: Tenant ID
            signal_type: Signal type

        Returns:
            Classification string or None
        """
        key = f"{tenant_id}:{signal_type}"
        rule = self.rules.get(key, {})
        return rule.get('classification')

    def set_disallowed_fields(self, tenant_id: str, producer_id: str, signal_type: str, fields: List[str]):
        """Set disallowed fields for testing."""
        key = f"{tenant_id}:{producer_id}:{signal_type}"
        self.disallowed_fields[key] = fields

    def set_redaction_rules(self, tenant_id: str, producer_id: str, signal_type: str, rules: Dict[str, str]):
        """Set redaction rules for testing."""
        key = f"{tenant_id}:{producer_id}:{signal_type}"
        self.redaction_rules[key] = rules


class MockM34SchemaRegistry:
    """
    Mock Contracts Schema Registry (M34) for schema storage and retrieval.

    Per PRD F2.2: SignalEnvelope and data contracts SHALL be stored in shared schema registry.
    """

    def __init__(self):
        """Initialize mock schema registry with in-memory storage."""
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.contracts: Dict[str, Dict[str, Any]] = {}

    def get_schema(self, schema_id: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get schema by ID and optional version.

        Args:
            schema_id: Schema ID
            version: Schema version (optional, latest if not specified)

        Returns:
            Schema definition or None
        """
        if version:
            key = f"{schema_id}:{version}"
        else:
            # Get latest version
            matching = [k for k in self.schemas.keys() if k.startswith(f"{schema_id}:")]
            if not matching:
                return None
            key = sorted(matching)[-1]  # Latest version

        return self.schemas.get(key)

    def register_schema(self, schema_id: str, version: str, schema_def: Dict[str, Any]) -> None:
        """
        Register schema in registry.

        Args:
            schema_id: Schema ID
            version: Schema version
            schema_def: Schema definition
        """
        key = f"{schema_id}:{version}"
        self.schemas[key] = {
            'schema_id': schema_id,
            'version': version,
            'definition': schema_def,
            'registered_at': datetime.utcnow().isoformat()
        }

    def get_contract(self, signal_type: str, version: str) -> Optional[Dict[str, Any]]:
        """
        Get data contract for signal type and version.

        Args:
            signal_type: Signal type
            version: Contract version

        Returns:
            Contract definition or None
        """
        key = f"{signal_type}:{version}"
        return self.contracts.get(key)

    def register_contract(self, signal_type: str, version: str, contract_def: Dict[str, Any]) -> None:
        """
        Register data contract in registry.

        Args:
            signal_type: Signal type
            version: Contract version
            contract_def: Contract definition
        """
        key = f"{signal_type}:{version}"
        self.contracts[key] = {
            'signal_type': signal_type,
            'version': version,
            'definition': contract_def,
            'registered_at': datetime.utcnow().isoformat()
        }

    def list_contract_versions(self, signal_type: str) -> List[str]:
        """
        List all registered contract versions for signal type.

        Args:
            signal_type: Signal type

        Returns:
            List of version strings
        """
        matching = [k for k in self.contracts.keys() if k.startswith(f"{signal_type}:")]
        versions = [k.split(':', 1)[1] for k in matching]
        return sorted(versions)


class MockAPIGateway:
    """
    Mock API Gateway & Webhooks for webhook ingestion.

    Per PRD F3.3: Gateway translates external payloads into preliminary SignalEnvelopes.
    """

    def __init__(self):
        """Initialize mock API gateway."""
        self.webhook_mappings: Dict[str, Dict[str, Any]] = {}
        self.webhook_events: List[Dict[str, Any]] = []

    def translate_webhook(self, webhook_id: str, external_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Translate external webhook payload into preliminary SignalEnvelope.

        Args:
            webhook_id: Webhook integration ID
            external_payload: External webhook payload

        Returns:
            Preliminary SignalEnvelope dictionary or None
        """
        if webhook_id not in self.webhook_mappings:
            return None

        mapping = self.webhook_mappings[webhook_id]
        tenant_id = mapping.get('tenant_id')
        producer_id = mapping.get('producer_id')

        # Create preliminary envelope (SIN will validate and transform)
        preliminary = {
            'tenant_id': tenant_id,
            'producer_id': producer_id,
            'external_payload': external_payload,
            'webhook_id': webhook_id,
            'received_at': datetime.utcnow().isoformat()
        }

        self.webhook_events.append(preliminary)
        return preliminary

    def register_webhook_mapping(self, webhook_id: str, tenant_id: str, producer_id: str, config: Dict[str, Any]):
        """Register webhook mapping for testing."""
        self.webhook_mappings[webhook_id] = {
            'tenant_id': tenant_id,
            'producer_id': producer_id,
            'config': config
        }

