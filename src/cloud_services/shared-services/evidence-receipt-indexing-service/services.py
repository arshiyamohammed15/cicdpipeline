"""
Service layer for Evidence & Receipt Indexing Service (ERIS).

What: Business logic for receipt ingestion, validation, query, integrity verification
Why: Encapsulates ERIS logic, provides abstraction for route handlers
Reads/Writes: Reads receipts, writes to database, calls integration services
Contracts: ERIS service contracts per PRD functional requirements
Risks: Data integrity issues, performance degradation, integration failures
"""

import gzip
import hashlib
import json
import logging
import os
import tempfile
import zipfile
from csv import DictWriter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

try:
    from .dependencies import (
        get_schema, validate_receipt_schema, validate_payload_content,
        get_key, verify_signature, get_retention_policy, get_legal_holds
    )
    from .database.models import Receipt, CourierBatch, ExportJob, DLQEntry
    from .database.session import SessionLocal
except ImportError:
    # Fallback for direct imports (testing)
    from dependencies import (
        get_schema, validate_receipt_schema, validate_payload_content,
        get_key, verify_signature, get_retention_policy, get_legal_holds
    )
    from database.models import Receipt, CourierBatch, ExportJob, DLQEntry
    from database.session import SessionLocal

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# Sub-feature 4.1: Receipt Validation Service

