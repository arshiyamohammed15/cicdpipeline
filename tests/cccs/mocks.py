from __future__ import annotations
"""
Mock adapters for CCCS testing.

These mocks simulate EPC-1, EPC-3, EPC-13, PM-7, and EPC-11 services for unit testing.
"""


import hashlib
import json
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock

from src.shared_libs.cccs.adapters.epc1_adapter import EPC1IdentityAdapter
from src.shared_libs.cccs.adapters.epc3_adapter import EPC3PolicyAdapter
from src.shared_libs.cccs.adapters.epc11_adapter import EPC11SigningAdapter
from src.shared_libs.cccs.adapters.epc13_adapter import EPC13BudgetAdapter
from src.shared_libs.cccs.adapters.pm7_adapter import PM7ReceiptAdapter
from src.shared_libs.cccs.types import ActorBlock, ActorContext, PolicyDecision, PolicySnapshot


class MockEPC1Adapter(EPC1IdentityAdapter):
    """Mock EPC-1 adapter for testing."""

    def __init__(self, config):
        # Don't call super().__init__ to avoid HTTP client initialization
        self._config = config
        self._health_status = True
        self._fail_verify = False
        self._fail_provenance = False

    async def verify_identity(self, context: ActorContext, token: Optional[str] = None) -> Dict[str, Any]:
        if self._fail_verify:
            raise Exception("EPC-1 verification failed")
        return {
            "actor_id": f"actor-{context.user_id}",
            "user_id": context.user_id,
            "tenant_id": context.tenant_id,
        }

    async def get_actor_provenance(self, context: ActorContext) -> Dict[str, Any]:
        if self._fail_provenance:
            raise Exception("EPC-1 provenance failed")
        return {
            "provenance_signature": f"sig-{context.user_id}",
            "normalization_version": "v1",
            "warnings": [],
        }

    async def resolve_actor(self, context: ActorContext) -> ActorBlock:
        verify_result = await self.verify_identity(context)
        provenance_result = await self.get_actor_provenance(context)
        return ActorBlock(
            actor_id=verify_result["actor_id"],
            actor_type=context.actor_type,
            session_id=context.session_id,
            provenance_signature=provenance_result["provenance_signature"],
            normalization_version=provenance_result["normalization_version"],
            warnings=tuple(provenance_result.get("warnings", [])),
        )

    async def health_check(self) -> bool:
        return self._health_status

    async def close(self) -> None:
        pass


class MockEPC3Adapter(EPC3PolicyAdapter):
    """Mock EPC-3 adapter for testing."""

    def __init__(self, config):
        self._config = config
        self._health_status = True
        self._fail_signature = False
        self._fail_evaluation = False
        self._snapshots: Dict[str, PolicySnapshot] = {}

    def _hash_payload(self, payload: dict) -> str:
        blob = json.dumps(payload, sort_keys=True).encode()
        digest = hashlib.sha256(blob).hexdigest()
        return f"sha256:{digest}"

    async def validate_snapshot_signature(
        self, payload: dict, signature: str, public_key_id: Optional[str] = None
    ) -> bool:
        if self._fail_signature:
            return False
        # Simple mock: accept any signature that's not "invalid"
        return signature != "invalid"

    async def load_snapshot(
        self, payload: dict, signature: str, public_key_id: Optional[str] = None
    ) -> PolicySnapshot:
        if not await self.validate_snapshot_signature(payload, signature, public_key_id):
            raise Exception("Policy snapshot signature invalid")

        from src.shared_libs.cccs.types import PolicyRule

        rules = []
        for rule_data in payload.get("rules", []):
            rules.append(
                PolicyRule(
                    rule_id=rule_data["rule_id"],
                    priority=int(rule_data.get("priority", 100)),
                    conditions=rule_data.get("conditions", {}),
                    decision=rule_data.get("decision", "deny"),
                    rationale=rule_data.get("rationale", "unspecified"),
                )
            )
        rules.sort(key=lambda r: r.priority)

        snapshot = PolicySnapshot(
            module_id=payload["module_id"],
            version=str(payload["version"]),
            rules=tuple(rules),
            signature=signature,
            snapshot_hash=self._hash_payload(payload),
        )
        self._snapshots[payload["module_id"]] = snapshot
        return snapshot

    async def evaluate_policy(
        self, module_id: str, inputs: dict, snapshot_hash: Optional[str] = None
    ) -> PolicyDecision:
        if self._fail_evaluation:
            raise Exception("Policy evaluation failed")

        snapshot = self._snapshots.get(module_id)
        if not snapshot:
            return PolicyDecision(
                decision="deny",
                rationale="policy_unavailable",
                policy_version_ids=[],
                policy_snapshot_hash="",
            )

        # Simple rule matching
        for rule in snapshot.rules:
            if self._matches(rule, inputs):
                return PolicyDecision(
                    decision=rule.decision,
                    rationale=rule.rationale,
                    policy_version_ids=[snapshot.version],
                    policy_snapshot_hash=snapshot.snapshot_hash,
                )

        return PolicyDecision(
            decision="deny",
            rationale="no_rule_matched",
            policy_version_ids=[snapshot.version],
            policy_snapshot_hash=snapshot.snapshot_hash,
        )

    def _matches(self, rule, inputs: dict) -> bool:
        for key, expected in rule.conditions.items():
            value = inputs.get(key)
            if isinstance(expected, dict):
                op = expected.get("op", "eq")
                operand = expected.get("value")
                if op == "eq" and value != operand:
                    return False
                elif op == "lte" and value > operand:
                    return False
                elif op == "gte" and value < operand:
                    return False
                elif op == "in" and value not in operand:
                    return False
            elif value != expected:
                return False
        return True

    async def negotiate_rule_version(
        self, module_id: str, requested_version: Optional[str] = None
    ) -> str:
        return requested_version or "v1"

    async def health_check(self) -> bool:
        return self._health_status

    async def close(self) -> None:
        pass


