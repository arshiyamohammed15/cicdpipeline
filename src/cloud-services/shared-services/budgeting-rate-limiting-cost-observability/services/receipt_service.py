"""
Receipt generation service for M35.

What: Generates canonical M27 receipts for all budget, rate limit, cost, and quota operations
Why: Provides audit trail and compliance evidence per PRD
Reads/Writes: Reads operation data, writes receipts to M27 via dependencies
Contracts: Canonical M27 receipt schema per PRD lines 3345-3563
Risks: Receipt schema mismatch, signature failures, M27 unavailability
"""

import hashlib
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal

from ..dependencies import MockM27EvidenceLedger, MockM33KeyManagement

logger = logging.getLogger(__name__)


class ReceiptService:
    """
    Receipt generation service per M35 PRD Audit Integration section.

    Generates receipts conforming to canonical M27 receipt schema.
    """

    def __init__(
        self,
        evidence_ledger: MockM27EvidenceLedger,
        key_management: MockM33KeyManagement
    ):
        """
        Initialize receipt service.

        Args:
            evidence_ledger: M27 evidence ledger for receipt storage
            key_management: M33 key management for receipt signing
        """
        self.evidence_ledger = evidence_ledger
        self.key_management = key_management

    def _generate_snapshot_hash(self, data: Dict[str, Any]) -> str:
        """
        Generate SHA-256 snapshot hash for receipt.

        Args:
            data: Data to hash

        Returns:
            SHA-256 hash in format 'sha256:hex'
        """
        data_json = json.dumps(data, sort_keys=True, default=str)
        hash_value = hashlib.sha256(data_json.encode('utf-8')).hexdigest()
        return f"sha256:{hash_value}"

    def _generate_receipt_base(
        self,
        gate_id: str,
        inputs: Dict[str, Any],
        decision: Dict[str, Any],
        result: Dict[str, Any],
        actor: Dict[str, Any],
        policy_version_ids: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Generate base receipt structure conforming to canonical M27 schema.

        Args:
            gate_id: Gate identifier (e.g., 'budget-check', 'rate-limit-check')
            inputs: Input data for the operation
            decision: Decision data (status, rationale, badges)
            result: Result data
            actor: Actor information (repo_id, user_id, machine_fingerprint)
            policy_version_ids: Optional policy version IDs

        Returns:
            Receipt dictionary (without signature)
        """
        receipt_id = str(uuid.uuid4())
        timestamp_utc = datetime.utcnow().isoformat() + 'Z'
        timestamp_monotonic_ms = int(time.monotonic() * 1000)

        # Generate snapshot hash from inputs and decision
        snapshot_data = {
            "inputs": inputs,
            "decision": decision,
            "result": result
        }
        snapshot_hash = self._generate_snapshot_hash(snapshot_data)

        receipt = {
            "receipt_id": receipt_id,
            "gate_id": gate_id,
            "policy_version_ids": policy_version_ids or [],
            "snapshot_hash": snapshot_hash,
            "timestamp_utc": timestamp_utc,
            "timestamp_monotonic_ms": timestamp_monotonic_ms,
            "inputs": inputs,
            "decision": {
                "status": decision.get("status"),
                "rationale": decision.get("rationale", ""),
                "badges": decision.get("badges", [])
            },
            "result": result,
            "actor": {
                "repo_id": actor.get("repo_id", ""),
                "user_id": actor.get("user_id"),
                "machine_fingerprint": actor.get("machine_fingerprint")
            },
            "degraded": decision.get("degraded", False),
            "evidence_handles": decision.get("evidence_handles", [])
        }

        return receipt

    def generate_budget_check_receipt(
        self,
        tenant_id: str,
        resource_type: str,
        estimated_cost: Decimal,
        allowed: bool,
        remaining_budget: Decimal,
        budget_id: str,
        enforcement_action: Optional[str],
        utilization_ratio: Optional[float],
        allocated_to_type: Optional[str] = None,
        allocated_to_id: Optional[str] = None,
        operation_context: Optional[Dict[str, Any]] = None,
        actor: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate budget check receipt per PRD lines 3380-3424.

        Args:
            tenant_id: Tenant identifier
            resource_type: Resource type
            estimated_cost: Estimated cost
            allowed: Whether operation is allowed
            remaining_budget: Remaining budget amount
            budget_id: Budget identifier
            enforcement_action: Enforcement action
            utilization_ratio: Budget utilization ratio
            allocated_to_type: Allocated to type
            allocated_to_id: Allocated to identifier
            operation_context: Operation context
            actor: Actor information

        Returns:
            Signed receipt dictionary
        """
        # Determine decision status
        if not allowed:
            decision_status = "hard_block"
        elif utilization_ratio and utilization_ratio >= 0.9:
            decision_status = "warn"
        elif utilization_ratio and utilization_ratio >= 0.8:
            decision_status = "warn"
        else:
            decision_status = "pass"

        inputs = {
            "tenant_id": tenant_id,
            "resource_type": resource_type,
            "estimated_cost": str(estimated_cost),
            "allocated_to_type": allocated_to_type,
            "allocated_to_id": allocated_to_id,
            "operation_context": operation_context or {}
        }

        decision = {
            "status": decision_status,
            "rationale": f"Budget check: {'allowed' if allowed else 'blocked'}, remaining: {remaining_budget}, utilization: {utilization_ratio or 0:.2%}",
            "badges": ["budget-check"] + (["budget-exceeded"] if not allowed else []),
            "degraded": False
        }

        result = {
            "allowed": allowed,
            "remaining_budget": str(remaining_budget),
            "budget_id": budget_id,
            "enforcement_action": enforcement_action,
            "utilization_ratio": float(utilization_ratio) if utilization_ratio else None
        }

        actor_data = actor or {
            "repo_id": "M35",
            "user_id": None,
            "machine_fingerprint": None
        }

        receipt = self._generate_receipt_base(
            gate_id="budget-check",
            inputs=inputs,
            decision=decision,
            result=result,
            actor=actor_data
        )

        # Sign receipt via M33
        receipt_json = json.dumps(receipt, sort_keys=True, default=str)
        signature = self.key_management.sign(receipt_json.encode('utf-8'))
        receipt["signature"] = signature

        # Store receipt via M27
        self.evidence_ledger.store_receipt(receipt["receipt_id"], receipt)

        logger.info(f"Generated budget check receipt {receipt['receipt_id']} for budget {budget_id}")
        return receipt

    def generate_rate_limit_check_receipt(
        self,
        tenant_id: str,
        resource_type: str,
        request_count: int,
        allowed: bool,
        remaining_requests: int,
        limit_value: int,
        policy_id: str,
        reset_time: str,
        priority: Optional[str] = None,
        resource_key: Optional[str] = None,
        actor: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate rate limit check receipt per PRD lines 3426-3469.

        Args:
            tenant_id: Tenant identifier
            resource_type: Resource type
            request_count: Request count
            allowed: Whether request is allowed
            remaining_requests: Remaining requests in window
            limit_value: Limit value
            policy_id: Policy identifier
            reset_time: Reset time (ISO 8601)
            priority: Request priority
            resource_key: Resource key
            actor: Actor information

        Returns:
            Signed receipt dictionary
        """
        decision_status = "hard_block" if not allowed else "pass"

        inputs = {
            "tenant_id": tenant_id,
            "resource_type": resource_type,
            "request_count": request_count,
            "priority": priority,
            "resource_key": resource_key
        }

        decision = {
            "status": decision_status,
            "rationale": f"Rate limit check: {'allowed' if allowed else 'blocked'}, remaining: {remaining_requests}/{limit_value}",
            "badges": ["rate-limit-check"] + (["rate-limit-exceeded"] if not allowed else []),
            "degraded": False
        }

        result = {
            "allowed": allowed,
            "remaining_requests": remaining_requests,
            "reset_time": reset_time,
            "limit_value": limit_value,
            "policy_id": policy_id
        }

        actor_data = actor or {
            "repo_id": "M35",
            "user_id": None,
            "machine_fingerprint": None
        }

        receipt = self._generate_receipt_base(
            gate_id="rate-limit-check",
            inputs=inputs,
            decision=decision,
            result=result,
            actor=actor_data
        )

        # Sign receipt via M33
        receipt_json = json.dumps(receipt, sort_keys=True, default=str)
        signature = self.key_management.sign(receipt_json.encode('utf-8'))
        receipt["signature"] = signature

        # Store receipt via M27
        self.evidence_ledger.store_receipt(receipt["receipt_id"], receipt)

        logger.info(f"Generated rate limit check receipt {receipt['receipt_id']} for policy {policy_id}")
        return receipt

    def generate_cost_recording_receipt(
        self,
        tenant_id: str,
        resource_type: str,
        cost_amount: Decimal,
        record_id: str,
        attributed_to_type: str,
        attributed_to_id: str,
        usage_quantity: Optional[Decimal] = None,
        usage_unit: Optional[str] = None,
        resource_id: Optional[str] = None,
        service_name: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        actor: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate cost recording receipt per PRD lines 3471-3516.

        Args:
            tenant_id: Tenant identifier
            resource_type: Resource type
            cost_amount: Cost amount
            record_id: Record identifier
            attributed_to_type: Attributed to type
            attributed_to_id: Attributed to identifier
            usage_quantity: Usage quantity
            usage_unit: Usage unit
            resource_id: Resource identifier
            service_name: Service name
            tags: Tags
            actor: Actor information

        Returns:
            Signed receipt dictionary
        """
        inputs = {
            "tenant_id": tenant_id,
            "resource_type": resource_type,
            "cost_amount": str(cost_amount),
            "usage_quantity": str(usage_quantity) if usage_quantity else None,
            "usage_unit": usage_unit,
            "resource_id": resource_id,
            "service_name": service_name,
            "tags": tags or {}
        }

        decision = {
            "status": "pass",
            "rationale": f"Cost recorded: {cost_amount} for {resource_type}",
            "badges": ["cost-tracking"],
            "degraded": False
        }

        result = {
            "record_id": record_id,
            "recorded_at": datetime.utcnow().isoformat() + 'Z',
            "attributed_to_type": attributed_to_type,
            "attributed_to_id": attributed_to_id
        }

        actor_data = actor or {
            "repo_id": "M35",
            "user_id": None,
            "machine_fingerprint": None
        }

        receipt = self._generate_receipt_base(
            gate_id="cost-tracking",
            inputs=inputs,
            decision=decision,
            result=result,
            actor=actor_data
        )

        # Sign receipt via M33
        receipt_json = json.dumps(receipt, sort_keys=True, default=str)
        signature = self.key_management.sign(receipt_json.encode('utf-8'))
        receipt["signature"] = signature

        # Store receipt via M27
        self.evidence_ledger.store_receipt(receipt["receipt_id"], receipt)

        logger.info(f"Generated cost recording receipt {receipt['receipt_id']} for record {record_id}")
        return receipt

    def generate_quota_allocation_receipt(
        self,
        tenant_id: str,
        resource_type: str,
        allocated_amount: Decimal,
        quota_id: str,
        allocation_type: str,
        period_start: str,
        period_end: str,
        used_amount: Decimal,
        remaining_amount: Decimal,
        max_burst_amount: Optional[Decimal] = None,
        auto_renew: bool = True,
        actor: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate quota allocation receipt per PRD lines 3518-3563.

        Args:
            tenant_id: Tenant identifier
            resource_type: Resource type
            allocated_amount: Allocated amount
            quota_id: Quota identifier
            allocation_type: Allocation type
            period_start: Period start (ISO 8601)
            period_end: Period end (ISO 8601)
            used_amount: Used amount
            remaining_amount: Remaining amount
            max_burst_amount: Max burst amount
            auto_renew: Auto renew flag
            actor: Actor information

        Returns:
            Signed receipt dictionary
        """
        inputs = {
            "tenant_id": tenant_id,
            "resource_type": resource_type,
            "allocated_amount": str(allocated_amount),
            "period_start": period_start,
            "period_end": period_end,
            "allocation_type": allocation_type,
            "max_burst_amount": str(max_burst_amount) if max_burst_amount else None,
            "auto_renew": auto_renew
        }

        decision = {
            "status": "pass",
            "rationale": f"Quota allocated: {allocated_amount} for {resource_type}",
            "badges": ["quota-management"],
            "degraded": False
        }

        result = {
            "quota_id": quota_id,
            "allocated_at": datetime.utcnow().isoformat() + 'Z',
            "used_amount": str(used_amount),
            "remaining_amount": str(remaining_amount)
        }

        actor_data = actor or {
            "repo_id": "M35",
            "user_id": None,
            "machine_fingerprint": None
        }

        receipt = self._generate_receipt_base(
            gate_id="quota-management",
            inputs=inputs,
            decision=decision,
            result=result,
            actor=actor_data
        )

        # Sign receipt via M33
        receipt_json = json.dumps(receipt, sort_keys=True, default=str)
        signature = self.key_management.sign(receipt_json.encode('utf-8'))
        receipt["signature"] = signature

        # Store receipt via M27
        self.evidence_ledger.store_receipt(receipt["receipt_id"], receipt)

        logger.info(f"Generated quota allocation receipt {receipt['receipt_id']} for quota {quota_id}")
        return receipt