class ReceiptValidator:
    """
    Receipt validation service per FR-2.

    Responsibilities:
        - Schema validation via Contracts & Schema Registry
        - Metadata-only payload validation via Data Governance
        - Field normalization
    """

    def __init__(self):
        """Initialize receipt validator."""
        pass

    async def validate_receipt(self, receipt: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Validate receipt against schema and metadata-only constraints.

        Args:
            receipt: Receipt JSON dict

        Returns:
            Tuple of (is_valid, error_message, normalized_receipt)
        """
        schema_version = receipt.get("schema_version")
        if not schema_version:
            return False, "Missing schema_version", None

        # Schema validation
        schema = await get_schema("receipt", schema_version)
        if not schema:
            return False, f"Schema not found: receipt:{schema_version}", None

        is_valid, error = await validate_receipt_schema(receipt, schema_version)
        if not is_valid:
            return False, f"Schema validation failed: {error}", None

        # Metadata-only payload validation
        inputs = receipt.get("inputs", {})
        result = receipt.get("result", {})
        is_valid, error = await validate_payload_content(inputs)
        if not is_valid:
            return False, f"Inputs validation failed: {error}", None
        is_valid, error = await validate_payload_content(result) if result else (True, None)
        if not is_valid:
            return False, f"Result validation failed: {error}", None

        # Normalize receipt
        normalized = self._normalize_receipt(receipt)
        return True, None, normalized

    def _normalize_receipt(self, receipt: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize receipt fields per FR-2.

        Args:
            receipt: Receipt dict

        Returns:
            Normalized receipt dict
        """
        normalized = receipt.copy()

        # Normalize timestamps
        if isinstance(normalized.get("timestamp_utc"), str):
            try:
                normalized["timestamp_utc"] = datetime.fromisoformat(
                    normalized["timestamp_utc"].replace("Z", "+00:00")
                )
            except Exception:
                pass

        # Normalize enum values
        decision_status = normalized.get("decision", {}).get("status") if isinstance(normalized.get("decision"), dict) else normalized.get("decision_status")
        if decision_status:
            normalized["decision_status"] = decision_status.lower()

        evaluation_point = normalized.get("evaluation_point")
        if evaluation_point:
            normalized["evaluation_point"] = evaluation_point.lower().replace("_", "-")

        return normalized


# Sub-feature 4.2: Tenant ID Derivation Service

class TenantIdResolver:
    """
    Tenant ID derivation service per FR-1.

    Implements algorithm: receipt metadata → IAM context → error
    """

    def __init__(self):
        """Initialize tenant ID resolver."""
        # Repository-to-tenant mapping (in production, this would come from IAM/config)
        self.repo_to_tenant: Dict[str, str] = {}

    def derive_tenant_id(self, receipt: Dict[str, Any], iam_context: Optional[Dict[str, Any]] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Derive tenant_id from receipt or IAM context per FR-1 algorithm.

        Args:
            receipt: Receipt dict
            iam_context: IAM context dict (optional)

        Returns:
            Tuple of (tenant_id, error_message)
        """
        # Primary: Extract from receipt metadata
        if "tenant_id" in receipt:
            return receipt["tenant_id"], None

        # Extract from actor.repo_id mapping
        actor = receipt.get("actor", {})
        if isinstance(actor, dict):
            repo_id = actor.get("repo_id")
            if repo_id and repo_id in self.repo_to_tenant:
                return self.repo_to_tenant[repo_id], None

        # Fallback: Extract from IAM context
        if iam_context:
            tenant_id = iam_context.get("tenant_id")
            if tenant_id:
                return tenant_id, None

        # Error: Cannot determine tenant_id
        return None, "tenant_id cannot be determined from receipt metadata or IAM context"

    def register_repo_mapping(self, repo_id: str, tenant_id: str) -> None:
        """Register repository-to-tenant mapping."""
        self.repo_to_tenant[repo_id] = tenant_id


# Sub-feature 4.3: Receipt Ingestion Service

class ReceiptIngestionService:
    """
    Receipt ingestion service per FR-1, FR-3, FR-4.

    Responsibilities:
        - Idempotent receipt ingestion
        - Hash chain management
        - Signature verification
        - Database persistence
    """

    def __init__(self, db: Session):
        """Initialize receipt ingestion service."""
        self.db = db

    async def ingest_receipt(self, receipt: Dict[str, Any], tenant_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Ingest receipt with idempotency and integrity checks.

        Args:
            receipt: Receipt dict
            tenant_id: Tenant identifier

        Returns:
            Tuple of (success, receipt_id, error_message)
        """
        receipt_id = receipt.get("receipt_id")
        if not receipt_id:
            return False, None, "Missing receipt_id"

        # Check idempotency
        existing = self.db.query(Receipt).filter(
            Receipt.receipt_id == UUID(receipt_id),
            Receipt.tenant_id == tenant_id
        ).first()
        if existing:
            return True, receipt_id, None  # Already exists, idempotent success

        # Generate chain_id
        plane = receipt.get("plane", "unknown")
        environment = receipt.get("environment", "unknown")
        emitter_service = receipt.get("emitter_service", receipt.get("gate_id", "unknown"))
        chain_id = f"{tenant_id}:{plane}:{environment}:{emitter_service}"

        # Calculate hash
        receipt_hash = self._calculate_receipt_hash(receipt)

        # Get previous hash for chain
        prev_hash = self._get_previous_hash(chain_id)

        # Verify signature if present
        signature_status = "not_present"
        if receipt.get("signature") and receipt.get("kid"):
            kid = receipt.get("kid")
            # Get key metadata (requires tenant_id, environment, plane from receipt)
            receipt_tenant_id = receipt.get("tenant_id") or tenant_id
            environment = receipt.get("environment", "dev")
            plane = receipt.get("plane", "shared")
            key = await get_key(kid, receipt_tenant_id, environment, plane)
            if key:
                data_bytes = json.dumps(receipt, sort_keys=True, default=str).encode("utf-8")
                is_valid, status = await verify_signature(data_bytes, receipt.get("signature"), kid, receipt_tenant_id, environment, plane)
                signature_status = status if is_valid else "verification_failed"
            else:
                signature_status = "kid_not_found"

        # Validate parent_receipt_id exists if provided (orphaned receipt detection per FR-12)
        parent_receipt_id = receipt.get("parent_receipt_id")
        if parent_receipt_id:
            try:
                parent_exists = self.db.query(Receipt).filter(
                    Receipt.receipt_id == UUID(parent_receipt_id),
                    Receipt.tenant_id == tenant_id
                ).first()
                if not parent_exists:
                    logger.warning("Orphaned receipt detected: receipt_id=%s has parent_receipt_id=%s that does not exist", 
                                  receipt_id, parent_receipt_id)
            except Exception as exc:
                logger.warning("Error checking parent_receipt_id for receipt_id=%s: %s", receipt_id, exc)

        # Create receipt record
        receipt_record = self._create_receipt_record(receipt, tenant_id, chain_id, receipt_hash, prev_hash, signature_status)

        try:
            self.db.add(receipt_record)
            self.db.commit()
            return True, receipt_id, None
        except Exception as exc:
            self.db.rollback()
            logger.error("Failed to persist receipt: %s", exc)
            return False, receipt_id, str(exc)

    def _calculate_receipt_hash(self, receipt: Dict[str, Any]) -> str:
        """Calculate hash of canonical receipt representation."""
        canonical = json.dumps(receipt, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _get_previous_hash(self, chain_id: str) -> Optional[str]:
        """Get previous receipt hash in chain."""
        last_receipt = self.db.query(Receipt).filter(
            Receipt.chain_id == chain_id
        ).order_by(Receipt.timestamp_utc.desc()).first()
        return last_receipt.hash if last_receipt else None

    def _create_receipt_record(self, receipt: Dict[str, Any], tenant_id: str, chain_id: str,
                               receipt_hash: str, prev_hash: Optional[str], signature_status: str) -> Receipt:
        """Create Receipt ORM record from receipt dict."""
        decision = receipt.get("decision", {})
        actor = receipt.get("actor", {})
        timestamp_utc = receipt.get("timestamp_utc")
        if isinstance(timestamp_utc, str):
            timestamp_utc = datetime.fromisoformat(timestamp_utc.replace("Z", "+00:00"))

        dt = timestamp_utc.date() if timestamp_utc else datetime.utcnow().date()

        return Receipt(
            receipt_id=UUID(receipt.get("receipt_id")),
            gate_id=receipt.get("gate_id"),
            schema_version=receipt.get("schema_version"),
            policy_version_ids=receipt.get("policy_version_ids", []),
            snapshot_hash=receipt.get("snapshot_hash"),
            timestamp_utc=timestamp_utc,
            timestamp_monotonic_ms=receipt.get("timestamp_monotonic_ms", 0),
            evaluation_point=receipt.get("evaluation_point"),
            inputs=receipt.get("inputs", {}),
            decision_status=decision.get("status") if isinstance(decision, dict) else receipt.get("decision_status"),
            decision_rationale=decision.get("rationale") if isinstance(decision, dict) else "",
            decision_badges=decision.get("badges", []) if isinstance(decision, dict) else [],
            result=receipt.get("result"),
            actor_repo_id=actor.get("repo_id") if isinstance(actor, dict) else "",
            actor_machine_fingerprint=actor.get("machine_fingerprint") if isinstance(actor, dict) else None,
            actor_type=actor.get("type") if isinstance(actor, dict) else None,
            evidence_handles=receipt.get("evidence_handles"),
            degraded=receipt.get("degraded", False),
            signature=receipt.get("signature"),
            tenant_id=tenant_id,
            plane=receipt.get("plane"),
            environment=receipt.get("environment"),
            module_id=receipt.get("module_id"),
            resource_type=receipt.get("resource_type"),
            resource_id=receipt.get("resource_id"),
            severity=receipt.get("severity"),
            risk_score=receipt.get("risk_score"),
            hash=receipt_hash,
            prev_hash=prev_hash,
            chain_id=chain_id,
            signature_algo=receipt.get("signature_algo"),
            kid=receipt.get("kid"),
            signature_verification_status=signature_status,
            parent_receipt_id=UUID(receipt.get("parent_receipt_id")) if receipt.get("parent_receipt_id") else None,
            related_receipt_ids=[UUID(rid) for rid in receipt.get("related_receipt_ids", [])] if receipt.get("related_receipt_ids") else None,
            emitter_service=receipt.get("emitter_service"),
            ingest_source=receipt.get("ingest_source", "http"),
            dt=dt,
            retention_state="active",
            legal_hold=False
        )


# Phase 5: Query and Aggregation Services

class ReceiptQueryService:
    """
    Receipt query service per FR-5.

    Responsibilities:
        - Search receipts by filters
        - Cursor-based pagination
        - IAM access control integration
    """

    def __init__(self, db: Session):
        """Initialize receipt query service."""
        self.db = db

    def search_receipts(self, filters: Dict[str, Any], tenant_id: str, cursor: Optional[str] = None, limit: int = 100) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Search receipts with filters and pagination.

        Args:
            filters: Search filters
            tenant_id: Tenant identifier
            cursor: Pagination cursor
            limit: Page size

        Returns:
            Tuple of (receipts_list, next_cursor)
        """
        query = self.db.query(Receipt).filter(Receipt.tenant_id == tenant_id)

        # Apply filters
        if filters.get("from_timestamp"):
            query = query.filter(Receipt.timestamp_utc >= filters["from_timestamp"])
        if filters.get("to_timestamp"):
            query = query.filter(Receipt.timestamp_utc <= filters["to_timestamp"])
        if filters.get("gate_id"):
            query = query.filter(Receipt.gate_id == filters["gate_id"])
        if filters.get("decision_status"):
            query = query.filter(Receipt.decision_status == filters["decision_status"])
        if filters.get("module_id"):
            query = query.filter(Receipt.module_id == filters["module_id"])
        if filters.get("actor_repo_id"):
            query = query.filter(Receipt.actor_repo_id == filters["actor_repo_id"])
        if filters.get("actor_type"):
            query = query.filter(Receipt.actor_type == filters["actor_type"])
        if filters.get("resource_type"):
            query = query.filter(Receipt.resource_type == filters["resource_type"])
        if filters.get("resource_id"):
            query = query.filter(Receipt.resource_id == filters["resource_id"])
        if filters.get("chain_id"):
            query = query.filter(Receipt.chain_id == filters["chain_id"])
        if filters.get("parent_receipt_id"):
            query = query.filter(Receipt.parent_receipt_id == UUID(filters["parent_receipt_id"]))
        if filters.get("severity"):
            query = query.filter(Receipt.severity == filters["severity"])
        if filters.get("policy_version_ids"):
            # Use PostgreSQL array overlap operator for array field
            policy_ids = filters["policy_version_ids"]
            if isinstance(policy_ids, list) and len(policy_ids) > 0:
                query = query.filter(Receipt.policy_version_ids.overlap(policy_ids))

        # Apply cursor if provided
        if cursor:
            try:
                cursor_timestamp = datetime.fromisoformat(cursor)
                query = query.filter(Receipt.timestamp_utc > cursor_timestamp)
            except Exception:
                pass

        # Order and limit
        query = query.order_by(Receipt.timestamp_utc.asc()).limit(limit + 1)
        receipts = query.all()

        # Determine next cursor
        next_cursor = None
        if len(receipts) > limit:
            next_cursor = receipts[limit].timestamp_utc.isoformat()
            receipts = receipts[:limit]

        # Convert to dicts
        receipt_dicts = [self._receipt_to_dict(r) for r in receipts]
        return receipt_dicts, next_cursor

    def _receipt_to_dict(self, receipt: Receipt) -> Dict[str, Any]:
        """Convert Receipt ORM to dict."""
        return {
            "receipt_id": str(receipt.receipt_id),
            "gate_id": receipt.gate_id,
            "timestamp_utc": receipt.timestamp_utc.isoformat(),
            "decision": {
                "status": receipt.decision_status,
                "rationale": receipt.decision_rationale,
                "badges": receipt.decision_badges or []
            },
            "actor": {
                "repo_id": receipt.actor_repo_id,
                "machine_fingerprint": receipt.actor_machine_fingerprint,
                "type": receipt.actor_type
            },
            "inputs": receipt.inputs,
            "result": receipt.result
        }


class ReceiptAggregationService:
    """
    Receipt aggregation service per FR-5.

    Responsibilities:
        - Aggregations by decision.status, policy_version_id, module_id, etc.
        - Time bucket aggregations
    """

    def __init__(self, db: Session):
        """Initialize receipt aggregation service."""
        self.db = db

    def aggregate_receipts(self, filters: Dict[str, Any], group_by: List[str], tenant_id: str, time_bucket: Optional[str] = None) -> Dict[str, Any]:
        """
        Aggregate receipts by specified dimensions per FR-5.

        Args:
            filters: Filter criteria
            group_by: Fields to group by (decision.status, policy_version_id, module_id, gate_id, actor.type, plane, environment, etc.)
            tenant_id: Tenant identifier
            time_bucket: Time bucket (day, week, month)

        Returns:
            Aggregation results dict
        """
        query = self.db.query(Receipt).filter(Receipt.tenant_id == tenant_id)

        # Apply filters
        if filters.get("from_timestamp"):
            query = query.filter(Receipt.timestamp_utc >= filters["from_timestamp"])
        if filters.get("to_timestamp"):
            query = query.filter(Receipt.timestamp_utc <= filters["to_timestamp"])
        if filters.get("gate_id"):
            query = query.filter(Receipt.gate_id == filters["gate_id"])
        if filters.get("module_id"):
            query = query.filter(Receipt.module_id == filters["module_id"])
        if filters.get("plane"):
            query = query.filter(Receipt.plane == filters["plane"])
        if filters.get("environment"):
            query = query.filter(Receipt.environment == filters["environment"])

        receipts = query.all()

        aggregations = {}

        # Aggregation by decision.status
        if "decision.status" in group_by or "decision_status" in group_by:
            decision_counts = {}
            for receipt in receipts:
                status = receipt.decision_status
                decision_counts[status] = decision_counts.get(status, 0) + 1
            aggregations["by_decision_status"] = decision_counts

        # Aggregation by policy_version_id
        if "policy_version_id" in group_by or "policy_version_ids" in group_by:
            policy_counts = {}
            for receipt in receipts:
                for policy_id in (receipt.policy_version_ids or []):
                    policy_counts[policy_id] = policy_counts.get(policy_id, 0) + 1
            aggregations["by_policy_version_id"] = policy_counts

        # Aggregation by module_id
        if "module_id" in group_by:
            module_counts = {}
            for receipt in receipts:
                module_id = receipt.module_id or "unknown"
                module_counts[module_id] = module_counts.get(module_id, 0) + 1
            aggregations["by_module_id"] = module_counts

        # Aggregation by gate_id
        if "gate_id" in group_by:
            gate_counts = {}
            for receipt in receipts:
                gate_id = receipt.gate_id
                gate_counts[gate_id] = gate_counts.get(gate_id, 0) + 1
            aggregations["by_gate_id"] = gate_counts

        # Aggregation by actor.type
        if "actor.type" in group_by or "actor_type" in group_by:
            actor_type_counts = {}
            for receipt in receipts:
                actor_type = receipt.actor_type or "unknown"
                actor_type_counts[actor_type] = actor_type_counts.get(actor_type, 0) + 1
            aggregations["by_actor_type"] = actor_type_counts

        # Aggregation by plane
        if "plane" in group_by:
            plane_counts = {}
            for receipt in receipts:
                plane = receipt.plane or "unknown"
                plane_counts[plane] = plane_counts.get(plane, 0) + 1
            aggregations["by_plane"] = plane_counts

        # Aggregation by environment
        if "environment" in group_by:
            env_counts = {}
            for receipt in receipts:
                env = receipt.environment or "unknown"
                env_counts[env] = env_counts.get(env, 0) + 1
            aggregations["by_environment"] = env_counts

        # Aggregation by severity (if present)
        if "severity" in group_by:
            severity_counts = {}
            for receipt in receipts:
                if receipt.severity:
                    severity_counts[receipt.severity] = severity_counts.get(receipt.severity, 0) + 1
            if severity_counts:
                aggregations["by_severity"] = severity_counts

        # Combined aggregations (decision.status by gate_id, module_id, tenant_id)
        if "decision.status" in group_by and "gate_id" in group_by:
            decision_by_gate = {}
            for receipt in receipts:
                gate_id = receipt.gate_id
                status = receipt.decision_status
                if gate_id not in decision_by_gate:
                    decision_by_gate[gate_id] = {}
                decision_by_gate[gate_id][status] = decision_by_gate[gate_id].get(status, 0) + 1
            aggregations["by_decision_status_and_gate_id"] = decision_by_gate

        if "decision.status" in group_by and "module_id" in group_by:
            decision_by_module = {}
            for receipt in receipts:
                module_id = receipt.module_id or "unknown"
                status = receipt.decision_status
                if module_id not in decision_by_module:
                    decision_by_module[module_id] = {}
                decision_by_module[module_id][status] = decision_by_module[module_id].get(status, 0) + 1
            aggregations["by_decision_status_and_module_id"] = decision_by_module

        # Time bucket aggregation
        if time_bucket:
            time_buckets = {}
            for receipt in receipts:
                if time_bucket == "day":
                    bucket_key = receipt.dt.isoformat()
                elif time_bucket == "week":
                    # Simple week calculation
                    bucket_key = f"{receipt.dt.year}-W{receipt.dt.isocalendar()[1]}"
                elif time_bucket == "month":
                    bucket_key = f"{receipt.dt.year}-{receipt.dt.month:02d}"
                else:
                    bucket_key = receipt.dt.isoformat()

                if bucket_key not in time_buckets:
                    time_buckets[bucket_key] = 0
                time_buckets[bucket_key] += 1
            aggregations["by_time_bucket"] = time_buckets

        return {"aggregations": aggregations, "total_count": len(receipts)}


# Phase 6: Integrity and Chain Services

class IntegrityVerificationService:
    """
    Integrity verification service per FR-4.

    Responsibilities:
        - Single receipt verification (hash, signature)
        - Range verification (hash-chain continuity)
        - Chain head management
    """

    def __init__(self, db: Session):
        """Initialize integrity verification service."""
        self.db = db

    def verify_receipt(self, receipt_id: str, tenant_id: str) -> Dict[str, Any]:
        """
        Verify single receipt integrity.

        Args:
            receipt_id: Receipt identifier
            tenant_id: Tenant identifier

        Returns:
            Verification result dict
        """
        receipt = self.db.query(Receipt).filter(
            Receipt.receipt_id == UUID(receipt_id),
            Receipt.tenant_id == tenant_id
        ).first()

        if not receipt:
            return {"hash_valid": False, "error": "Receipt not found"}

        # Verify hash
        receipt_dict = self._receipt_to_dict_for_hash(receipt)
        calculated_hash = hashlib.sha256(
            json.dumps(receipt_dict, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        hash_valid = calculated_hash == receipt.hash

        return {
            "hash_valid": hash_valid,
            "signature_valid": receipt.signature_verification_status == "verified",
            "signature_verification_status": receipt.signature_verification_status
        }

    def verify_range(self, tenant_id: str, chain_id: str, from_timestamp: datetime, to_timestamp: datetime) -> Dict[str, Any]:
        """
        Verify hash-chain continuity for receipt range.

        Args:
            tenant_id: Tenant identifier
            chain_id: Chain identifier
            from_timestamp: Start timestamp
            to_timestamp: End timestamp

        Returns:
            Verification result dict
        """
        receipts = self.db.query(Receipt).filter(
            Receipt.tenant_id == tenant_id,
            Receipt.chain_id == chain_id,
            Receipt.timestamp_utc >= from_timestamp,
            Receipt.timestamp_utc <= to_timestamp
        ).order_by(Receipt.timestamp_utc.asc()).all()

        if not receipts:
            return {"valid": False, "error": "No receipts found in range"}

        gaps = []
        for i in range(1, len(receipts)):
            prev_receipt = receipts[i - 1]
            curr_receipt = receipts[i]
            if curr_receipt.prev_hash != prev_receipt.hash:
                gaps.append({
                    "receipt_id": str(curr_receipt.receipt_id),
                    "expected_prev_hash": prev_receipt.hash,
                    "actual_prev_hash": curr_receipt.prev_hash
                })

        return {
            "valid": len(gaps) == 0,
            "receipt_count": len(receipts),
            "gaps": gaps
        }

    def _receipt_to_dict_for_hash(self, receipt: Receipt) -> Dict[str, Any]:
        """Convert receipt to dict for hash calculation."""
        return {
            "receipt_id": str(receipt.receipt_id),
            "gate_id": receipt.gate_id,
            "timestamp_utc": receipt.timestamp_utc.isoformat(),
            "decision_status": receipt.decision_status,
            "actor_repo_id": receipt.actor_repo_id,
            "inputs": receipt.inputs,
            "result": receipt.result
        }


class ChainTraversalService:
    """
    Receipt chain traversal service per FR-12.

    Responsibilities:
        - Traverse parent_receipt_id links (up/down)
        - Traverse related_receipt_ids (siblings)
        - Circular reference detection
        - Orphaned receipt detection
        - Max depth handling
    """

    def __init__(self, db: Session):
        """Initialize chain traversal service."""
        self.db = db

    def traverse_chain(self, receipt_id: str, tenant_id: str, direction: str = "both", max_depth: int = 10) -> Dict[str, Any]:
        """
        Traverse receipt chain.

        Args:
            receipt_id: Starting receipt identifier
            tenant_id: Tenant identifier
            direction: Traversal direction (up, down, both, siblings)
            max_depth: Maximum traversal depth

        Returns:
            Chain traversal result dict
        """
        visited = set()
        receipts = []
        circular_refs = []

        def traverse_up(curr_id: str, depth: int):
            if depth > max_depth or curr_id in visited:
                if curr_id in visited:
                    circular_refs.append(curr_id)
                return
            visited.add(curr_id)

            receipt = self.db.query(Receipt).filter(
                Receipt.receipt_id == UUID(curr_id),
                Receipt.tenant_id == tenant_id
            ).first()

            if not receipt:
                # Orphaned receipt detected (parent_receipt_id points to non-existent receipt)
                logger.warning("Orphaned receipt detected: receipt_id=%s has parent_receipt_id=%s that does not exist", 
                              curr_id, curr_id)
                return

            receipts.append(self._receipt_to_dict(receipt))

            if receipt.parent_receipt_id:
                traverse_up(str(receipt.parent_receipt_id), depth + 1)

        def traverse_down(curr_id: str, depth: int):
            if depth > max_depth or curr_id in visited:
                if curr_id in visited:
                    circular_refs.append(curr_id)
                return
            visited.add(curr_id)

            child_receipts = self.db.query(Receipt).filter(
                Receipt.parent_receipt_id == UUID(curr_id),
                Receipt.tenant_id == tenant_id
            ).all()

            for child in child_receipts:
                receipts.append(self._receipt_to_dict(child))
                traverse_down(str(child.receipt_id), depth + 1)

        def traverse_siblings(curr_id: str):
            receipt = self.db.query(Receipt).filter(
                Receipt.receipt_id == UUID(curr_id),
                Receipt.tenant_id == tenant_id
            ).first()

            if not receipt or not receipt.related_receipt_ids:
                return

            for related_id in receipt.related_receipt_ids:
                if str(related_id) not in visited:
                    visited.add(str(related_id))
                    related_receipt = self.db.query(Receipt).filter(
                        Receipt.receipt_id == related_id,
                        Receipt.tenant_id == tenant_id
                    ).first()
                    if related_receipt:
                        receipts.append(self._receipt_to_dict(related_receipt))

        # Start traversal
        if direction in ["up", "both"]:
            traverse_up(receipt_id, 0)
        if direction in ["down", "both"]:
            traverse_down(receipt_id, 0)
        if direction == "siblings":
            traverse_siblings(receipt_id)

        return {
            "receipts": receipts,
            "traversal_depth": len(receipts),
            "circular_references_detected": len(circular_refs) > 0
        }

    def _receipt_to_dict(self, receipt: Receipt) -> Dict[str, Any]:
        """Convert Receipt ORM to dict."""
        return {
            "receipt_id": str(receipt.receipt_id),
            "gate_id": receipt.gate_id,
            "timestamp_utc": receipt.timestamp_utc.isoformat(),
            "decision": {
                "status": receipt.decision_status,
                "rationale": receipt.decision_rationale
            },
            "actor": {
                "repo_id": receipt.actor_repo_id
            }
        }


# Phase 7: Courier Batch and Export Services

class CourierBatchService:
    """
    Courier batch service per FR-10.

    Responsibilities:
        - Batch ingestion with idempotency
        - Merkle root validation
        - Receipt deduplication within batch
        - Batch metadata storage
    """

    def __init__(self, db: Session):
        """Initialize courier batch service."""
        self.db = db

    async def ingest_batch(self, batch_data: Dict[str, Any], tenant_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Ingest courier batch with idempotency and validation.

        Args:
            batch_data: Courier batch dict
            tenant_id: Tenant identifier

        Returns:
            Tuple of (success, batch_id, error_message)
        """
        batch_id = batch_data.get("batch_id")
        if not batch_id:
            return False, None, "Missing batch_id"

        # Check idempotency
        existing = self.db.query(CourierBatch).filter(
            CourierBatch.batch_id == UUID(batch_id)
        ).first()
        if existing:
            return True, batch_id, None  # Already exists

        # Validate Merkle root and calculate leaf hashes
        merkle_root = batch_data.get("merkle_root")
        receipts = batch_data.get("receipts", [])
        calculated_root, leaf_hashes = self._calculate_merkle_root(receipts)
        if calculated_root != merkle_root:
            return False, batch_id, f"Merkle root mismatch: expected {merkle_root}, got {calculated_root}"

        # Deduplicate receipts within batch
        seen_receipt_ids = set()
        unique_receipts = []
        for receipt in receipts:
            receipt_id = receipt.get("receipt_id")
            if receipt_id and receipt_id not in seen_receipt_ids:
                seen_receipt_ids.add(receipt_id)
                unique_receipts.append(receipt)

        try:
            # Ingest individual receipts from batch per FR-10
            ingestion_service = ReceiptIngestionService(self.db)
            ingested_count = 0
            failed_count = 0
            
            for receipt in unique_receipts:
                try:
                    # Ensure receipt has tenant_id (use batch tenant_id if not present)
                    if "tenant_id" not in receipt:
                        receipt["tenant_id"] = tenant_id
                    
                    # Ingest receipt (idempotent, so duplicates are handled)
                    success, receipt_id, error = await ingestion_service.ingest_receipt(receipt, tenant_id)
                    if success:
                        ingested_count += 1
                    else:
                        failed_count += 1
                        logger.warning("Failed to ingest receipt %s from batch %s: %s", receipt_id, batch_id, error)
                except Exception as exc:
                    failed_count += 1
                    logger.error("Error ingesting receipt from batch %s: %s", batch_id, exc)
            
            # Create batch record with leaf hashes
            batch_record = CourierBatch(
                batch_id=UUID(batch_id),
                tenant_id=tenant_id,
                emitter_service=batch_data.get("emitter_service"),
                merkle_root=merkle_root,
                sequence_numbers=batch_data.get("sequence_numbers", []),
                receipt_count=len(unique_receipts),
                leaf_hashes=leaf_hashes,
                timestamp=batch_data.get("timestamp", datetime.utcnow()),
                status="completed" if failed_count == 0 else "partial"
            )

            self.db.add(batch_record)
            self.db.commit()
            
            if failed_count > 0:
                logger.warning("Batch %s ingested with %d failures out of %d receipts", batch_id, failed_count, len(unique_receipts))
            
            return True, batch_id, None
        except Exception as exc:
            self.db.rollback()
            logger.error("Failed to persist batch: %s", exc)
            return False, batch_id, str(exc)

    def _calculate_merkle_root(self, receipts: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """
        Calculate Merkle root for receipts and return leaf hashes.
        
        Returns:
            Tuple of (merkle_root, leaf_hashes)
        """
        if not receipts:
            return "", []
        # Calculate leaf hashes (one per receipt)
        leaf_hashes = [hashlib.sha256(json.dumps(r, sort_keys=True, default=str).encode("utf-8")).hexdigest() for r in receipts]
        
        # Build Merkle tree from leaves to root
        hashes = leaf_hashes.copy()
        while len(hashes) > 1:
            new_hashes = []
            for i in range(0, len(hashes), 2):
                if i + 1 < len(hashes):
                    combined = hashes[i] + hashes[i + 1]
                else:
                    combined = hashes[i]
                new_hashes.append(hashlib.sha256(combined.encode("utf-8")).hexdigest())
            hashes = new_hashes
        merkle_root = hashes[0] if hashes else ""
        return merkle_root, leaf_hashes


class MerkleProofService:
    """
    Merkle proof service per FR-10.

    Responsibilities:
        - Generate Merkle proof for batch
        - Proof structure (root, leaf hashes, path)
    """

    def __init__(self, db: Session):
        """Initialize Merkle proof service."""
        self.db = db

    def get_merkle_proof(self, batch_id: str, leaf_index: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get Merkle proof for batch.

        Args:
            batch_id: Batch identifier
            leaf_index: Optional leaf index to calculate path for specific leaf

        Returns:
            Merkle proof dict or None
        """
        batch = self.db.query(CourierBatch).filter(
            CourierBatch.batch_id == UUID(batch_id)
        ).first()

        if not batch:
            return None

        leaf_hashes = batch.leaf_hashes or []
        
        # Calculate path_to_root for a specific leaf or for all leaves
        path_to_root = []
        if leaf_index is not None and 0 <= leaf_index < len(leaf_hashes):
            # Calculate path from specific leaf to root
            path_to_root = self._calculate_path_to_root(leaf_hashes, leaf_index, batch.merkle_root)
        elif len(leaf_hashes) > 0:
            # Default: calculate path for first leaf
            path_to_root = self._calculate_path_to_root(leaf_hashes, 0, batch.merkle_root)

        return {
            "batch_id": str(batch.batch_id),
            "merkle_root": batch.merkle_root,
            "leaf_hashes": leaf_hashes,
            "path_to_root": path_to_root
        }
    
    def _calculate_path_to_root(self, leaf_hashes: List[str], leaf_index: int, root_hash: str) -> List[str]:
        """
        Calculate path from a leaf to the root in Merkle tree.
        
        Args:
            leaf_hashes: List of leaf hashes
            leaf_index: Index of the leaf to calculate path for
            root_hash: Root hash of the tree
            
        Returns:
            List of hashes representing path from leaf to root
        """
        if not leaf_hashes or leaf_index >= len(leaf_hashes):
            return []
        
        path = []
        current_level = leaf_hashes.copy()
        current_index = leaf_index
        
        # Build tree level by level and track path
        while len(current_level) > 1:
            # Add sibling hash to path (the hash paired with current node)
            if current_index % 2 == 0:
                # Current is left, sibling is right (if exists)
                if current_index + 1 < len(current_level):
                    path.append(current_level[current_index + 1])
                else:
                    # No sibling, path continues with current
                    path.append(current_level[current_index])
            else:
                # Current is right, sibling is left
                path.append(current_level[current_index - 1])
            
            # Build next level
            next_level = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined = current_level[i] + current_level[i + 1]
                else:
                    combined = current_level[i]
                next_level.append(hashlib.sha256(combined.encode("utf-8")).hexdigest())
            
            current_level = next_level
            current_index = current_index // 2
        
        return path


class ExportService:
    """
    Export service per FR-11.

    Responsibilities:
        - Async export job creation
        - Export file generation (JSONL, CSV, Parquet)
        - Data Governance constraint enforcement
        - Export metadata tracking
    """

    def __init__(self, db: Session, export_storage_path: Optional[str] = None):
        """
        Initialize export service.
        
        Args:
            db: Database session
            export_storage_path: Path to store export files (defaults to temp directory)
        """
        self.db = db
        self.export_storage_path = export_storage_path or os.path.join(tempfile.gettempdir(), "eris_exports")
        Path(self.export_storage_path).mkdir(parents=True, exist_ok=True)

    def create_export_job(self, export_request: Dict[str, Any], tenant_id: str) -> str:
        """
        Create export job.

        Args:
            export_request: Export request dict
            tenant_id: Tenant identifier

        Returns:
            Export job identifier
        """
        export_id = str(uuid4())

        export_job = ExportJob(
            export_id=UUID(export_id),
            tenant_id=tenant_id,
            status="pending",
            export_format=export_request.get("export_format", "jsonl"),
            compression=export_request.get("compression", "gzip"),
            filters=export_request.get("filters", {}),
            created_at=datetime.utcnow()
        )

        try:
            self.db.add(export_job)
            self.db.commit()
            return export_id
        except Exception as exc:
            self.db.rollback()
            logger.error("Failed to create export job: %s", exc)
            raise

    def get_export_status(self, export_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get export job status.

        Args:
            export_id: Export job identifier
            tenant_id: Tenant identifier

        Returns:
            Export status dict or None
        """
        export_job = self.db.query(ExportJob).filter(
            ExportJob.export_id == UUID(export_id),
            ExportJob.tenant_id == tenant_id
        ).first()

        if not export_job:
            return None

        return {
            "export_id": str(export_job.export_id),
            "status": export_job.status,
            "download_url": export_job.download_url,
            "export_metadata": {
                "receipt_count": export_job.receipt_count,
                "export_format": export_job.export_format,
                "compression": export_job.compression,
                "file_size": export_job.file_size,
                "checksum": export_job.checksum
            },
            "created_at": export_job.created_at.isoformat(),
            "updated_at": export_job.updated_at.isoformat() if export_job.updated_at else None
        }
    
    async def _generate_export_file(self, export_job: ExportJob) -> None:
        """
        Generate export file asynchronously.
        
        Args:
            export_job: Export job record
        """
        try:
            # Update status to processing
            export_job.status = "processing"
            export_job.updated_at = datetime.utcnow()
            self.db.commit()
            
            # Query receipts based on filters
            query_service = ReceiptQueryService(self.db)
            filters = export_job.filters or {}
            tenant_id = export_job.tenant_id
            
            # Get all receipts (no pagination for export)
            receipts, _ = query_service.search_receipts(filters, tenant_id, None, limit=1000000)
            
            # Generate file based on format
            file_path = self._write_export_file(receipts, export_job)
            
            # Compress if needed
            if export_job.compression and export_job.compression != "none":
                file_path = self._compress_file(file_path, export_job.compression)
            
            # Calculate file size and checksum
            file_size = os.path.getsize(file_path)
            checksum = self._calculate_file_checksum(file_path)
            
            # Generate download URL (simplified - in production would use signed URL)
            download_url = f"/v1/evidence/export/{export_job.export_id}/download"
            
            # Set expiration (7 days from creation)
            expires_at = export_job.created_at + timedelta(days=7)
            
            # Update export job
            export_job.status = "completed"
            export_job.download_url = download_url
            export_job.receipt_count = len(receipts)
            export_job.file_size = file_size
            export_job.checksum = checksum
            export_job.expires_at = expires_at
            export_job.completed_at = datetime.utcnow()
            export_job.updated_at = datetime.utcnow()
            self.db.commit()
            
        except Exception as exc:
            logger.error("Export file generation failed: %s", exc)
            export_job.status = "failed"
            export_job.updated_at = datetime.utcnow()
            self.db.commit()
            raise
    
    def _write_export_file(self, receipts: List[Dict[str, Any]], export_job: ExportJob) -> str:
        """
        Write receipts to file in specified format.
        
        Args:
            receipts: List of receipt dicts
            export_job: Export job record
            
        Returns:
            Path to generated file
        """
        export_format = export_job.export_format
        export_id = str(export_job.export_id)
        file_path = os.path.join(self.export_storage_path, f"{export_id}.{export_format}")
        
        if export_format == "jsonl":
            with open(file_path, 'w', encoding='utf-8') as f:
                for receipt in receipts:
                    f.write(json.dumps(receipt, default=str) + '\n')
        
        elif export_format == "csv":
            if not receipts:
                # Create empty CSV file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("")
            else:
                # Flatten nested structures for CSV
                flattened = [self._flatten_receipt(r) for r in receipts]
                fieldnames = set()
                for rec in flattened:
                    fieldnames.update(rec.keys())
                
                with open(file_path, 'w', encoding='utf-8', newline='') as f:
                    writer = DictWriter(f, fieldnames=sorted(fieldnames))
                    writer.writeheader()
                    writer.writerows(flattened)
        
        elif export_format == "parquet":
            # Parquet format support per FR-11
            try:
                try:
                    import pyarrow as pa
                    import pyarrow.parquet as pq
                    use_pyarrow = True
                except ImportError:
                    try:
                        import pandas as pd
                        use_pyarrow = False
                    except ImportError:
                        raise ImportError("Parquet format requires pyarrow or pandas. Install with: pip install pyarrow or pip install pandas")
                
                if use_pyarrow:
                    # Use pyarrow for Parquet writing
                    # Convert receipts to list of dicts and create Arrow table
                    table = pa.Table.from_pylist(receipts)
                    pq.write_table(table, file_path)
                else:
                    # Use pandas for Parquet writing
                    df = pd.DataFrame(receipts)
                    # Flatten nested structures for Parquet
                    df_flat = pd.json_normalize(receipts)
                    df_flat.to_parquet(file_path, engine='pyarrow' if 'pyarrow' in globals() else 'fastparquet', index=False)
            except ImportError as ie:
                logger.error("Parquet dependencies not available: %s", ie)
                raise ValueError(f"Parquet format requires pyarrow or pandas: {ie}")
            except Exception as exc:
                logger.error("Failed to write Parquet file: %s", exc)
                raise
        else:
            raise ValueError(f"Unsupported export format: {export_format}")
        
        return file_path
    
    def _flatten_receipt(self, receipt: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """
        Flatten nested receipt structure for CSV export.
        
        Args:
            receipt: Receipt dict
            parent_key: Parent key prefix
            sep: Separator for nested keys
            
        Returns:
            Flattened dict
        """
        items = []
        for k, v in receipt.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_receipt(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert lists to JSON strings for CSV
                items.append((new_key, json.dumps(v, default=str)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _compress_file(self, file_path: str, compression: str) -> str:
        """
        Compress file using specified compression method.
        
        Args:
            file_path: Path to file to compress
            compression: Compression method (gzip, zip)
            
        Returns:
            Path to compressed file
        """
        if compression == "gzip":
            compressed_path = f"{file_path}.gz"
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            os.remove(file_path)
            return compressed_path
        
        elif compression == "zip":
            compressed_path = f"{file_path}.zip"
            with zipfile.ZipFile(compressed_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(file_path, os.path.basename(file_path))
            os.remove(file_path)
            return compressed_path
        
        else:
            return file_path
    
    def _calculate_file_checksum(self, file_path: str) -> str:
        """
        Calculate SHA256 checksum of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 checksum as hex string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


# Phase 8: Retention and Meta-Audit Services

class RetentionManagementService:
    """
    Retention management service per FR-7.

    Responsibilities:
        - Query Data Governance for retention policies
        - Mark receipts as archived/expired
        - Legal hold handling
        - Retention policy re-evaluation
    """

    def __init__(self, db: Session):
        """Initialize retention management service."""
        self.db = db

    async def evaluate_retention(self, tenant_id: str) -> Dict[str, Any]:
        """
        Evaluate retention policies for tenant receipts.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Evaluation result dict
        """
        # Get retention policy from Data Governance
        retention_policy = await get_retention_policy(tenant_id)
        if not retention_policy:
            return {"evaluated": 0, "archived": 0, "expired": 0}

        retention_months = retention_policy.get("retention_period_months", 12)
        cutoff_date = datetime.utcnow() - timedelta(days=retention_months * 30)

        # Get legal holds
        legal_holds = await get_legal_holds(tenant_id)
        legal_hold_incidents = set(legal_holds)

        # Query receipts that should be archived/expired
        receipts = self.db.query(Receipt).filter(
            Receipt.tenant_id == tenant_id,
            Receipt.timestamp_utc < cutoff_date,
            Receipt.retention_state == "active"
        ).all()

        archived_count = 0
        expired_count = 0

        for receipt in receipts:
            # Check legal hold
            if receipt.legal_hold:
                continue  # Skip if under legal hold

            # Mark as archived or expired based on policy
            if retention_policy.get("auto_delete", True):
                receipt.retention_state = "expired"
                expired_count += 1
            else:
                receipt.retention_state = "archived"
                archived_count += 1

        try:
            self.db.commit()
            return {
                "evaluated": len(receipts),
                "archived": archived_count,
                "expired": expired_count
            }
        except Exception as exc:
            self.db.rollback()
            logger.error("Failed to update retention states: %s", exc)
            return {"evaluated": 0, "archived": 0, "expired": 0, "error": str(exc)}


class MetaAuditService:
    """
    Meta-audit service per FR-9.

    Responsibilities:
        - Generate meta-receipts for access operations
        - Store meta-receipts via same ingestion path
    """

    def __init__(self, db: Session):
        """Initialize meta-audit service."""
        self.db = db

    def create_meta_receipt(self, access_event: Dict[str, Any]) -> str:
        """
        Create meta-receipt for access operation.

        Args:
            access_event: Access event dict

        Returns:
            Meta-receipt identifier
        """
        try:
            from .database.models import MetaReceipt
        except ImportError:
            from database.models import MetaReceipt

        access_event_id = str(uuid4())

        meta_receipt = MetaReceipt(
            access_event_id=UUID(access_event_id),
            requester_actor_id=access_event.get("requester_actor_id"),
            actor_type=access_event.get("actor_type"),
            requester_role=access_event.get("requester_role"),
            tenant_ids=access_event.get("tenant_ids", []),
            plane=access_event.get("plane"),
            environment=access_event.get("environment"),
            timestamp=access_event.get("timestamp", datetime.utcnow()),
            query_scope=access_event.get("query_scope"),
            decision=access_event.get("decision", "success"),
            receipt_count=access_event.get("receipt_count")
        )

        try:
            self.db.add(meta_receipt)
            self.db.commit()
            return access_event_id
        except Exception as exc:
            self.db.rollback()
            logger.error("Failed to create meta-receipt: %s", exc)
            raise


# Phase 11: DLQ Service

class DLQService:
    """
    Dead Letter Queue service per FR-2.

    Responsibilities:
        - Invalid receipt storage (JSONL format)
        - DLQ retention policy (configurable per tenant via Data Governance)
        - DLQ replay functionality
    """

    def __init__(self, db: Session):
        """Initialize DLQ service."""
        self.db = db
        self.default_dlq_retention_days = 30  # Default fallback
    
    async def get_dlq_retention_days(self, tenant_id: Optional[str] = None) -> int:
        """
        Get DLQ retention days for tenant from Data Governance.
        
        Args:
            tenant_id: Tenant identifier (optional)
            
        Returns:
            Retention days (default: 30 if tenant_id not provided or policy not found)
        """
        if not tenant_id:
            return self.default_dlq_retention_days
        
        try:
            # Query Data Governance for DLQ retention policy
            retention_policy = await get_retention_policy(tenant_id)
            if retention_policy:
                # Check if retention policy has DLQ-specific retention
                dlq_retention = retention_policy.get("dlq_retention_days")
                if dlq_retention:
                    return int(dlq_retention)
                # Fallback to general retention period if available
                retention_months = retention_policy.get("retention_period_months")
                if retention_months:
                    # Convert months to days (approximate)
                    return int(retention_months * 30)
        except Exception as exc:
            logger.warning("Failed to get DLQ retention policy for tenant %s: %s", tenant_id, exc)
        
        return self.default_dlq_retention_days

    async def store_invalid_receipt(self, receipt: Dict[str, Any], rejection_reason: str, tenant_id: Optional[str] = None) -> str:
        """
        Store invalid receipt in DLQ.

        Args:
            receipt: Invalid receipt dict
            rejection_reason: Reason for rejection
            tenant_id: Tenant identifier (optional, extracted from receipt if not provided)

        Returns:
            DLQ entry identifier
        """
        dlq_entry_id = uuid4()
        
        # Extract tenant_id from receipt if not provided
        if not tenant_id:
            tenant_id = receipt.get("tenant_id")
        
        # Get retention days from Data Governance (configurable per tenant)
        retention_days = await self.get_dlq_retention_days(tenant_id)
        
        timestamp = datetime.utcnow()
        expires_at = timestamp + timedelta(days=retention_days)
        
        dlq_entry = DLQEntry(
            dlq_entry_id=dlq_entry_id,
            tenant_id=tenant_id,
            receipt=receipt,
            rejection_reason=rejection_reason,
            timestamp=timestamp,
            expires_at=expires_at
        )

        try:
            self.db.add(dlq_entry)
            self.db.commit()
            logger.info("DLQ entry created: %s, reason: %s", str(dlq_entry_id), rejection_reason)
            return str(dlq_entry_id)
        except Exception as exc:
            self.db.rollback()
            logger.error("Failed to store DLQ entry: %s", exc)
            # Fallback to logging if database write fails
            logger.warning("DLQ Entry (fallback log): receipt_id=%s, reason=%s", 
                          receipt.get("receipt_id"), rejection_reason)
            return str(dlq_entry_id)

    def get_dlq_entries(self, tenant_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get DLQ entries for replay.

        Args:
            tenant_id: Tenant identifier (optional)
            limit: Maximum number of entries

        Returns:
            List of DLQ entry dicts
        """
        query = self.db.query(DLQEntry).filter(DLQEntry.expires_at > datetime.utcnow())
        
        if tenant_id:
            query = query.filter(DLQEntry.tenant_id == tenant_id)
        
        entries = query.order_by(DLQEntry.timestamp.desc()).limit(limit).all()
        
        return [
            {
                "dlq_entry_id": str(entry.dlq_entry_id),
                "tenant_id": entry.tenant_id,
                "receipt": entry.receipt,
                "rejection_reason": entry.rejection_reason,
                "timestamp": entry.timestamp.isoformat(),
                "expires_at": entry.expires_at.isoformat(),
                "created_at": entry.created_at.isoformat()
            }
            for entry in entries
        ]

    def replay_dlq_entry(self, dlq_entry_id: str) -> Tuple[bool, Optional[str]]:
        """
        Replay DLQ entry after fixing validation issues.

        Args:
            dlq_entry_id: DLQ entry identifier

        Returns:
            Tuple of (success, error_message)
        """
        # In production, this would retrieve from DLQ and re-ingest
        # For now, return success (implementation would use proper DLQ storage)
        return True, None
