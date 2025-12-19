"""
Business logic layer for Data Governance & Privacy Module (EPC-2).

Architecture:
    - DataClassificationEngine: Automated data discovery & classification
    - PrivacyEnforcementService: Policy-driven privacy enforcement
    - ConsentManagementService: Consent capture, verification, lifecycle
    - DataLineageService: Lineage capture and provenance analytics
    - RetentionManagementService: Retention/deletion policy enforcement
    - DataRightsService: Automated data subject rights workflows
    - DataGovernanceService: Orchestrator that exposes consolidated APIs

All business logic resides here per ZeroUI architecture rules (Tier 3 only).
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timedelta
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from .dependencies import (
    MockM21IAM,  # EPC-1 (Identity & Access Management)
    MockM23PolicyManagement,  # EPC-3 (Configuration & Policy Management)
    MockM27EvidenceLedger,  # PM-7 (Evidence & Receipt Indexing Service / ERIS)
    MockM29DataPlane,  # CCP-6 (Data & Memory Plane)
    MockM33KeyManagement,  # EPC-11 (Key & Trust Management)
)

# --------------------------------------------------------------------------- #
# Utility helpers
# --------------------------------------------------------------------------- #


class PerformanceWindow:
    """Tracks sliding-window latencies to validate PRD latency budgets."""

    def __init__(self, window: int = 1000) -> None:
        self.window = window
        self.entries: List[float] = []

    def add(self, value_ms: float) -> None:
        self.entries.append(value_ms)
        if len(self.entries) > self.window:
            self.entries = self.entries[-self.window :]

    def p95(self) -> float:
        if not self.entries:
            return 0.0
        sorted_entries = sorted(self.entries)
        index = int(len(sorted_entries) * 0.95) - 1
        index = max(0, min(index, len(sorted_entries) - 1))
        return sorted_entries[index]

    def average(self) -> float:
        return mean(self.entries) if self.entries else 0.0


# --------------------------------------------------------------------------- #
# Data Classification
# --------------------------------------------------------------------------- #


class DataClassificationEngine:
    """Implements PRD classification engine requirements."""

    SENSITIVITY_PATTERNS = {
        "pii": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN
        "financial": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),  # credit cards
        "health": re.compile(r"\bICD-\d{1,2}[A-Z0-9]+\b", re.IGNORECASE),
        "proprietary": re.compile(r"(trade secret|confidential roadmap)", re.IGNORECASE),
        "contact": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    }

    CLASSIFICATION_LEVELS = ["public", "internal", "confidential", "restricted"]

    def __init__(
        self,
        data_plane: MockM29DataPlane,
        kms: MockM33KeyManagement,
    ) -> None:
        self.data_plane = data_plane
        self.kms = kms
        self.latencies = PerformanceWindow()

    def classify(
        self,
        tenant_id: str,
        data_location: str,
        data_content: Dict[str, Any],
        context: Dict[str, Any],
        hints: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Classify data per PRD specification.

        Returns:
            Classification record with level, sensitivity tags, confidence, and metadata.
        """
        start = time.perf_counter()

        content_blob = self._flatten_content(data_content)
        sensitivity_tags = self._detect_tags(content_blob, hints or [])
        classification_level = self._determine_level(sensitivity_tags, context)
        confidence = self._calculate_confidence(sensitivity_tags, hints or [])

        record = {
            "classification_id": str(uuid4()),
            "data_id": str(uuid4()),
            "tenant_id": tenant_id,
            "data_location": data_location,
            "classification_level": classification_level,
            "sensitivity_tags": sensitivity_tags,
            "classification_confidence": round(confidence, 2),
            "classified_at": datetime.utcnow().isoformat(),  # type: ignore[name-defined]
            "classified_by": context.get("actor_id", "automated_engine"),
            "classification_method": "automated" if sensitivity_tags else "heuristic",
            "review_required": confidence < 0.75,
            "data_content_hash": self.kms.hash_payload(data_content),
            "data_content_sample": content_blob[:512],
        }

        self.data_plane.store_classification(record.copy())
        latency_ms = (time.perf_counter() - start) * 1000
        self.latencies.add(latency_ms)

        record["performance"] = {
            "latency_ms": round(latency_ms, 2),
            "p95_ms": round(self.latencies.p95(), 2),
            "average_ms": round(self.latencies.average(), 2),
        }
        return record

    def metrics(self) -> Dict[str, Any]:
        """Return classification engine metrics."""
        return {
            "latency_p95_ms": round(self.latencies.p95(), 2),
            "average_latency_ms": round(self.latencies.average(), 2),
            "window": len(self.latencies.entries),
        }

    @staticmethod
    def _flatten_content(payload: Dict[str, Any]) -> str:
        """Flatten nested dict into string for pattern analysis."""
        parts: List[str] = []

        def _walk(value: Any) -> None:
            if isinstance(value, dict):
                for nested in value.values():
                    _walk(nested)
            elif isinstance(value, list):
                for nested in value:
                    _walk(nested)
            else:
                parts.append(str(value))

        _walk(payload)
        return " ".join(parts)

    def _detect_tags(self, blob: str, hints: List[str]) -> List[str]:
        tags: List[str] = []
        for tag, pattern in self.SENSITIVITY_PATTERNS.items():
            if pattern.search(blob):
                tags.append(tag)
        # Merge hints
        for hint in hints:
            normalized = hint.lower()
            if normalized not in tags:
                tags.append(normalized)
        return tags or ["public"]

    @staticmethod
    def _determine_level(tags: List[str], context: Dict[str, Any]) -> str:
        if "financial" in tags or "health" in tags:
            return "restricted"
        if "pii" in tags or "contact" in tags:
            return "confidential"
        if context.get("contains_internal_only"):
            return "internal"
        return "public"

    @staticmethod
    def _calculate_confidence(tags: List[str], hints: List[str]) -> float:
        base = 0.6 if tags else 0.5
        bonus = min(len(tags) * 0.1, 0.3)
        hint_bonus = min(len(hints) * 0.05, 0.25)
        return min(1.0, base + bonus + hint_bonus)


