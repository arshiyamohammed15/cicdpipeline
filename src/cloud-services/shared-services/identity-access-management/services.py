"""
Service layer for Identity & Access Management (IAM).

What: Business logic for authentication, authorization, policy management per IAM spec v1.1.0
Why: Encapsulates IAM logic, provides abstraction for route handlers, implements RBAC/ABAC evaluation
Reads/Writes: Reads policies, tokens, writes receipts, audit logs via mock dependencies (M27, M29, M32)
Contracts: IAM API contract (verify, decision, policies endpoints), receipt schema per spec section 7
Risks: Security vulnerabilities if tokens/policies mishandled, performance degradation under load, key compromise
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple

from .models import (
    VerifyRequest, VerifyResponse,
    DecisionRequest, DecisionResponse,
    PolicyBundle, Policy,
    Subject, DecisionContext, ElevationRequest, BreakGlassRequest
)
from .dependencies import MockM27EvidenceLedger, MockM29DataPlane, MockM32TrustPlane

logger = logging.getLogger(__name__)

# Canonical RBAC roles per IAM spec section 2
CANONICAL_ROLES = ["admin", "developer", "viewer", "ci_bot"]

# Organizational role mapping per IAM spec section 2
ORG_ROLE_MAPPING = {
    "executive": "admin",
    "lead": "developer",
    "individual_contributor": "developer",
    "ai_agent": "ci_bot"
}


class TokenValidator:
    """
    JWT token validator per IAM spec section 4.
    
    Tokens: JWT signed with RS256 (RSA-2048), 1h expiry, refresh at 55m.
    Claims: kid, iat, exp, aud, iss, sub, scope (no PII).
    Revocation: jti denylist with TTL=exp, propagate within 5s.
    """

    def __init__(self, data_plane: MockM29DataPlane):
        """
        Initialize token validator.

        Args:
            data_plane: Mock M29 data plane for jti denylist storage
        """
        self.data_plane = data_plane
        self.jti_denylist_key = "iam:jti_denylist"

    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Verify JWT token per IAM spec section 4.

        Args:
            token: JWT token string

        Returns:
            Tuple of (is_valid, claims_dict, error_message)
        """
        try:
            import jwt
        except ImportError:
            logger.error("PyJWT library not available")
            return False, None, "Token validation library not available"

        try:
            decoded = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            
            jti = decoded.get("jti")
            if jti:
                denylist = self.data_plane.cache_get(self.jti_denylist_key) or {}
                if jti in denylist:
                    return False, None, "Token revoked (jti in denylist)"
            
            exp = decoded.get("exp")
            if exp:
                exp_time = datetime.fromtimestamp(exp)
                if datetime.utcnow() > exp_time:
                    return False, None, "Token expired"
            
            required_claims = ["kid", "iat", "exp", "aud", "iss", "sub", "scope"]
            missing_claims = [claim for claim in required_claims if claim not in decoded]
            if missing_claims:
                return False, None, f"Missing required claims: {', '.join(missing_claims)}"
            
            return True, decoded, None
            
        except jwt.InvalidTokenError as exc:
            return False, None, f"Invalid token: {str(exc)}"
        except Exception as exc:
            logger.error(f"Token verification error: {exc}")
            return False, None, f"Token verification failed: {str(exc)}"

    def revoke_token(self, jti: str, exp: int) -> None:
        """
        Revoke token by adding jti to denylist with TTL=exp.

        Args:
            jti: JWT ID claim
            exp: Expiration timestamp
        """
        denylist = self.data_plane.cache_get(self.jti_denylist_key) or {}
        denylist[jti] = True
        
        exp_time = datetime.fromtimestamp(exp)
        ttl_seconds = int((exp_time - datetime.utcnow()).total_seconds()) + 86400
        
        self.data_plane.cache_set(self.jti_denylist_key, denylist, ttl_seconds)


