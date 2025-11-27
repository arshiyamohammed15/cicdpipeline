"""
Dependency clients for UBI Module (EPC-9).

What: Mock clients for IAM, ERIS, Data Governance for development/testing
Why: Enable development without full platform dependencies
Reads/Writes: Mock service calls
Contracts: IAM, ERIS, Data Governance API contracts
Risks: Mock implementations may not match production behavior exactly
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class MockM21IAM:
    """
    Mock IAM Module (EPC-1) for token verification.

    Per UBI PRD Section 11: Token verification via POST /iam/v1/verify
    """

    def __init__(self):
        """Initialize mock IAM with in-memory token store."""
        self.valid_tokens: Dict[str, Dict[str, Any]] = {}
        self.revoked_tokens: set = set()

    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
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
            required_claims = ["sub", "tenant_id"]
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

    def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """
        Check if user has permission for resource/action.

        Args:
            user_id: User identifier
            resource: Resource identifier
            action: Action (read, write, etc.)

        Returns:
            True if permission granted, False otherwise
        """
        # Mock permission check - in production would query IAM policies
        return True


class MockM7ERIS:
    """
    Mock ERIS (PM-7) for receipt emission.

    Per UBI PRD FR-13: Receipt emission via POST /v1/evidence/receipts
    """

    def __init__(self):
        """Initialize mock ERIS with in-memory receipt store."""
        self.receipts: Dict[str, Dict[str, Any]] = {}
        self.available = True  # Simulate ERIS availability

    async def emit_receipt(self, receipt: Dict[str, Any]) -> str:
        """
        Emit receipt to ERIS.

        Args:
            receipt: Receipt dictionary following canonical schema

        Returns:
            Receipt ID

        Raises:
            Exception: If ERIS is unavailable
        """
        if not self.available:
            raise Exception("ERIS unavailable")

        receipt_id = receipt.get("receipt_id", "")
        self.receipts[receipt_id] = receipt
        logger.debug(f"Mock ERIS: Receipt emitted: {receipt_id}")
        return receipt_id

    def get_receipt(self, receipt_id: str) -> Optional[Dict[str, Any]]:
        """
        Get receipt by ID.

        Args:
            receipt_id: Receipt identifier

        Returns:
            Receipt dictionary or None if not found
        """
        return self.receipts.get(receipt_id)

    def set_available(self, available: bool) -> None:
        """
        Set ERIS availability (for testing).

        Args:
            available: Whether ERIS is available
        """
        self.available = available


class MockM22DataGovernance:
    """
    Mock Data Governance & Privacy (EPC-2) for retention policies and data deletion.

    Per UBI PRD FR-8: Retention policy query and data deletion callbacks
    """

    def __init__(self):
        """Initialize mock Data Governance with in-memory policy store."""
        self.retention_policies: Dict[str, Dict[str, Any]] = {}

    async def get_retention_policies(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Get retention policies for tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of retention policy dictionaries
        """
        policies = self.retention_policies.get(tenant_id, [])
        return policies if isinstance(policies, list) else [policies]

    async def delete_data(self, tenant_id: str, time_range: Dict[str, str]) -> bool:
        """
        Delete data for tenant within time range.

        Args:
            tenant_id: Tenant identifier
            time_range: Time range dictionary with 'from' and 'to' ISO 8601 timestamps

        Returns:
            True if deletion successful
        """
        logger.info(f"Mock Data Governance: Delete data for tenant {tenant_id}, range {time_range}")
        return True

    async def classify_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify data for privacy.

        Args:
            data: Data dictionary to classify

        Returns:
            Classification result with privacy tags
        """
        return {
            "classification_level": "internal",
            "privacy_tags": [],
            "confidence": 0.9
        }

    def set_retention_policy(self, tenant_id: str, policy: Dict[str, Any]) -> None:
        """
        Set retention policy for tenant (for testing).

        Args:
            tenant_id: Tenant identifier
            policy: Retention policy dictionary
        """
        if tenant_id not in self.retention_policies:
            self.retention_policies[tenant_id] = []
        self.retention_policies[tenant_id].append(policy)

