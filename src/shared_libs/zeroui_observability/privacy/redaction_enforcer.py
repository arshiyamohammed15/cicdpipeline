"""
Redaction enforcer for ZeroUI Observability Layer.

Wraps CCCS SSDRS and integrates with EPC-2 for policy-driven redaction.
Computes fingerprints after redaction per PRD requirements.
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from ...cccs.redaction.service import RedactionService, RedactionConfig, RedactionRule
    from ...cccs.exceptions import RedactionBlockedError
    CCCS_AVAILABLE = True
except ImportError:
    CCCS_AVAILABLE = False
    RedactionBlockedError = Exception  # type: ignore

logger = logging.getLogger(__name__)

# Deny patterns file
_DENY_PATTERNS_FILE = Path(__file__).parent / "deny_patterns.json"

# Field deny list
_FIELD_DENY_LIST = [
    "raw_input", "raw_output", "raw_message", "raw_error", "raw_stack",
    "raw_code", "raw_content", "password", "passwd", "pwd", "secret",
    "api_key", "apikey", "access_token", "refresh_token", "private_key",
    "privkey", "credential", "credentials", "ssn", "social_security_number",
    "credit_card", "card_number", "email_address", "phone_number",
    "full_name", "address"
]


@dataclass
class RedactionResult:
    """Result of redaction enforcement."""

    redacted_payload: Dict[str, Any]
    removed_fields: List[str]
    blocked_fields: List[str]
    fingerprints: Dict[str, str]
    redaction_applied: bool
    policy_version: str


class RedactionEnforcer:
    """
    Enforces redaction policy for observability telemetry.

    Integrates with:
    - CCCS SSDRS for rule-based redaction
    - EPC-2 for policy-driven redaction (future)
    - Deny patterns for content detection
    """

    def __init__(
        self,
        use_cccs: bool = True,
        deny_patterns_file: Optional[Path] = None,
    ):
        """
        Initialize redaction enforcer.

        Args:
            use_cccs: Whether to use CCCS SSDRS for redaction
            deny_patterns_file: Path to deny patterns JSON file
        """
        self._use_cccs = use_cccs and CCCS_AVAILABLE
        self._deny_patterns_file = deny_patterns_file or _DENY_PATTERNS_FILE
        self._deny_patterns: Dict[str, List[str]] = {}
        self._cccs_service: Optional[RedactionService] = None

        # Load deny patterns
        self._load_deny_patterns()

        # Initialize CCCS service if available
        if self._use_cccs:
            self._init_cccs_service()

    def _load_deny_patterns(self) -> None:
        """Load deny patterns from JSON file."""
        if not self._deny_patterns_file.exists():
            logger.warning(f"Deny patterns file not found: {self._deny_patterns_file}")
            return

        try:
            with open(self._deny_patterns_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                patterns_data = data.get("patterns", {})
                # Extract regex arrays from each category
                self._deny_patterns = {}
                for category, category_data in patterns_data.items():
                    if isinstance(category_data, dict) and "regex" in category_data:
                        self._deny_patterns[category] = category_data["regex"]
                    elif isinstance(category_data, list):
                        # Handle direct list format
                        self._deny_patterns[category] = category_data
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load deny patterns: {e}")

    def _init_cccs_service(self) -> None:
        """Initialize CCCS redaction service."""
        try:
            # Create default rules from deny patterns
            rules = []
            for category, patterns in self._deny_patterns.items():
                for pattern in patterns:
                    # Create rule to remove fields matching pattern
                    rules.append(
                        RedactionRule(
                            field_path=pattern,  # Pattern as field path hint
                            strategy="remove",
                            rule_version="v1"
                        )
                    )

            config = RedactionConfig(
                rules=rules,
                rule_version_negotiation_enabled=True,
                require_rule_version_match=False  # Allow flexible matching
            )
            self._cccs_service = RedactionService(config)
        except Exception as e:
            logger.error(f"Failed to initialize CCCS service: {e}")
            self._cccs_service = None

    def _check_deny_patterns(self, content: str) -> List[str]:
        """
        Check content against deny patterns.

        Args:
            content: Content to check

        Returns:
            List of matched pattern categories
        """
        matched = []
        for category, patterns in self._deny_patterns.items():
            for pattern in patterns:
                try:
                    if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                        matched.append(f"{category}:{pattern[:50]}")
                except re.error as e:
                    logger.warning(f"Invalid regex pattern {pattern}: {e}")
        return matched

    def _check_field_deny_list(self, payload: Dict[str, Any]) -> List[str]:
        """
        Check payload for deny-listed field names.

        Args:
            payload: Payload to check

        Returns:
            List of deny-listed fields found
        """
        found = []
        for field in _FIELD_DENY_LIST:
            if field in payload:
                found.append(field)
        return found

    def _compute_fingerprint(self, content: Any) -> str:
        """
        Compute SHA-256 fingerprint of content.

        Args:
            content: Content to fingerprint (will be JSON-serialized)

        Returns:
            Hex-encoded SHA-256 hash (64 characters)
        """
        if content is None:
            return ""
        try:
            # Serialize to JSON for consistent hashing
            json_str = json.dumps(content, sort_keys=True, separators=(",", ":"))
            hash_obj = hashlib.sha256(json_str.encode("utf-8"))
            return hash_obj.hexdigest()
        except (TypeError, ValueError) as e:
            logger.warning(f"Failed to compute fingerprint: {e}")
            return ""

    def enforce(
        self,
        payload: Dict[str, Any],
        policy_hint: Optional[str] = None,
        compute_fingerprints: bool = True,
    ) -> RedactionResult:
        """
        Enforce redaction policy on payload.

        Args:
            payload: Payload to redact
            policy_hint: Optional policy hint for rule version negotiation
            compute_fingerprints: Whether to compute fingerprints after redaction

        Returns:
            RedactionResult with redacted payload and metadata
        """
        # Deep copy to avoid mutation
        import copy
        payload_copy = copy.deepcopy(payload)

        removed_fields: List[str] = []
        blocked_fields: List[str] = []
        redaction_applied = False

        # Step 1: Check field deny list
        deny_list_fields = self._check_field_deny_list(payload_copy)
        for field in deny_list_fields:
            if field in payload_copy:
                blocked_fields.append(field)
                del payload_copy[field]
                redaction_applied = True

        # Step 2: Check content against deny patterns (field-by-field)
        for key, value in list(payload_copy.items()):
            if isinstance(value, str):
                # Check if field value matches deny patterns
                matched_patterns = self._check_deny_patterns(value)
                if matched_patterns:
                    blocked_fields.extend([f"{key}:{p}" for p in matched_patterns])
                    removed_fields.append(key)
                    del payload_copy[key]
                    redaction_applied = True
            elif isinstance(value, dict):
                # Recursively check nested objects
                try:
                    nested_str = json.dumps(value)
                    nested_matched = self._check_deny_patterns(nested_str)
                    if nested_matched:
                        # Remove entire nested object if it contains deny patterns
                        blocked_fields.extend([f"{key}:{p}" for p in nested_matched])
                        removed_fields.append(key)
                        del payload_copy[key]
                        redaction_applied = True
                except (TypeError, ValueError):
                    pass  # Skip if can't serialize

        # Step 3: Apply CCCS redaction if available
        if self._use_cccs and self._cccs_service:
            try:
                cccs_result = self._cccs_service.apply_redaction(
                    payload_copy, policy_hint=policy_hint
                )
                payload_copy = cccs_result["redacted_payload"]
                removed_fields.extend(cccs_result["removed_fields"])
                redaction_applied = True
                policy_version = cccs_result.get("rule_version", "v1")
            except RedactionBlockedError as e:
                logger.error(f"CCCS redaction blocked: {e}")
                # Continue with basic redaction
                policy_version = "v1"
        else:
            policy_version = "v1"

        # Step 4: Compute fingerprints after redaction
        fingerprints: Dict[str, str] = {}
        if compute_fingerprints:
            # Compute fingerprints for common fields
            for field in ["message", "input", "output", "internal_state", "stack"]:
                if f"{field}_fingerprint" not in payload_copy:
                    # Don't compute if already present
                    continue
                # Fingerprints are computed after redaction per PRD
                source_field = field.replace("_fingerprint", "")
                if source_field in payload_copy:
                    fingerprints[f"{field}_fingerprint"] = self._compute_fingerprint(
                        payload_copy[source_field]
                    )

        return RedactionResult(
            redacted_payload=payload_copy,
            removed_fields=list(set(removed_fields)),
            blocked_fields=list(set(blocked_fields)),
            fingerprints=fingerprints,
            redaction_applied=redaction_applied,
            policy_version=policy_version,
        )