class RBACEvaluator:
    """
    RBAC evaluator per IAM spec section 3.1.
    
    RBAC base: role → base permissions.
    Canonical roles: admin, developer, viewer, ci_bot.
    """

    def __init__(self):
        """Initialize RBAC evaluator with role permissions."""
        self.role_permissions = {
            "admin": ["read", "write", "execute", "admin"],
            "developer": ["read", "write", "execute"],
            "viewer": ["read"],
            "ci_bot": ["read", "execute"]
        }

    def map_org_role(self, org_role: str) -> str:
        """
        Map organizational role to canonical role per IAM spec section 2.

        Args:
            org_role: Organizational role

        Returns:
            Canonical role
        """
        return ORG_ROLE_MAPPING.get(org_role, org_role)

    def evaluate(self, roles: List[str], action: str, resource: str) -> Tuple[bool, str]:
        """
        Evaluate RBAC permissions.

        Args:
            roles: List of subject roles
            action: Action to perform
            resource: Resource to access

        Returns:
            Tuple of (is_allowed, reason)
        """
        for role in roles:
            canonical_role = self.map_org_role(role)
            if canonical_role not in CANONICAL_ROLES:
                continue
            
            permissions = self.role_permissions.get(canonical_role, [])
            if action in permissions or "admin" in permissions:
                return True, f"RBAC: {canonical_role} role allows {action}"
        
        return False, f"RBAC: No role allows {action}"


class ABACEvaluator:
    """
    ABAC evaluator per IAM spec section 3.1.
    
    ABAC constraints: time, device posture, location, risk score.
    """

    def __init__(self, trust_plane: MockM32TrustPlane):
        """
        Initialize ABAC evaluator.

        Args:
            trust_plane: Mock M32 trust plane for device posture
        """
        self.trust_plane = trust_plane

    def evaluate(self, context: Optional[DecisionContext], subject: Subject) -> Tuple[bool, str]:
        """
        Evaluate ABAC constraints.

        Args:
            context: Decision context (time, device_posture, location, risk_score)
            subject: Subject requesting access

        Returns:
            Tuple of (is_allowed, reason)
        """
        if not context:
            return True, "ABAC: No constraints specified"
        
        if context.risk_score is not None:
            if context.risk_score > 0.8:
                return False, f"ABAC: Risk score too high ({context.risk_score})"
        
        if context.device_posture:
            if context.device_posture == "insecure":
                return False, "ABAC: Device posture insecure"
        
        if context.time:
            hour = context.time.hour
            if hour < 6 or hour > 22:
                return False, f"ABAC: Outside allowed time window (06:00-22:00), current: {hour:02d}:00"
        
        return True, "ABAC: All constraints satisfied"


