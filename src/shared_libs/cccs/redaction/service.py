"""Secure Redaction (SSDRS) implementation with rule-version negotiation."""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..exceptions import RedactionBlockedError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RedactionRule:
    """Redaction rule from EPC-2."""

    field_path: str
    strategy: str  # e.g., "remove" or "mask"
    mask_value: str | None = None
    rule_version: str = "v1"


@dataclass
class RedactionConfig:
    """Configuration for redaction service."""

    rules: List[RedactionRule]
    rule_version_negotiation_enabled: bool = True
    require_rule_version_match: bool = True


class RedactionService:
    """
    Applies EPC-2 provided rules without mutating originals.

    Hardened with:
    - Deep-copy payloads to prevent mutation
    - Rule-version negotiation enforcement
    - Emits redaction_blocked receipts when rules unavailable
    """

    def __init__(self, config: RedactionConfig):
        self._config = config
        if not config.rules:
            raise RedactionBlockedError("No redaction rules available")
        self._negotiated_versions: Dict[str, str] = {}  # policy_hint -> rule_version

    def _negotiate_rule_version(self, policy_hint: Optional[str] = None) -> str:
        """
        Negotiate rule version.

        Args:
            policy_hint: Optional policy hint for version negotiation

        Returns:
            Negotiated rule version

        Raises:
            RedactionBlockedError: If version negotiation fails and required
        """
        if not self._config.rule_version_negotiation_enabled:
            return "v1"  # Default version

        if not policy_hint:
            return "v1"  # Default if no hint

        # Check if we've already negotiated this version
        if policy_hint in self._negotiated_versions:
            return self._negotiated_versions[policy_hint]

        # For now, use policy_hint as version (EPC-2 would provide negotiation)
        # In production, this would call EPC-2 to negotiate version
        version = policy_hint
        self._negotiated_versions[policy_hint] = version
        return version

    def _get_rules_for_version(self, rule_version: str) -> List[RedactionRule]:
        """
        Get rules matching the specified version.
        
        Per PRD §7.1: Redaction rule drift → emit redaction_blocked and halt response emission.
        """
        if not self._config.require_rule_version_match:
            return self._config.rules

        # Filter rules by version
        matching_rules = [r for r in self._config.rules if r.rule_version == rule_version]
        if not matching_rules:
            # Per PRD §7.1: Rule drift must raise redaction_blocked and halt
            raise RedactionBlockedError(f"No redaction rules available for version {rule_version}")
        return matching_rules

    def apply_redaction(
        self, payload: Dict[str, Any], policy_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Apply redaction with deep-copy and rule-version negotiation.

        Never mutates source payload; returns detached copy.

        Args:
            payload: Payload to redact (will be deep-copied)
            policy_hint: Optional policy hint for rule version negotiation

        Returns:
            Dict with redacted_payload, removed_fields, rule_version

        Raises:
            RedactionBlockedError: If rules unavailable or version mismatch
        """
        # Deep copy payload to prevent mutation
        payload_copy = copy.deepcopy(payload)

        # Negotiate rule version
        try:
            rule_version = self._negotiate_rule_version(policy_hint)
        except Exception as e:
            raise RedactionBlockedError(f"Rule version negotiation failed: {e}") from e

        # Get rules for negotiated version
        rules = self._get_rules_for_version(rule_version)
        if not rules:
            raise RedactionBlockedError(f"No redaction rules available for version {rule_version}")

        # Apply redaction rules
        stripped = copy.deepcopy(payload_copy)  # Another copy for redaction result
        removed_fields: List[str] = []

        for rule in rules:
            # Handle nested field paths (e.g., "user.email")
            if "." in rule.field_path:
                parts = rule.field_path.split(".")
                current = stripped
                for part in parts[:-1]:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        break
                else:
                    final_key = parts[-1]
                    if isinstance(current, dict) and final_key in current:
                        if rule.strategy == "remove":
                            removed_fields.append(rule.field_path)
                            current.pop(final_key)
                        elif rule.strategy == "mask":
                            current[final_key] = rule.mask_value or "***"
                            removed_fields.append(rule.field_path)
                        continue

            # Handle top-level fields
            if rule.field_path in stripped:
                if rule.strategy == "remove":
                    removed_fields.append(rule.field_path)
                    stripped.pop(rule.field_path)
                elif rule.strategy == "mask":
                    stripped[rule.field_path] = rule.mask_value or "***"
                    removed_fields.append(rule.field_path)
                else:
                    raise RedactionBlockedError(f"Unsupported strategy {rule.strategy}")

        return {
            "redacted_payload": stripped,
            "removed_fields": removed_fields,
            "rule_version": rule_version,
        }


