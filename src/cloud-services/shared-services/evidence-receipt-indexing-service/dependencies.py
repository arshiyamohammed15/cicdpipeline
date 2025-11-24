"""
Dependency integrations for Evidence & Receipt Indexing Service (ERIS).

What: Mock and real implementations for IAM, Data Governance, Contracts & Schema Registry, KMS
Why: Allows ERIS development and testing before upstream services are available
Reads/Writes: Calls external services, stores data in memory for mocks
Risks: Mocks are NOT production ready; replace with real integrations before launch
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import httpx

logger = logging.getLogger(__name__)


# Sub-feature 3.1: Mock Dependencies

class MockM21IAM:
    """
    Mock Identity & Access Management (M21) module.

    Responsibilities:
        - Token verification
        - Access decision evaluation
        - Tenant context extraction
    """

    def __init__(self) -> None:
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.permissions: Dict[str, Dict[str, List[str]]] = {}

    def register_token(self, token: str, claims: Dict[str, Any]) -> None:
        """Register a token with claims."""
        self.tokens[token] = claims

    def register_permission(self, tenant_id: str, user_id: str, permission: str) -> None:
        """Grant a permission to a user for a tenant."""
        tenant_permissions = self.permissions.setdefault(tenant_id, {})
        user_permissions = tenant_permissions.setdefault(user_id, [])
        if permission not in user_permissions:
            user_permissions.append(permission)

    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Verify JWT token.

        Returns:
            Tuple of (is_valid, claims_dict, error_message)
        """
        if token in self.tokens:
            return True, self.tokens[token], None
        return False, None, "Token not found or invalid"

    def evaluate_access(self, subject: Dict[str, Any], action: str, resource: str) -> Tuple[bool, str]:
        """
        Evaluate access decision.

        Returns:
            Tuple of (allowed, reason)
        """
        tenant_id = subject.get("tenant_id")
        user_id = subject.get("sub")
        tenant_permissions = self.permissions.get(tenant_id, {})
        user_permissions = tenant_permissions.get(user_id, [])

        if action in user_permissions:
            return True, "Access granted"

        return False, "Access denied"


