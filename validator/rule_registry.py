"""
Constitution rule lookup utilities.

This module centralizes access to constitution rule metadata so callers never
need to hardcode rule numbers. It loads the canonical rule data from
`config/constitution_rules.json`, applies a small set of aliases for legacy
rule names, and exposes helpers for building consistent `Violation` objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Dict, Optional

BASE_DIR = Path(__file__).resolve().parents[1]
CONSTITUTION_PATH = BASE_DIR / "config" / "constitution_rules.json"


@dataclass(frozen=True)
class RuleMetadata:
    """Container for core constitution rule attributes."""

    number: int
    title: str
    category: str
    priority: str

    @property
    def rule_id(self) -> str:
        """Return the canonical rule identifier string."""
        return f"rule_{self.number:03d}"


def _normalize(text: str) -> str:
    """Normalize text for fuzzy lookups (lowercase, alphanumeric only)."""
    return "".join(ch.lower() for ch in text if ch.isalnum())


@lru_cache(maxsize=1)
def _load_rules_index() -> Dict[str, RuleMetadata]:
    """Load constitution rule metadata and index by normalized title."""
    if not CONSTITUTION_PATH.exists():
        raise FileNotFoundError(
            f"Constitution rules JSON not found at {CONSTITUTION_PATH}"
        )

    with CONSTITUTION_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    rules: Dict[str, RuleMetadata] = {}
    for entry in data.get("rules", {}).values():
        metadata = RuleMetadata(
            number=int(entry["rule_number"]),
            title=entry["title"],
            category=entry["category"],
            priority=entry["priority"],
        )
        rules[_normalize(metadata.title)] = metadata
    return rules


def _alias_map() -> Dict[str, str]:
    """Return mapping of legacy rule names to canonical titles."""
    aliases = {
        "architectureconsistency": "Make All 20 Modules Look the Same",
        "makeall18moduleslookthesame": "Make All 20 Modules Look the Same",
        "codereviewreadiness": "Conduct Comprehensive Test Reviews",
        "collaborationstandards": "Build for Real Team Work",
        "functionlength": "Small, Clear Functions",
        "keepgoodrecordskeepgoodlogs": "Keep Good Logs",
        "namingconventions": "Consistent Naming",
    }
    index = {}
    for legacy, canonical in aliases.items():
        index[_normalize(legacy)] = _normalize(canonical)
    return index


ALIASES = _alias_map()


def slugify_rule_name(name: str) -> str:
    """Generate a slug suitable for use as a rule identifier fallback."""
    slug = re.sub(r"[^a-z0-9]+", "-", _normalize(name))
    return slug.strip("-") or "unspecified-rule"


def get_rule_metadata(name: str) -> Optional[RuleMetadata]:
    """
    Retrieve rule metadata by title or alias.

    Args:
        name: Human-readable rule title or known alias.

    Returns:
        RuleMetadata if found, otherwise None.
    """
    if not name:
        return None

    normalized = _normalize(name)
    index = _load_rules_index()

    if normalized in index:
        return index[normalized]

    alias_key = ALIASES.get(normalized)
    if alias_key and alias_key in index:
        return index[alias_key]

    # Fallback: exact substring match
    matches = [
        metadata for key, metadata in index.items() if normalized in key
    ]
    if len(matches) == 1:
        return matches[0]

    return None


def require_rule_metadata(name: str) -> RuleMetadata:
    """
    Retrieve rule metadata or raise a descriptive error when unavailable.

    Args:
        name: Human-readable rule title or alias.

    Returns:
        RuleMetadata

    Raises:
        KeyError: If the rule cannot be resolved to constitution metadata.
    """
    metadata = get_rule_metadata(name)
    if metadata is None:
        raise KeyError(f"Unable to resolve constitution rule '{name}'.")
    return metadata


def rule_fields(name: str) -> Dict[str, object]:
    """
    Return a dictionary of rule identifiers suitable for Violation kwargs.

    Args:
        name: Human-readable rule title or alias.

    Returns:
        Dict containing rule_id, rule_number, rule_name, and category.
    """
    metadata = require_rule_metadata(name)
    return {
        "rule_id": metadata.rule_id,
        "rule_number": metadata.number,
        "rule_name": metadata.title,
        "category": metadata.category,
    }


def fallback_rule_fields(name: str, category: Optional[str] = None) -> Dict[str, object]:
    """
    Provide rule identifier fields for unmapped/internal rules.

    Args:
        name: Display name for the rule.
        category: Optional category to attach.

    Returns:
        Dict with stable rule identifier fields.
    """
    return {
        "rule_id": f"rule:{slugify_rule_name(name)}",
        "rule_number": None,
        "rule_name": name,
        "category": category,
    }