# --------------------------------------------------------------------------- #
# Privacy Enforcement
# --------------------------------------------------------------------------- #


class PrivacyEnforcementService:
    """Evaluates privacy policies, consent state, and IAM permissions."""

    def __init__(
        self,
        policy_engine: MockM23PolicyManagement,
        iam: MockM21IAM,
        evidence_ledger: MockM27EvidenceLedger,
    ) -> None:
        self.policy_engine = policy_engine
        self.iam = iam
        self.evidence_ledger = evidence_ledger
        self.latencies = PerformanceWindow()

    def enforce(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        resource: str,
        policy_id: str,
        context: Dict[str, Any],
        classification_record: Optional[Dict[str, Any]] = None,
        consent_result: Optional[Dict[str, Any]] = None,
        override_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate privacy enforcement decision.
        """
        start = time.perf_counter()

        allowed_permission, reason = self.iam.check_permission(
            tenant_id=tenant_id,
            user_id=user_id,
            permission=action,
            resource=resource,
            override_token=override_token,
        )

        policy_context = {
            **context,
            "action": action,
            "resource": resource,
            "consent_granted": consent_result.get("allowed", False) if consent_result else False,
        }
        policy_result = self.policy_engine.evaluate(
            policy_id=policy_id,
            context=policy_context,
            data_classification=classification_record,
        )

        final_allowed = allowed_permission and policy_result["allowed"]
        violations = []
        if not allowed_permission:
            violations.append("iam_permission_denied")
        violations.extend(policy_result["violations"])
        if consent_result and not consent_result.get("allowed"):
            violations.append("consent_denied")

        receipt_id = self._record_decision(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource=resource,
            decision="ALLOW" if final_allowed else "DENY",
            policy_result=policy_result,
            consent_result=consent_result,
            override_token=override_token,
        )

        latency_ms = (time.perf_counter() - start) * 1000
        self.latencies.add(latency_ms)

        return {
            "allowed": final_allowed,
            "violations": violations,
            "iam_reason": reason,
            "policy_evidence": policy_result["evidence"],
            "receipt_id": receipt_id,
            "latency_ms": round(latency_ms, 2),
            "p95_ms": round(self.latencies.p95(), 2),
        }

    def _record_decision(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        resource: str,
        decision: str,
        policy_result: Dict[str, Any],
        consent_result: Optional[Dict[str, Any]],
        override_token: Optional[str],
    ) -> str:
        receipt_id = str(uuid4())
        payload = {
            "receipt_id": receipt_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "decision": decision,
            "policy": policy_result.get("evidence", {}).get("policy"),
            "violations": policy_result.get("violations", []),
            "consent": consent_result,
            "override_token": override_token,
            "timestamp": datetime.utcnow().isoformat(),
        }
        signature = self.evidence_ledger.sign_receipt(payload)
        payload["signature"] = signature
        self.evidence_ledger.store_receipt(receipt_id, payload)
        return receipt_id


# --------------------------------------------------------------------------- #
# Consent Management
# --------------------------------------------------------------------------- #


class ConsentManagementService:
    """Manages consent capture, verification, and lifecycle events."""

    def __init__(self, data_plane: MockM29DataPlane, kms: MockM33KeyManagement) -> None:
        self.data_plane = data_plane
        self.kms = kms
        self.latencies = PerformanceWindow()

    def grant_consent(
        self,
        tenant_id: str,
        data_subject_id: str,
        purpose: str,
        legal_basis: str,
        data_categories: List[str],
        granted_through: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = {
            "tenant_id": tenant_id,
            "data_subject_id": data_subject_id,
            "purpose": purpose,
            "legal_basis": legal_basis,
            "data_categories": data_categories,
            "granted_through": granted_through,
            "granted_at": datetime.utcnow().isoformat(),
            "version": metadata.get("version", "1.0") if metadata else "1.0",
            "restrictions": metadata.get("restrictions") if metadata else [],
        }
        consent_id = self.data_plane.store_consent(payload)
        payload["consent_id"] = consent_id
        return payload

    def check_consent(
        self,
        tenant_id: str,
        data_subject_id: str,
        purpose: str,
        data_categories: List[str],
        required_legal_basis: Optional[str] = None,
    ) -> Dict[str, Any]:
        start = time.perf_counter()
        consents = [
            record
            for record in self.data_plane.list_consents(tenant_id, data_subject_id)
            if record.get("status") != "revoked"
        ]
        matched = [
            record
            for record in consents
            if record.get("purpose") == purpose and self._categories_allowed(record, data_categories)
        ]
        allowed = bool(matched)
        legal_basis = matched[0]["legal_basis"] if matched else required_legal_basis
        latency_ms = (time.perf_counter() - start) * 1000
        self.latencies.add(latency_ms)
        return {
            "allowed": allowed,
            "consent_id": matched[0]["consent_id"] if matched else None,
            "legal_basis": legal_basis,
            "restrictions": matched[0].get("restrictions", []) if matched else [],
            "latency_ms": round(latency_ms, 2),
            "p95_ms": round(self.latencies.p95(), 2),
        }

    def withdraw_consent(self, consent_id: str, reason: Optional[str] = None) -> bool:
        consent = self.data_plane.get_consent(consent_id)
        if not consent:
            return False
        consent["withdrawal_at"] = datetime.utcnow().isoformat()
        consent["withdrawal_reason"] = reason
        consent["status"] = "revoked"
        return True

    @staticmethod
    def _categories_allowed(record: Dict[str, Any], requested: List[str]) -> bool:
        stored = set(record.get("data_categories", []))
        return stored.issuperset(set(requested))


# --------------------------------------------------------------------------- #
# Data Lineage
# --------------------------------------------------------------------------- #


class DataLineageService:
    """Captures and queries data lineage records."""

    def __init__(self, data_plane: MockM29DataPlane) -> None:
        self.data_plane = data_plane
        self.latencies = PerformanceWindow()

    def record_lineage(
        self,
        tenant_id: str,
        source_data_id: str,
        target_data_id: str,
        transformation_type: str,
        transformation_details: Optional[Dict[str, Any]],
        processed_by: str,
        system_component: str,
    ) -> Dict[str, Any]:
        entry = {
            "tenant_id": tenant_id,
            "source_data_id": source_data_id,
            "target_data_id": target_data_id,
            "transformation_type": transformation_type,
            "transformation_details": transformation_details or {},
            "processed_at": datetime.utcnow().isoformat(),
            "processed_by": processed_by,
            "system_component": system_component,
        }
        lineage_id = self.data_plane.store_lineage(entry)
        entry["lineage_id"] = lineage_id
        return entry

    def query_lineage(self, tenant_id: str, data_id: str) -> Dict[str, Any]:
        start = time.perf_counter()
        entries = self.data_plane.query_lineage(tenant_id, data_id)
        latency_ms = (time.perf_counter() - start) * 1000
        self.latencies.add(latency_ms)
        return {
            "entries": entries,
            "latency_ms": round(latency_ms, 2),
            "p95_ms": round(self.latencies.p95(), 2),
        }


# --------------------------------------------------------------------------- #
# Retention Management
# --------------------------------------------------------------------------- #


class RetentionManagementService:
    """Evaluates retention policies and generates enforcement actions."""

    def __init__(self, data_plane: MockM29DataPlane) -> None:
        self.data_plane = data_plane

    def evaluate_retention(
        self,
        tenant_id: str,
        data_category: str,
        last_activity_months: int,
    ) -> Dict[str, Any]:
        policy = self.data_plane.get_retention_policy(tenant_id, data_category)
        if not policy:
            return {
                "action": "none",
                "policy_id": None,
                "legal_hold": None,
                "regulatory_basis": None,
            }

        should_delete = (
            last_activity_months >= policy["retention_period_months"]
            and not policy.get("legal_hold", False)
        )
        action = "delete" if should_delete and policy.get("auto_delete", True) else "retain"
        return {
            "action": action,
            "policy_id": policy["policy_id"],
            "legal_hold": policy.get("legal_hold", False),
            "regulatory_basis": policy.get("regulatory_basis"),
        }


# --------------------------------------------------------------------------- #
# Data Subject Rights
# --------------------------------------------------------------------------- #


class DataRightsService:
    """Automates GDPR/CCPA rights workflows."""

    def __init__(self, data_plane: MockM29DataPlane, iam: MockM21IAM) -> None:
        self.data_plane = data_plane
        self.iam = iam

    def submit_request(
        self,
        tenant_id: str,
        data_subject_id: str,
        right_type: str,
        verification_data: Dict[str, Any],
        additional_info: Optional[str] = None,
    ) -> Dict[str, Any]:
        request = {
            "tenant_id": tenant_id,
            "data_subject_id": data_subject_id,
            "right_type": right_type,
            "verification_data": verification_data,
            "additional_info": additional_info,
            "status": "pending",
        }
        request_id = self.data_plane.store_rights_request(request)
        return {
            "request_id": request_id,
            "estimated_completion": (datetime.utcnow() + timedelta(days=5)).isoformat(),
            "next_steps": ["verify_identity", "collect_data", "fulfill_request"],
        }

    def update_request_status(
        self,
        tenant_id: str,
        request_id: str,
        status: str,
        processed_by: str,
        notes: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        request = self.data_plane.update_rights_request(
            request_id,
            {
                "status": status,
                "processed_by": processed_by,
                "processed_at": datetime.utcnow().isoformat(),
                "notes": notes,
            },
        )
        if request and request.get("tenant_id") == tenant_id:
            return request
        return None


# --------------------------------------------------------------------------- #
# Receipt Generator
# --------------------------------------------------------------------------- #


class GovernanceReceiptGenerator:
    """Generates signed receipts for module operations."""

    def __init__(self, evidence_ledger: MockM27EvidenceLedger) -> None:
        self.evidence_ledger = evidence_ledger

    def generate(
        self,
        tenant_id: str,
        operation: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        receipt_id = str(uuid4())
        envelope = {
            "receipt_id": receipt_id,
            "tenant_id": tenant_id,
            "operation": operation,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
        }
        signature = self.evidence_ledger.sign_receipt(envelope)
        envelope["signature"] = signature
        self.evidence_ledger.store_receipt(receipt_id, envelope)
        return envelope


# --------------------------------------------------------------------------- #
# Orchestrator
# --------------------------------------------------------------------------- #


class DataGovernanceService:
    """High-level orchestrator exposing module capabilities."""

    def __init__(
        self,
        data_plane: Optional[MockM29DataPlane] = None,
        policy_engine: Optional[MockM23PolicyManagement] = None,
        iam: Optional[MockM21IAM] = None,
        kms: Optional[MockM33KeyManagement] = None,
        evidence_ledger: Optional[MockM27EvidenceLedger] = None,
    ) -> None:
        self.data_plane = data_plane or MockM29DataPlane()
        self.policy_engine = policy_engine or MockM23PolicyManagement()
        self.iam = iam or MockM21IAM()
        self.kms = kms or MockM33KeyManagement()
        self.evidence_ledger = evidence_ledger or MockM27EvidenceLedger()
        self.receipts = GovernanceReceiptGenerator(self.evidence_ledger)

        self.classification_engine = DataClassificationEngine(self.data_plane, self.kms)
        self.consent_service = ConsentManagementService(self.data_plane, self.kms)
        self.lineage_service = DataLineageService(self.data_plane)
        self.retention_service = RetentionManagementService(self.data_plane)
        self.rights_service = DataRightsService(self.data_plane, self.iam)
        self.privacy_enforcement = PrivacyEnforcementService(
            self.policy_engine,
            self.iam,
            self.evidence_ledger,
        )

    # Classification ---------------------------------------------------------
    def classify_data(
        self,
        tenant_id: str,
        data_location: str,
        data_content: Dict[str, Any],
        context: Dict[str, Any],
        hints: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return self.classification_engine.classify(
            tenant_id=tenant_id,
            data_location=data_location,
            data_content=data_content,
            context=context,
            hints=hints,
        )

    # Consent ----------------------------------------------------------------
    def check_consent(
        self,
        tenant_id: str,
        data_subject_id: str,
        purpose: str,
        data_categories: List[str],
        legal_basis: Optional[str],
    ) -> Dict[str, Any]:
        return self.consent_service.check_consent(
            tenant_id=tenant_id,
            data_subject_id=data_subject_id,
            purpose=purpose,
            data_categories=data_categories,
            required_legal_basis=legal_basis,
        )

    # Privacy enforcement ----------------------------------------------------
    def enforce_privacy(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        resource: str,
        policy_id: str,
        context: Dict[str, Any],
        classification_record: Optional[Dict[str, Any]],
        consent_result: Optional[Dict[str, Any]],
        override_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        result = self.privacy_enforcement.enforce(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource=resource,
            policy_id=policy_id,
            context=context,
            classification_record=classification_record,
            consent_result=consent_result,
            override_token=override_token,
        )
        receipt = self.receipts.generate(
            tenant_id=tenant_id,
            operation="privacy_enforcement",
            payload=result,
        )
        result["receipt_id"] = receipt["receipt_id"]
        return result

    # Lineage ----------------------------------------------------------------
    def record_lineage(self, **kwargs: Any) -> Dict[str, Any]:
        return self.lineage_service.record_lineage(**kwargs)

    def query_lineage(self, tenant_id: str, data_id: str) -> Dict[str, Any]:
        return self.lineage_service.query_lineage(tenant_id, data_id)

    # Retention --------------------------------------------------------------
    def evaluate_retention(self, tenant_id: str, data_category: str, last_activity_months: int) -> Dict[str, Any]:
        return self.retention_service.evaluate_retention(tenant_id, data_category, last_activity_months)

    # Rights -----------------------------------------------------------------
    def submit_rights_request(
        self,
        tenant_id: str,
        data_subject_id: str,
        right_type: str,
        verification_data: Dict[str, Any],
        additional_info: Optional[str] = None,
    ) -> Dict[str, Any]:
        result = self.rights_service.submit_request(
            tenant_id=tenant_id,
            data_subject_id=data_subject_id,
            right_type=right_type,
            verification_data=verification_data,
            additional_info=additional_info,
        )
        self.receipts.generate(
            tenant_id=tenant_id,
            operation=f"rights_{right_type}",
            payload=result,
        )
        return result

    # Metrics ----------------------------------------------------------------
    def service_metrics(self) -> Dict[str, Any]:
        return {
            "classification": self.classification_engine.metrics(),
            "consent_p95_ms": self.consent_service.latencies.p95(),
            "privacy_p95_ms": self.privacy_enforcement.latencies.p95(),
            "lineage_p95_ms": self.lineage_service.latencies.p95(),
        }