class MockM22DataGovernance:
    """
    Mock Data Governance & Privacy (M22) module.

    Responsibilities:
        - Retention policy lookup
        - Legal hold management
        - Payload content validation
    """

    def __init__(self) -> None:
        self.retention_policies: Dict[str, Dict[str, Any]] = {}
        self.legal_holds: Dict[str, List[str]] = {}

    def set_retention_policy(self, tenant_id: str, policy: Dict[str, Any]) -> None:
        """Set retention policy for tenant."""
        self.retention_policies[tenant_id] = policy

    def get_retention_policy(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get retention policy for tenant."""
        return self.retention_policies.get(tenant_id)

    def set_legal_hold(self, tenant_id: str, incident_id: str) -> None:
        """Set legal hold for tenant/incident."""
        if tenant_id not in self.legal_holds:
            self.legal_holds[tenant_id] = []
        if incident_id not in self.legal_holds[tenant_id]:
            self.legal_holds[tenant_id].append(incident_id)

    def get_legal_holds(self, tenant_id: str) -> List[str]:
        """Get legal holds for tenant."""
        return self.legal_holds.get(tenant_id, [])

    def validate_payload_content(self, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate payload content for metadata-only constraint.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Simple validation: check for common PII/secrets patterns
        payload_str = json.dumps(payload).lower()
        forbidden_patterns = ["password", "secret", "token", "api_key", "ssn", "credit_card"]
        for pattern in forbidden_patterns:
            if pattern in payload_str:
                return False, f"Forbidden content detected: {pattern}"
        return True, None


class MockM34ContractsSchemaRegistry:
    """
    Mock Contracts & Schema Registry (M34) module.

    Responsibilities:
        - Schema lookup by version
        - Receipt validation
    """

    def __init__(self) -> None:
        self.schemas: Dict[str, Dict[str, Any]] = {}

    def register_schema(self, schema_name: str, schema_version: str, schema: Dict[str, Any]) -> None:
        """Register a schema."""
        key = f"{schema_name}:{schema_version}"
        self.schemas[key] = schema

    def get_schema(self, schema_name: str, schema_version: str) -> Optional[Dict[str, Any]]:
        """Get schema by name and version."""
        key = f"{schema_name}:{schema_version}"
        return self.schemas.get(key)

    def validate_receipt(self, receipt: Dict[str, Any], schema_version: str) -> Tuple[bool, Optional[str]]:
        """
        Validate receipt against schema.

        Returns:
            Tuple of (is_valid, error_message)
        """
        schema = self.get_schema("receipt", schema_version)
        if not schema:
            return False, f"Schema not found: receipt:{schema_version}"

        # Simple validation: check required fields
        required_fields = ["receipt_id", "gate_id", "timestamp_utc", "decision", "actor", "signature"]
        for field in required_fields:
            if field not in receipt:
                return False, f"Missing required field: {field}"

        return True, None


class MockM33KMS:
    """
    Mock Key Management Service (M33) module.

    Responsibilities:
        - Key resolution by KID
        - Signature verification
    """

    def __init__(self) -> None:
        self.keys: Dict[str, Dict[str, Any]] = {}
        self.revoked_kids: List[str] = []

    def register_key(self, kid: str, key_data: Dict[str, Any]) -> None:
        """Register a key."""
        self.keys[kid] = key_data

    def revoke_key(self, kid: str) -> None:
        """Revoke a key."""
        if kid not in self.revoked_kids:
            self.revoked_kids.append(kid)

    def get_key(self, kid: str) -> Optional[Dict[str, Any]]:
        """Get key by KID."""
        if kid in self.revoked_kids:
            return None
        return self.keys.get(kid)

    def verify_signature(self, data: bytes, signature: str, kid: str) -> Tuple[bool, str]:
        """
        Verify signature.

        Returns:
            Tuple of (is_valid, status)
        """
        key = self.get_key(kid)
        if not key:
            return False, "kid_revoked"

        # Mock verification: always succeeds if key exists
        return True, "verified"


# Sub-feature 3.2: Dependency Integration Helpers

# Global mock instances (fallback)
_mock_iam = MockM21IAM()
_mock_data_governance = MockM22DataGovernance()
_mock_schema_registry = MockM34ContractsSchemaRegistry()
_mock_kms = MockM33KMS()

# Service URLs from environment
IAM_SERVICE_URL = os.getenv("IAM_SERVICE_URL")
DATA_GOVERNANCE_SERVICE_URL = os.getenv("DATA_GOVERNANCE_SERVICE_URL")
CONTRACTS_SCHEMA_REGISTRY_URL = os.getenv("CONTRACTS_SCHEMA_REGISTRY_URL")
KMS_SERVICE_URL = os.getenv("KMS_SERVICE_URL")


async def verify_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Verify token via IAM service or mock.

    Returns:
        Tuple of (is_valid, claims_dict, error_message)
        claims_dict includes: sub, scope, valid_until, tenant_id (derived from sub or attributes)
    """
    if IAM_SERVICE_URL:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{IAM_SERVICE_URL}/iam/v1/verify",
                    json={"token": token},
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    # IAM VerifyResponse: {sub, scope, valid_until}
                    # Extract tenant_id from sub (format: "tenant_id:user_id" or similar)
                    # or derive from sub field
                    sub = data.get("sub", "")
                    tenant_id = None
                    # Try to extract tenant_id from sub (common patterns: "tenant_id:user_id", "user_id@tenant_id")
                    if ":" in sub:
                        tenant_id = sub.split(":")[0]
                    elif "@" in sub:
                        parts = sub.split("@")
                        if len(parts) > 1:
                            tenant_id = parts[-1]
                    # If not found in sub, use sub as fallback (may need IAM context)
                    if not tenant_id:
                        tenant_id = sub
                    
                    # Build claims dict compatible with ERIS expectations
                    claims = {
                        "sub": sub,
                        "scope": data.get("scope", []),
                        "valid_until": data.get("valid_until"),
                        "tenant_id": tenant_id  # Derived from sub
                    }
                    return True, claims, None
                return False, None, f"IAM verification failed: {response.status_code}"
        except Exception as exc:
            logger.warning("IAM service unavailable, using mock: %s", exc)
            return _mock_iam.verify_token(token)
    return _mock_iam.verify_token(token)


async def evaluate_access(subject: Dict[str, Any], action: str, resource: str) -> Tuple[bool, str]:
    """
    Evaluate access decision via IAM service or mock.

    Args:
        subject: Subject dict with 'sub', 'roles', and optionally 'attributes'
        action: Action to perform
        resource: Resource to access

    Returns:
        Tuple of (allowed, reason)
    """
    if IAM_SERVICE_URL:
        try:
            async with httpx.AsyncClient() as client:
                # IAM DecisionRequest requires: {subject: Subject, action: str, resource: str, context?: DecisionContext, elevation?: ElevationRequest}
                # Subject model: {sub: str, roles: List[str], attributes?: Dict[str, Any]}
                decision_request = {
                    "subject": {
                        "sub": subject.get("sub", subject.get("user_id", "unknown")),
                        "roles": subject.get("roles", []),
                        "attributes": subject.get("attributes")
                    },
                    "action": action,
                    "resource": resource
                }
                response = await client.post(
                    f"{IAM_SERVICE_URL}/iam/v1/decision",
                    json=decision_request,
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    # IAM DecisionResponse: {decision: "ALLOW"|"DENY"|..., reason: str, expires_at?: datetime, receipt_id: str}
                    decision = data.get("decision", "DENY")
                    return decision == "ALLOW", data.get("reason", "Access decision")
                return False, f"IAM decision failed: {response.status_code}"
        except Exception as exc:
            logger.warning("IAM service unavailable, using mock: %s", exc)
            return _mock_iam.evaluate_access(subject, action, resource)
    return _mock_iam.evaluate_access(subject, action, resource)


async def check_rbac_permission(claims: Optional[Dict[str, Any]], action: str, tenant_id: Optional[str] = None, is_system_wide: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Check RBAC permission for ERIS operations per FR-6.
    
    Args:
        claims: IAM token claims dict with 'sub', 'scope', 'tenant_id', and optionally 'roles'
        action: Action to perform ('evidence:read', 'evidence:read:all', 'evidence:export', 'evidence:write')
        tenant_id: Tenant ID for tenant-scoped operations
        is_system_wide: Whether this is a system-wide multi-tenant query
        
    Returns:
        Tuple of (allowed, error_message)
    """
    if not claims:
        return False, "Missing IAM claims"
    
    sub = claims.get("sub", "unknown")
    scope = claims.get("scope", [])
    roles = claims.get("roles", [])
    claims_tenant_id = claims.get("tenant_id")
    
    # Extract roles from scope if not directly available
    # Scope may contain permissions like "evidence:read" or role names
    if not roles and scope:
        # Check if scope contains role names (common pattern: roles in scope)
        potential_roles = [s for s in scope if s.startswith("role:") or s in ["product_ops", "admin", "tenant_admin"]]
        if potential_roles:
            roles = [r.replace("role:", "") for r in potential_roles]
    
    # For system-wide queries, require product_ops or admin role
    if is_system_wide:
        if "product_ops" not in roles and "admin" not in roles:
            return False, "System-wide queries require product_ops or admin role"
        # Use evidence:read:all for system-wide access
        action = "evidence:read:all"
    
    # Build subject for access evaluation
    subject = {
        "sub": sub,
        "roles": roles,
        "tenant_id": tenant_id or claims_tenant_id,
        "attributes": claims.get("attributes", {})
    }
    
    # Build resource identifier
    if tenant_id:
        resource = f"evidence:tenant:{tenant_id}"
    else:
        resource = "evidence:*"
    
    # Evaluate access via IAM
    allowed, reason = await evaluate_access(subject, action, resource)
    
    if not allowed:
        return False, f"Access denied: {reason}"
    
    return True, None


async def get_retention_policy(tenant_id: str) -> Optional[Dict[str, Any]]:
    """
    Get retention policy via Data Governance service or mock.

    Uses POST /privacy/v1/retention/evaluate with RetentionEvaluationRequest.

    Returns:
        Retention policy dict with action, policy_id, legal_hold, regulatory_basis or None
    """
    if DATA_GOVERNANCE_SERVICE_URL:
        try:
            async with httpx.AsyncClient() as client:
                # Data Governance uses POST /privacy/v1/retention/evaluate
                # RetentionEvaluationRequest: {tenant_id: str, data_category: str, last_activity_months: int}
                response = await client.post(
                    f"{DATA_GOVERNANCE_SERVICE_URL}/privacy/v1/retention/evaluate",
                    json={
                        "tenant_id": tenant_id,
                        "data_category": "receipts",  # ERIS receipts category
                        "last_activity_months": 0  # Current evaluation
                    },
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    # RetentionEvaluationResponse: {action: str, policy_id?: str, legal_hold?: bool, regulatory_basis?: str}
                    return data
                return None
        except Exception as exc:
            logger.warning("Data Governance service unavailable, using mock: %s", exc)
            return _mock_data_governance.get_retention_policy(tenant_id)
    return _mock_data_governance.get_retention_policy(tenant_id)


async def get_legal_holds(tenant_id: str) -> List[str]:
    """
    Get legal holds via Data Governance service or mock.

    Note: Data Governance doesn't have a separate legal holds endpoint.
    Legal hold status is included in retention evaluation response.
    This function extracts legal hold information from retention policy.

    Returns:
        List of incident IDs under legal hold (empty list if no legal holds)
    """
    if DATA_GOVERNANCE_SERVICE_URL:
        try:
            # Legal hold status is part of retention evaluation response
            retention_policy = await get_retention_policy(tenant_id)
            if retention_policy and retention_policy.get("legal_hold"):
                # If legal_hold is True, return a placeholder incident ID
                # In production, this should be extracted from retention policy details
                return ["legal-hold-active"]  # Placeholder - actual implementation should extract incident IDs
            return []
        except Exception as exc:
            logger.warning("Data Governance service unavailable, using mock: %s", exc)
            return _mock_data_governance.get_legal_holds(tenant_id)
    return _mock_data_governance.get_legal_holds(tenant_id)


async def validate_payload_content(payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate payload content via Data Governance service or mock.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if DATA_GOVERNANCE_SERVICE_URL:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{DATA_GOVERNANCE_SERVICE_URL}/privacy/v1/classification",
                    json={"data_content": payload},
                    timeout=5.0
                )
                if response.status_code == 200:
                    return True, None
                return False, "Payload validation failed"
        except Exception as exc:
            logger.warning("Data Governance service unavailable, using mock: %s", exc)
            return _mock_data_governance.validate_payload_content(payload)
    return _mock_data_governance.validate_payload_content(payload)


async def get_schema(schema_name: str, schema_version: str) -> Optional[Dict[str, Any]]:
    """
    Get schema via Contracts & Schema Registry service or mock.

    Contracts & Schema Registry uses schema_id (UUID) not schema_name:version.
    This function first lists schemas to find schema_id by name, then retrieves schema.

    Returns:
        Schema dict or None
    """
    if CONTRACTS_SCHEMA_REGISTRY_URL:
        try:
            async with httpx.AsyncClient() as client:
                # First, list schemas to find schema_id by name
                response = await client.get(
                    f"{CONTRACTS_SCHEMA_REGISTRY_URL}/registry/v1/schemas",
                    params={"namespace": schema_name, "status": "released"},
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    schemas = data.get("schemas", [])
                    # Find schema matching name and version
                    schema_id = None
                    for schema in schemas:
                        if schema.get("name") == schema_name:
                            # Check if version matches (if version specified)
                            if schema_version:
                                versions = schema.get("versions", [])
                                if any(v.get("version") == schema_version for v in versions):
                                    schema_id = schema.get("schema_id")
                                    break
                            else:
                                # Use latest version
                                schema_id = schema.get("schema_id")
                                break
                    
                    if schema_id:
                        # Get schema details by schema_id
                        response = await client.get(
                            f"{CONTRACTS_SCHEMA_REGISTRY_URL}/registry/v1/schemas/{schema_id}",
                            params={"version": schema_version} if schema_version else {},
                            timeout=5.0
                        )
                        if response.status_code == 200:
                            return response.json()
                return None
        except Exception as exc:
            logger.warning("Contracts & Schema Registry unavailable, using mock: %s", exc)
            return _mock_schema_registry.get_schema(schema_name, schema_version)
    return _mock_schema_registry.get_schema(schema_name, schema_version)


async def validate_receipt_schema(receipt: Dict[str, Any], schema_version: str) -> Tuple[bool, Optional[str]]:
    """
    Validate receipt via Contracts & Schema Registry service or mock.

    Contracts & Schema Registry ValidateDataRequest requires schema_id (UUID).
    This function first gets schema_id by looking up schema, then validates.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if CONTRACTS_SCHEMA_REGISTRY_URL:
        try:
            # First get schema to obtain schema_id
            schema = await get_schema("receipt", schema_version)
            if not schema:
                return False, f"Schema not found: receipt:{schema_version}"
            
            schema_id = schema.get("schema_id")
            if not schema_id:
                return False, "Schema ID not found in schema metadata"
            
            async with httpx.AsyncClient() as client:
                # ValidateDataRequest: {schema_id: str (UUID), version?: str, data: Dict[str, Any]}
                response = await client.post(
                    f"{CONTRACTS_SCHEMA_REGISTRY_URL}/registry/v1/validate",
                    json={
                        "schema_id": schema_id,
                        "version": schema_version,
                        "data": receipt
                    },
                    timeout=5.0
                )
                if response.status_code == 200:
                    result = response.json()
                    # ValidationResult: {valid: bool, errors?: List[str]}
                    if result.get("valid", False):
                        return True, None
                    else:
                        errors = result.get("errors", [])
                        return False, "; ".join(errors) if errors else "Validation failed"
                data = response.json()
                error_detail = data.get("error", {})
                return False, error_detail.get("message", "Validation failed") if isinstance(error_detail, dict) else str(error_detail)
        except Exception as exc:
            logger.warning("Contracts & Schema Registry unavailable, using mock: %s", exc)
            return _mock_schema_registry.validate_receipt(receipt, schema_version)
    return _mock_schema_registry.validate_receipt(receipt, schema_version)


async def get_key(kid: str, tenant_id: str, environment: str = "dev", plane: str = "shared") -> Optional[Dict[str, Any]]:
    """
    Get key metadata via KMS service or mock.

    Note: KMS doesn't expose a GET endpoint for key retrieval.
    Key metadata is retrieved during signature verification or via internal service methods.
    This function uses the mock implementation as KMS key retrieval requires internal access.

    Args:
        kid: Key identifier
        tenant_id: Tenant identifier
        environment: Environment (dev, staging, prod)
        plane: Plane (laptop, tenant, product, shared)

    Returns:
        Key dict or None
    """
    # KMS doesn't expose GET /keys/{kid} endpoint
    # Key metadata is typically retrieved during verification or via internal service
    # For now, use mock implementation
    # In production, this should use internal KMS service method or trust store
    if KMS_SERVICE_URL:
        # KMS key retrieval requires internal service access
        # For now, log and use mock
        logger.debug("KMS key retrieval via HTTP not available, using mock for kid: %s", kid)
        return _mock_kms.get_key(kid)
    return _mock_kms.get_key(kid)


async def verify_signature(data: bytes, signature: str, kid: str, tenant_id: str, environment: str = "dev", plane: str = "shared") -> Tuple[bool, str]:
    """
    Verify signature via KMS service or mock.

    KMS VerifySignatureRequest requires: tenant_id, environment, plane, key_id, data (base64), signature (base64), algorithm (optional).

    Args:
        data: Data bytes that were signed
        signature: Base64-encoded signature
        kid: Key identifier
        tenant_id: Tenant identifier
        environment: Environment (dev, staging, prod)
        plane: Plane (laptop, tenant, product, shared)

    Returns:
        Tuple of (is_valid, status)
    """
    if KMS_SERVICE_URL:
        try:
            import base64
            async with httpx.AsyncClient() as client:
                # KMS VerifySignatureRequest: {tenant_id, environment, plane, key_id, data (base64), signature (base64), algorithm?}
                response = await client.post(
                    f"{KMS_SERVICE_URL}/kms/v1/verify",
                    json={
                        "tenant_id": tenant_id,
                        "environment": environment,
                        "plane": plane,
                        "key_id": kid,
                        "data": base64.b64encode(data).decode("utf-8"),
                        "signature": signature,  # Assume already base64-encoded
                        "algorithm": None  # Let KMS determine from key metadata
                    },
                    timeout=5.0
                )
                if response.status_code == 200:
                    result = response.json()
                    # VerifySignatureResponse: {valid: bool, key_id: str, algorithm: str, status: str}
                    return result.get("valid", False), result.get("status", "unknown")
                error_data = response.json()
                error_detail = error_data.get("error", {})
                error_msg = error_detail.get("message", "Verification failed") if isinstance(error_detail, dict) else str(error_detail)
                return False, f"verification_failed: {error_msg}"
        except Exception as exc:
            logger.warning("KMS service unavailable, using mock: %s", exc)
            return _mock_kms.verify_signature(data, signature, kid)
    return _mock_kms.verify_signature(data, signature, kid)


def extract_tenant_context(headers: Dict[str, str]) -> Optional[Dict[str, str]]:
    """
    Extract tenant context from HTTP headers.

    Expected headers:
        - X-Tenant-ID
        - X-User-ID
        - Authorization (JWT token)
    """
    tenant_id = headers.get("X-Tenant-ID")
    if not tenant_id:
        return None
    return {
        "tenant_id": tenant_id,
        "user_id": headers.get("X-User-ID", "unknown-user"),
        "authorization": headers.get("Authorization", ""),
    }
