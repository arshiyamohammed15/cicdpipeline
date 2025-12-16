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
        # CR-071: Index rules by condition keys for faster lookup
        self._rule_index: dict[str, list[PolicyRule]] = {}
        # CR-072: Cache evaluation results for identical inputs
        self._evaluation_cache: dict[str, PolicyDecision] = {}
        self._cache_max_size = 1000

    def _serialize(self, payload: dict) -> bytes:
        return json.dumps(payload, sort_keys=True).encode("utf-8")

    def _is_signature_valid(self, payload: dict, signature: str) -> bool:
        # CR-033: Ensure constant-time comparison to prevent timing attacks
        serialized = self._serialize(payload)
        # Compute all expected signatures first, then compare
        expected_signatures = []
        for secret in self._config.signing_secrets:
            expected = hmac.new(secret, serialized, hashlib.sha256).hexdigest()
            expected_signatures.append(expected)
        
        # Compare all signatures in constant time
        # Use hmac.compare_digest for each, but ensure we always check all
        matches = [hmac.compare_digest(expected, signature) for expected in expected_signatures]
        return any(matches)

    def load_snapshot(self, payload: dict, signature: str) -> PolicySnapshot:
        """Validates and stores a GSMD snapshot using offline trust anchors."""
        payload_copy = copy.deepcopy(payload)
        if not self._is_signature_valid(payload_copy, signature):
            raise PolicyUnavailableError("Policy snapshot signature invalid (offline validation)")

        rules = []
        for rule_data in payload_copy.get("rules", []):
            # CR-034: Validate rule priority range
            priority = rule_data.get("priority", 100)
            try:
                priority_int = int(priority)
                if priority_int < 0 or priority_int > 10000:
                    raise ValueError(f"Rule priority {priority_int} out of valid range [0, 10000]")
            except (ValueError, TypeError) as e:
                raise PolicyUnavailableError(f"Invalid rule priority: {priority}") from e
            
            rules.append(
                PolicyRule(
                    rule_id=rule_data["rule_id"],
                    priority=priority_int,
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
        # CR-071: Build index by condition keys for faster rule lookup
        self._build_rule_index(rules)
        # CR-072: Clear evaluation cache when snapshot changes
        self._evaluation_cache.clear()
        return snapshot

    def evaluate(self, module_id: str, inputs: dict) -> PolicyDecision:
        """Evaluates policy locally without any synchronous network calls."""
        if self._snapshot is None or self._snapshot.module_id != module_id:
            raise PolicyUnavailableError("Policy snapshot unavailable")

        inputs_copy = copy.deepcopy(inputs)
        if self._config.rule_version_negotiation_enabled and module_id not in self._negotiated_versions:
            self._negotiated_versions[module_id] = self._snapshot.version

        # CR-072: Check cache first
        cache_key = self._cache_key(module_id, inputs_copy)
        if cache_key in self._evaluation_cache:
            return self._evaluation_cache[cache_key]

        # CR-071: Use indexed lookup instead of linear search
        candidate_rules = self._get_candidate_rules(inputs_copy)
        matching_rule = next((rule for rule in candidate_rules if self._rule_matches(rule, inputs_copy)), None)
        
        if matching_rule is None:
            decision = PolicyDecision(
                decision="deny",
                rationale="no_rule_matched",
                policy_version_ids=[self._snapshot.version],
                policy_snapshot_hash=self._snapshot.snapshot_hash,
            )
        else:
            decision = PolicyDecision(
            decision=matching_rule.decision,
            rationale=matching_rule.rationale,
            policy_version_ids=[self._snapshot.version],
            policy_snapshot_hash=self._snapshot.snapshot_hash,
        )

        # CR-072: Cache the result
        self._cache_decision(cache_key, decision)
        return decision

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

    def _build_rule_index(self, rules: list[PolicyRule]) -> None:
        """
        CR-071: Build index of rules by condition keys for faster lookup.
        
        Creates an inverted index mapping condition keys to rules that contain them.
        This allows O(1) lookup of candidate rules instead of O(n) linear search.
        
        Args:
            rules: List of policy rules to index
        """
        self._rule_index.clear()
        for rule in rules:
            if rule.conditions:
                # Index by all condition keys
                for key in rule.conditions.keys():
                    if key not in self._rule_index:
                        self._rule_index[key] = []
                    self._rule_index[key].append(rule)
            else:
                # Rules with no conditions match everything - store separately
                if "__no_conditions__" not in self._rule_index:
                    self._rule_index["__no_conditions__"] = []
                self._rule_index["__no_conditions__"].append(rule)

    def _get_candidate_rules(self, inputs: dict) -> list[PolicyRule]:
        """
        CR-071: Get candidate rules using index instead of checking all rules.
        
        Uses the rule index to quickly find rules that might match the given inputs,
        significantly reducing the number of rules that need to be evaluated.
        
        Args:
            inputs: Policy evaluation inputs dictionary
            
        Returns:
            List of candidate rules sorted by priority (highest first)
        """
        candidate_rules = []
        input_keys = set(inputs.keys())
        
        # Get rules that match input keys
        matched_rules = set()
        for key in input_keys:
            if key in self._rule_index:
                for rule in self._rule_index[key]:
                    matched_rules.add(rule)
        
        # Add rules with no conditions (match everything)
        if "__no_conditions__" in self._rule_index:
            for rule in self._rule_index["__no_conditions__"]:
                matched_rules.add(rule)
        
        # Sort by priority (highest first) as rules are already sorted
        candidate_rules = sorted(matched_rules, key=lambda r: r.priority, reverse=True)
        
        # Fallback to all rules if index is empty (shouldn't happen, but defensive)
        if not candidate_rules and self._snapshot:
            candidate_rules = list(self._snapshot.rules)
        
        return candidate_rules

    def _cache_key(self, module_id: str, inputs: dict) -> str:
        """
        CR-072: Generate cache key for evaluation inputs.
        
        Creates a deterministic cache key from module ID and inputs for caching
        policy evaluation results.
        
        Args:
            module_id: Policy module identifier
            inputs: Policy evaluation inputs dictionary
            
        Returns:
            SHA-256 hash-based cache key string
        """
        # Create deterministic key from inputs
        inputs_str = json.dumps(inputs, sort_keys=True)
        return f"{module_id}:{hashlib.sha256(inputs_str.encode()).hexdigest()}"

    def _cache_decision(self, cache_key: str, decision: PolicyDecision) -> None:
        """
        CR-072: Cache decision result with size limit.
        
        Stores policy evaluation results in cache with FIFO eviction when cache
        size limit is reached to prevent unbounded memory growth.
        
        Args:
            cache_key: Cache key generated from inputs
            decision: Policy decision result to cache
        """
        # Limit cache size to prevent memory growth
        if len(self._evaluation_cache) >= self._cache_max_size:
            # Remove oldest entry (simple FIFO - in production could use LRU)
            oldest_key = next(iter(self._evaluation_cache))
            del self._evaluation_cache[oldest_key]
        self._evaluation_cache[cache_key] = decision

    async def close(self) -> None:
        """Nothing to close for offline evaluation."""
        # CR-072: Clear cache on close
        self._evaluation_cache.clear()
        self._rule_index.clear()
        return None
