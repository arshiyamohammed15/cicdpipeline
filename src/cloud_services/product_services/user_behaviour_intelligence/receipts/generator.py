"""
Receipt Generation Service for UBI Module (EPC-9).

What: Generates receipts for configuration changes and high-severity signals
Why: Record operations for auditability per PRD FR-13
Reads/Writes: Receipt generation (no storage)
Contracts: Canonical receipt schema, ERIS PRD Section 8.1
Risks: Receipt schema violations
"""

import logging
import uuid
import hashlib
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ReceiptGenerator:
    """
    Receipt generator for UBI operations.

    Per UBI PRD FR-13:
    - Receipt schema validation (canonical schema)
    - Receipt generation for configuration changes and high-severity signals
    - Gate ID: "ubi"
    - Receipt signing (cryptographic signature)
    """

    GATE_ID = "ubi"
    SCHEMA_VERSION = "1.0.0"

    def generate_config_receipt(
        self,
        tenant_id: str,
        config_version: str,
        actor_id: str,
        actor_type: str,
        decision_status: str,  # "pass" or "warn"
        decision_rationale: str,
        inputs: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate receipt for configuration change.

        Args:
            tenant_id: Tenant identifier
            config_version: Configuration version
            actor_id: Actor identifier (IAM identity)
            actor_type: Actor type (human or service)
            decision_status: Decision status ("pass" for success, "warn" for failure)
            decision_rationale: Human-readable explanation
            inputs: Operation inputs
            result: Operation results

        Returns:
            Receipt dictionary
        """
        receipt_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        monotonic_ms = int(time.perf_counter() * 1000)
        
        # Generate snapshot hash (placeholder - would be actual hash of config)
        snapshot_hash = hashlib.sha256(config_version.encode()).hexdigest()
        
        receipt = {
            "receipt_id": receipt_id,
            "gate_id": self.GATE_ID,
            "schema_version": self.SCHEMA_VERSION,
            "policy_version_ids": [config_version],
            "snapshot_hash": f"sha256:{snapshot_hash}",
            "timestamp_utc": now.isoformat(),
            "timestamp_monotonic_ms": monotonic_ms,
            "evaluation_point": "config",
            "inputs": inputs,
            "decision": {
                "status": decision_status,
                "rationale": decision_rationale,
                "badges": []
            },
            "result": result,
            "actor": {
                "repo_id": tenant_id,  # Using tenant_id as repo_id
                "type": actor_type
            },
            "evidence_handles": [],
            "degraded": False,
            "signature": "base64:PLACEHOLDER_SIGNATURE",  # Placeholder - would be cryptographic signature
            "tenant_id": tenant_id
        }
        
        return receipt

    def generate_signal_receipt(
        self,
        signal: Dict[str, Any],
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Generate receipt for high-severity signal.

        Args:
            signal: BehaviouralSignal dictionary
            tenant_id: Tenant identifier

        Returns:
            Receipt dictionary
        """
        receipt_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        monotonic_ms = int(time.perf_counter() * 1000)
        
        receipt = {
            "receipt_id": receipt_id,
            "gate_id": self.GATE_ID,
            "schema_version": self.SCHEMA_VERSION,
            "policy_version_ids": [],
            "snapshot_hash": "sha256:0" * 64,  # Placeholder
            "timestamp_utc": now.isoformat(),
            "timestamp_monotonic_ms": monotonic_ms,
            "evaluation_point": "post-deploy",  # Placeholder
            "inputs": {
                "signal_id": signal.get("signal_id"),
                "dimension": signal.get("dimension"),
                "actor_scope": signal.get("actor_scope")
            },
            "decision": {
                "status": "pass",  # Signal generation is always "pass"
                "rationale": f"Behavioural signal generated: {signal.get('signal_type')} - {signal.get('severity')}",
                "badges": []
            },
            "result": {
                "signal_id": signal.get("signal_id"),
                "severity": signal.get("severity"),
                "score": signal.get("score")
            },
            "actor": {
                "repo_id": tenant_id,
                "type": "service"  # UBI service identity
            },
            "evidence_handles": signal.get("evidence_refs", []),
            "degraded": False,
            "signature": "base64:PLACEHOLDER_SIGNATURE",
            "tenant_id": tenant_id
        }
        
        return receipt

