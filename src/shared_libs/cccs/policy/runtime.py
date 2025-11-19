"""Policy Runtime & Evaluation Engine (PREE) implementation."""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
import logging
from dataclasses import dataclass
from typing import Sequence

from ..exceptions import PolicyUnavailableError
from ..types import PolicyDecision, PolicyRule, PolicySnapshot

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PolicyConfig:
    """Offline policy validation configuration."""

    signing_secrets: Sequence[bytes]
    rule_version_negotiation_enabled: bool = True


class PolicyRuntime:
    """
    Loads signed snapshots and evaluates policies entirely offline.

    Per PRD §9: GSMD snapshots must be validated without network access.
    We model the EPC-3 signature chain via HMAC secrets supplied in the configuration.
    """

    def __init__(self, config: PolicyConfig):
        if not config.signing_secrets:
            raise ValueError("PolicyConfig.signing_secrets must not be empty")
        self._config = config
        self._snapshot: PolicySnapshot | None = None
        self._negotiated_versions: dict[str, str] = {}

    def _serialize(self, payload: dict) -> bytes:
        return json.dumps(payload, sort_keys=True).encode("utf-8")

    def _is_signature_valid(self, payload: dict, signature: str) -> bool:
        serialized = self._serialize(payload)
        for secret in self._config.signing_secrets:
            expected = hmac.new(secret, serialized, hashlib.sha256).hexdigest()
            if hmac.compare_digest(expected, signature):
                return True
        return False

    def load_snapshot(self, payload: dict, signature: str) -> PolicySnapshot:
        """Validates and stores a GSMD snapshot using offline trust anchors."""
        payload_copy = copy.deepcopy(payload)
        if not self._is_signature_valid(payload_copy, signature):
            raise PolicyUnavailableError("Policy snapshot signature invalid (offline validation)")

        rules = []
        for rule_data in payload_copy.get("rules", []):
            rules.append(
                PolicyRule(
                    rule_id=rule_data["rule_id"],
                    priority=int(rule_data.get("priority", 100)),
                    conditions=rule_data.get("conditions", {}),
                    decision=rule_data.get("decision", "deny"),
                    rationale=rule_data.get("rationale", "unspecified"),
                )
            )
        rules.sort(key=lambda r: r.priority, reverse=True)

        snapshot_hash = f"sha256:{hashlib.sha256(self._serialize(payload_copy)).hexdigest()}"
        snapshot = PolicySnapshot(
            module_id=payload_copy["module_id"],
            version=str(payload_copy["version"]),
            rules=tuple(rules),
            signature=signature,
            snapshot_hash=snapshot_hash,
        )
        self._snapshot = snapshot
        return snapshot

    def evaluate(self, module_id: str, inputs: dict) -> PolicyDecision:
        """Evaluates policy locally without any synchronous network calls."""
        if self._snapshot is None or self._snapshot.module_id != module_id:
            raise PolicyUnavailableError("Policy snapshot unavailable")

        inputs_copy = copy.deepcopy(inputs)
        if self._config.rule_version_negotiation_enabled and module_id not in self._negotiated_versions:
            self._negotiated_versions[module_id] = self._snapshot.version

        matching_rule = next((rule for rule in self._snapshot.rules if self._rule_matches(rule, inputs_copy)), None)
        if matching_rule is None:
            return PolicyDecision(
                decision="deny",
                rationale="no_rule_matched",
                policy_version_ids=[self._snapshot.version],
                policy_snapshot_hash=self._snapshot.snapshot_hash,
            )

        return PolicyDecision(
            decision=matching_rule.decision,
            rationale=matching_rule.rationale,
            policy_version_ids=[self._snapshot.version],
            policy_snapshot_hash=self._snapshot.snapshot_hash,
        )

    @staticmethod
    def _rule_matches(rule: PolicyRule, inputs: dict) -> bool:
        if not rule.conditions:
            return True
        for key, expected in rule.conditions.items():
            value = inputs.get(key)
            if isinstance(expected, dict):
                op = expected.get("op", "eq")
                operand = expected.get("value")
                if op == "eq" and value != operand:
                    return False
                if op == "lte" and not (value <= operand):
                    return False
                if op == "gte" and not (value >= operand):
                    return False
                if op == "in" and value not in operand:
                    return False
                if op == "not_in" and value in operand:
                    return False
            elif value != expected:
                return False
        return True

    async def health_check(self) -> bool:
        """Offline evaluation always reports healthy."""
        return True

    async def close(self) -> None:
        """Nothing to close for offline evaluation."""
        return None