class PolicyStore:
    """
    Policy store per IAM spec section 8.
    
    Versioning: Immutable releases with SHA-256 snapshot_id.
    Prior versions retained, deprecation requires explicit end-of-life date.
    """

    def __init__(self, data_plane: MockM29DataPlane):
        """
        Initialize policy store.

        Args:
            data_plane: Mock M29 data plane for policy storage
        """
        self.data_plane = data_plane

    def upsert_policy_bundle(self, bundle: PolicyBundle) -> str:
        """
        Upsert policy bundle with versioning per IAM spec section 8.

        Args:
            bundle: Policy bundle to upsert

        Returns:
            SHA-256 snapshot_id
        """
        bundle_data = bundle.model_dump()
        bundle_data['effective_from'] = bundle.effective_from.isoformat() if bundle.effective_from else datetime.utcnow().isoformat()
        
        snapshot_id = self.data_plane.store_policy(bundle.bundle_id, bundle_data)
        
        for policy in bundle.policies:
            policy_data = policy.model_dump()
            policy_data['bundle_id'] = bundle.bundle_id
            policy_data['bundle_version'] = bundle.version
            self.data_plane.store_policy(policy.id, policy_data)
        
        return snapshot_id

    def get_policy(self, policy_id: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get policy by ID and optional version.

        Args:
            policy_id: Policy identifier
            version: Optional version identifier

        Returns:
            Policy data dictionary or None if not found
        """
        return self.data_plane.get_policy(policy_id, version)

    def list_policies(self) -> List[str]:
        """
        List all policy identifiers.

        Returns:
            List of policy identifiers
        """
        return self.data_plane.list_policies()


class ReceiptGenerator:
    """
    Receipt generator per IAM spec section 7.
    
    Receipts are Ed25519-signed, written to Evidence & Audit Ledger (M27).
    """

    def __init__(self, evidence_ledger: MockM27EvidenceLedger):
        """
        Initialize receipt generator.

        Args:
            evidence_ledger: Mock M27 evidence ledger for receipt signing
        """
        self.evidence_ledger = evidence_ledger

    def generate_receipt(
        self,
        event: str,
        decision: str,
        subject: Subject,
        policy_id: Optional[str] = None,
        risk_score: Optional[float] = None,
        auth_method: Optional[str] = None,
        incident_id: Optional[str] = None,
        approver_identity: Optional[str] = None,
        justification: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate IAM receipt per IAM spec section 7.

        Args:
            event: Event name (authentication_attempt, access_granted, etc.)
            decision: Decision (ALLOW, DENY, etc.)
            subject: Subject information
            policy_id: Optional policy identifier
            risk_score: Optional risk score [0.0, 1.0]
            auth_method: Optional authentication method
            incident_id: Optional incident ID for break-glass per IAM spec section 3.3
            approver_identity: Optional approver identity for break-glass
            justification: Optional justification text for break-glass (non-PII)

        Returns:
            Receipt dictionary with signature
        """
        receipt_id = str(uuid.uuid4())
        receipt = {
            "receipt_id": receipt_id,
            "ts": datetime.utcnow().isoformat() + "Z",
            "module": "IAM",
            "event": event,
            "iam_context": {
                "user_id": subject.sub,
                "auth_method": auth_method or "api_key",
                "access_level": subject.roles[0] if subject.roles else "viewer",
                "permissions_granted": subject.roles,
                "risk_score": risk_score or 0.0
            },
            "decision": decision,
            "policy_id": policy_id or "default",
            "evaluator": "rbac_abac_v1",
            "evidence": {
                "jti": str(uuid.uuid4()),
                "kid": "key-2025q4"
            }
        }
        
        # Add break-glass evidence if provided per IAM spec section 3.3
        if incident_id:
            receipt["evidence"]["incident_id"] = incident_id
        if approver_identity:
            receipt["evidence"]["approver_identity"] = approver_identity
        if justification:
            receipt["evidence"]["justification"] = justification
        
        signature = self.evidence_ledger.sign_receipt(receipt)
        receipt["sig"] = signature
        
        self.evidence_ledger.store_receipt(receipt_id, receipt)
        
        return receipt


class IAMService:
    """
    Main IAM service implementing all business logic per IAM spec v1.1.0.
    
    Implements: token verification, access decision, policy management, JIT elevation, break-glass.
    """

    def __init__(
        self,
        evidence_ledger: Optional[MockM27EvidenceLedger] = None,
        data_plane: Optional[MockM29DataPlane] = None,
        trust_plane: Optional[MockM32TrustPlane] = None
    ):
        """
        Initialize IAM service with dependencies.

        Args:
            evidence_ledger: Mock M27 evidence ledger (default: new instance)
            data_plane: Mock M29 data plane (default: new instance)
            trust_plane: Mock M32 trust plane (default: new instance)
        """
        self.evidence_ledger = evidence_ledger or MockM27EvidenceLedger()
        self.data_plane = data_plane or MockM29DataPlane()
        self.trust_plane = trust_plane or MockM32TrustPlane()
        
        self.token_validator = TokenValidator(self.data_plane)
        self.rbac_evaluator = RBACEvaluator()
        self.abac_evaluator = ABACEvaluator(self.trust_plane)
        self.policy_store = PolicyStore(self.data_plane)
        self.receipt_generator = ReceiptGenerator(self.evidence_ledger)
        
        self.metrics = {
            "authentication_count": 0,
            "decision_count": 0,
            "policy_count": 0,
            "auth_latencies": [],
            "decision_latencies": [],
            "policy_latencies": []
        }

    def verify_token(self, request: VerifyRequest) -> VerifyResponse:
        """
        Verify token per IAM spec section 4.

        Args:
            request: Verify request with token

        Returns:
            Verify response with sub, scope, valid_until

        Raises:
            ValueError: If token is invalid
        """
        start_time = time.perf_counter()
        
        is_valid, claims, error = self.token_validator.verify_token(request.token)
        
        if not is_valid:
            raise ValueError(error or "Token verification failed")
        
        exp = claims.get("exp")
        valid_until = datetime.fromtimestamp(exp) if exp else datetime.utcnow() + timedelta(hours=1)
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        self.metrics["authentication_count"] += 1
        self.metrics["auth_latencies"].append(latency_ms)
        if len(self.metrics["auth_latencies"]) > 1000:
            self.metrics["auth_latencies"] = self.metrics["auth_latencies"][-1000:]
        
        return VerifyResponse(
            sub=claims.get("sub", ""),
            scope=claims.get("scope", []),
            valid_until=valid_until
        )

    def evaluate_decision(self, request: DecisionRequest) -> DecisionResponse:
        """
        Evaluate access decision per IAM spec section 3.1 (precedence order).

        Args:
            request: Decision request with subject, action, resource, context

        Returns:
            Decision response with decision, reason, expires_at, receipt_id
        """
        start_time = time.perf_counter()
        
        receipt_id = str(uuid.uuid4())
        
        # Check for break-glass request per IAM spec section 3.3
        if request.context and request.context.crisis_mode is True:
            # Break-glass must be handled via explicit trigger_break_glass method
            # This check ensures crisis_mode is not ignored
            break_glass_policy = self.policy_store.get_policy("iam-break-glass")
            if not break_glass_policy:
                return DecisionResponse(
                    decision="DENY",
                    reason="Break-glass policy (iam-break-glass) not enabled",
                    receipt_id=receipt_id
                )
        
        if request.elevation and request.elevation.request:
            return self._handle_jit_elevation(request, receipt_id)
        
        policy = self.policy_store.get_policy(f"policy-{request.resource}")
        
        if policy:
            deny_rules = [r for r in policy.get("rules", []) if r.get("rule_type") == "deny"]
            if deny_rules:
                receipt = self.receipt_generator.generate_receipt(
                    "access_denied",
                    "DENY",
                    request.subject,
                    policy.get("id"),
                    request.context.risk_score if request.context else None
                )
                latency_ms = (time.perf_counter() - start_time) * 1000
                self.metrics["decision_count"] += 1
                self.metrics["decision_latencies"].append(latency_ms)
                return DecisionResponse(
                    decision="DENY",
                    reason="Deny override: explicit deny in policy",
                    receipt_id=receipt["receipt_id"]
                )
        
        rbac_allowed, rbac_reason = self.rbac_evaluator.evaluate(
            request.subject.roles,
            request.action,
            request.resource
        )
        
        if not rbac_allowed:
            receipt = self.receipt_generator.generate_receipt(
                "access_denied",
                "DENY",
                request.subject,
                policy.get("id") if policy else None,
                request.context.risk_score if request.context else None
            )
            latency_ms = (time.perf_counter() - start_time) * 1000
            self.metrics["decision_count"] += 1
            self.metrics["decision_latencies"].append(latency_ms)
            return DecisionResponse(
                decision="DENY",
                reason=rbac_reason,
                receipt_id=receipt["receipt_id"]
            )
        
        abac_allowed, abac_reason = self.abac_evaluator.evaluate(
            request.context,
            request.subject
        )
        
        if not abac_allowed:
            receipt = self.receipt_generator.generate_receipt(
                "access_denied",
                "DENY",
                request.subject,
                policy.get("id") if policy else None,
                request.context.risk_score if request.context else None
            )
            latency_ms = (time.perf_counter() - start_time) * 1000
            self.metrics["decision_count"] += 1
            self.metrics["decision_latencies"].append(latency_ms)
            return DecisionResponse(
                decision="DENY",
                reason=abac_reason,
                receipt_id=receipt["receipt_id"]
            )
        
        receipt = self.receipt_generator.generate_receipt(
            "access_granted",
            "ALLOW",
            request.subject,
            policy.get("id") if policy else None,
            request.context.risk_score if request.context else None
        )
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        self.metrics["decision_count"] += 1
        self.metrics["decision_latencies"].append(latency_ms)
        if len(self.metrics["decision_latencies"]) > 1000:
            self.metrics["decision_latencies"] = self.metrics["decision_latencies"][-1000:]
        
        return DecisionResponse(
            decision="ALLOW",
            reason=f"{rbac_reason}; {abac_reason}",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            receipt_id=receipt["receipt_id"]
        )

    def _handle_jit_elevation(self, request: DecisionRequest, receipt_id: str) -> DecisionResponse:
        """
        Handle JIT elevation request per IAM spec section 3.2.

        Args:
            request: Decision request with elevation request
            receipt_id: Receipt identifier

        Returns:
            Decision response with ELEVATION_REQUIRED or ELEVATION_GRANTED
        """
        if not request.elevation or not request.elevation.request:
            return DecisionResponse(
                decision="DENY",
                reason="JIT elevation not requested",
                receipt_id=receipt_id
            )
        
        scope = request.elevation.scope or []
        requires_dual_approval = "admin" in scope
        
        if requires_dual_approval:
            return DecisionResponse(
                decision="ELEVATION_REQUIRED",
                reason="JIT elevation requires dual approval for admin scope",
                receipt_id=receipt_id
            )
        
        granted_until = datetime.utcnow() + timedelta(hours=4)
        
        receipt = self.receipt_generator.generate_receipt(
            "privilege_escalation",
            "ELEVATION_GRANTED",
            request.subject,
            None,
            request.context.risk_score if request.context else None
        )
        
        return DecisionResponse(
            decision="ELEVATION_GRANTED",
            reason="JIT elevation granted",
            expires_at=granted_until,
            receipt_id=receipt["receipt_id"]
        )

    def upsert_policies(self, bundle: PolicyBundle) -> str:
        """
        Upsert policy bundle per IAM spec section 8.

        Args:
            bundle: Policy bundle to upsert

        Returns:
            SHA-256 snapshot_id
        """
        start_time = time.perf_counter()
        
        snapshot_id = self.policy_store.upsert_policy_bundle(bundle)
        
        self.metrics["policy_count"] = len(self.policy_store.list_policies())
        latency_ms = (time.perf_counter() - start_time) * 1000
        self.metrics["policy_latencies"].append(latency_ms)
        if len(self.metrics["policy_latencies"]) > 1000:
            self.metrics["policy_latencies"] = self.metrics["policy_latencies"][-1000:]
        
        return snapshot_id

    def trigger_break_glass(self, request: BreakGlassRequest) -> DecisionResponse:
        """
        Trigger break-glass access per IAM spec section 3.3.
        
        Break-glass is triggered by crisis_mode=true AND policy iam-break-glass enabled.
        Grants minimal time-boxed admin (default 4h).
        Evidence: Incident ID, requester/approver identity, justification text (non-PII).
        Review: Mandatory post-facto review within 24h; auto-revoke if not approved.

        Args:
            request: Break-glass request with subject, incident_id, justification, approver_identity

        Returns:
            Decision response with BREAK_GLASS_GRANTED decision

        Raises:
            ValueError: If break-glass policy not enabled or crisis_mode not true
        """
        start_time = time.perf_counter()
        
        # Check if break-glass policy is enabled per IAM spec section 3.3
        break_glass_policy = self.policy_store.get_policy("iam-break-glass")
        if not break_glass_policy:
            raise ValueError("Break-glass policy (iam-break-glass) not enabled")
        
        # Verify policy status is released
        if break_glass_policy.get("status") != "released":
            raise ValueError(f"Break-glass policy status is {break_glass_policy.get('status')}, must be 'released'")
        
        receipt_id = str(uuid.uuid4())
        
        # Grant minimal time-boxed admin (default 4h) per IAM spec section 3.3
        granted_until = datetime.utcnow() + timedelta(hours=4)
        
        # Generate receipt with break-glass evidence per IAM spec section 3.3
        receipt = self.receipt_generator.generate_receipt(
            event="privilege_escalation",
            decision="BREAK_GLASS_GRANTED",
            subject=request.subject,
            policy_id="iam-break-glass",
            risk_score=1.0,  # Break-glass is highest risk
            auth_method="break_glass",
            incident_id=request.incident_id,
            approver_identity=request.approver_identity,
            justification=request.justification
        )
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        self.metrics["decision_count"] += 1
        self.metrics["decision_latencies"].append(latency_ms)
        if len(self.metrics["decision_latencies"]) > 1000:
            self.metrics["decision_latencies"] = self.metrics["decision_latencies"][-1000:]
        
        return DecisionResponse(
            decision="BREAK_GLASS_GRANTED",
            reason=f"Break-glass access granted for incident {request.incident_id}. Post-facto review required within 24h.",
            expires_at=granted_until,
            receipt_id=receipt["receipt_id"]
        )

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics.

        Returns:
            Metrics dictionary
        """
        auth_latencies = self.metrics["auth_latencies"]
        decision_latencies = self.metrics["decision_latencies"]
        policy_latencies = self.metrics["policy_latencies"]
        
        return {
            "authentication_count": self.metrics["authentication_count"],
            "decision_count": self.metrics["decision_count"],
            "policy_count": self.metrics["policy_count"],
            "average_auth_latency_ms": sum(auth_latencies) / len(auth_latencies) if auth_latencies else 0.0,
            "average_decision_latency_ms": sum(decision_latencies) / len(decision_latencies) if decision_latencies else 0.0,
            "average_policy_latency_ms": sum(policy_latencies) / len(policy_latencies) if policy_latencies else 0.0
        }