class MockEPC13Adapter(EPC13BudgetAdapter):
    """Mock EPC-13 adapter for testing."""

    def __init__(self, config):
        self._config = config
        self._health_status = True
        self._fail_check = False
        self._budget_state: Dict[str, float] = {}
        self._default_capacity = 100.0

    async def check_budget(
        self, action_id: str, cost: float, tenant_id: Optional[str] = None
    ) -> Any:
        if self._fail_check:
            from src.shared_libs.cccs.exceptions import BudgetExceededError
            if self._config.default_deny_on_unavailable:
                raise BudgetExceededError("EPC-13 unavailable, denying by default")
            raise Exception("EPC-13 unavailable")

        if action_id not in self._budget_state:
            self._budget_state[action_id] = self._default_capacity

        if cost > self._budget_state[action_id]:
            from src.shared_libs.cccs.exceptions import BudgetExceededError

            raise BudgetExceededError(f"Budget exceeded for {action_id}")

        self._budget_state[action_id] -= cost
        from src.shared_libs.cccs.types import BudgetDecision

        return BudgetDecision(
            allowed=True,
            reason="budget_available",
            remaining=self._budget_state[action_id],
        )

    async def persist_budget_snapshot(
        self, budget_data: Dict[str, Any], tenant_id: Optional[str] = None
    ) -> str:
        return f"snapshot-{len(budget_data)}"

    async def health_check(self) -> bool:
        return self._health_status

    async def close(self) -> None:
        pass


class MockEPC11Adapter(EPC11SigningAdapter):
    """Mock EPC-11 adapter for testing."""

    def __init__(self, config):
        self._config = config
        self._health_status = True
        self._fail_sign = False

    async def sign_receipt(
        self, receipt_payload: Dict[str, Any], key_id: Optional[str] = None
    ) -> str:
        if self._fail_sign:
            raise Exception("EPC-11 signing failed")
        # Generate deterministic mock signature
        blob = json.dumps(receipt_payload, sort_keys=True).encode()
        digest = hashlib.sha256(blob).hexdigest()
        return f"ed25519:{digest[:64]}"

    async def verify_signature(
        self, payload: Dict[str, Any], signature: str, key_id: Optional[str] = None
    ) -> bool:
        # Verify mock signature
        expected = await self.sign_receipt(payload, key_id)
        return signature == expected

    async def health_check(self) -> bool:
        return self._health_status

    async def close(self) -> None:
        pass


class MockPM7Adapter(PM7ReceiptAdapter):
    """Mock PM-7 adapter for testing."""

    def __init__(self, config):
        self._config = config
        self._health_status = True
        self._fail_index = False
        self._indexed_receipts: list[Dict[str, Any]] = []

    async def index_receipt(self, receipt: Dict[str, Any]) -> Dict[str, Any]:
        if self._fail_index:
            raise Exception("PM-7 indexing failed")
        self._indexed_receipts.append(receipt)
        return {
            "receipt_id": receipt.get("receipt_id"),
            "merkle_root": f"root-{len(self._indexed_receipts)}",
            "batch_id": f"batch-{len(self._indexed_receipts)}",
        }

    async def index_batch(
        self, receipts: list[Dict[str, Any]], batch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if self._fail_index:
            raise Exception("PM-7 batch indexing failed")
        self._indexed_receipts.extend(receipts)
        return {
            "batch_id": batch_id or f"batch-{len(self._indexed_receipts)}",
            "merkle_root": f"root-{len(self._indexed_receipts)}",
            "receipt_count": len(receipts),
        }

    async def generate_merkle_proof(
        self, receipt_id: str, batch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return {
            "receipt_id": receipt_id,
            "path": ["node1", "node2"],
            "root": "merkle-root",
            "leaf_hash": f"hash-{receipt_id}",
        }

    async def health_check(self) -> bool:
        return self._health_status

    async def close(self) -> None:
        pass

