#!/usr/bin/env python3
"""
Unified rule catalog loader.

Uses docs/constitution/*.json as the single source of truth and
optionally enriches rule metadata with numeric identifiers from the
generated config/constitution_rules.json file. Provides normalized rule
lookups for validators and pre-implementation hooks so everything reads
the same catalog.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

CONFIG_CONSTITUTION_JSON = Path("config/constitution_rules.json")

# Candidate locations for constitution JSON sources, in priority order.
CANDIDATE_CONSTITUTION_DIRS = [
    Path("docs/architecture/constitution"),
    Path("docs/constitution"),
]


def _find_constitution_dir() -> Path:
    """Return the first existing constitution directory from known candidates."""
    for candidate in CANDIDATE_CONSTITUTION_DIRS:
        if candidate.exists() and candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        f"No constitution JSON directory found; checked: {', '.join(str(p) for p in CANDIDATE_CONSTITUTION_DIRS)}"
    )


def _normalize(text: str) -> str:
    """Normalize text for relaxed matching (lowercase, alnum only)."""
    return "".join(ch.lower() for ch in (text or "") if ch.isalnum())


def _normalize_category(category: str) -> str:
    """Normalize category names to snake_case-ish for consistent keys."""
    normalized = []
    for ch in category.strip():
        if ch.isalnum():
            normalized.append(ch.lower())
        elif ch in {" ", "-", "/","&"}:
            normalized.append("_")
    value = "".join(normalized).strip("_")
    return value or "unknown"


@dataclass(frozen=True)
class CatalogRule:
    """Stable representation of a constitution rule."""

    rule_number: Optional[int]
    rule_id: str
    title: str
    category: str
    priority: str
    enabled: bool
    doc_rule_id: Optional[str] = None
    description: str = ""
    raw: Dict[str, Any] = None  # original rule payload

    @property
    def normalized_title(self) -> str:
        return _normalize(self.title)


def _load_docs_rules() -> List[Dict]:
    """Load raw rules from constitution JSON directory (source of truth)."""
    rules: List[Dict] = []
    source_dir = _find_constitution_dir()

    for json_file in sorted(source_dir.glob("*.json")):
        try:
            with json_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:
            raise RuntimeError(f"Failed to parse {json_file}: {exc}") from exc

        for raw_rule in data.get("constitution_rules", []):
            if not isinstance(raw_rule, dict):
                continue
            rules.append(raw_rule)
    return rules


def _load_config_rules_by_title() -> Dict[str, Dict]:
    """
    Load rules from config/constitution_rules.json indexed by normalized title.

    The config file is treated as a generated artifact; this loader only
    enriches catalog entries and never serves as the source of truth.
    """
    if not CONFIG_CONSTITUTION_JSON.exists():
        return {}

    try:
        with CONFIG_CONSTITUTION_JSON.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:
        logger.warning("Failed to read %s: %s", CONFIG_CONSTITUTION_JSON, exc)
        return {}

    mapped: Dict[str, Dict] = {}
    for entry in data.get("rules", {}).values():
        title = entry.get("title")
        if not title:
            continue
        mapped[_normalize(title)] = entry
    return mapped


@lru_cache(maxsize=1)
def load_catalog() -> List[CatalogRule]:
    """
    Load the full catalog.

    Returns:
        List[CatalogRule]
    """
    doc_rules = _load_docs_rules()
    config_rules = _load_config_rules_by_title()

    catalog: List[CatalogRule] = []

    # Deterministic numbering fallback when config lacks an entry
    fallback_number = 1

    for raw in doc_rules:
        title = raw.get("title") or "Untitled Rule"
        norm_title = _normalize(title)
        doc_rule_id = raw.get("rule_id", "")
        enabled = bool(raw.get("enabled", True))
        priority = str(raw.get("priority") or raw.get("severity_level") or "unknown").lower()
        category = _normalize_category(raw.get("category", "unknown"))

        config_entry = config_rules.get(norm_title)
        rule_number = None
        if config_entry and isinstance(config_entry.get("rule_number"), int):
            rule_number = int(config_entry["rule_number"])
        else:
            rule_number = fallback_number
            fallback_number += 1

        rule_id = f"rule_{rule_number:03d}"

        catalog.append(CatalogRule(
            rule_number=rule_number,
            rule_id=rule_id,
            title=title,
            category=category,
            priority=priority,
            enabled=enabled,
            doc_rule_id=doc_rule_id or None,
            description=raw.get("description", ""),
            raw=raw,
        ))

    return catalog


def get_rule_by_title(title: str) -> Optional[CatalogRule]:
    """Lookup a rule by human-readable title."""
    if not title:
        return None
    norm = _normalize(title)
    for rule in load_catalog():
        if rule.normalized_title == norm:
            return rule
    return None


def get_rule_by_doc_id(doc_rule_id: str) -> Optional[CatalogRule]:
    """Lookup a rule by document rule_id (e.g., DOC-001)."""
    if not doc_rule_id:
        return None
    norm_target = _normalize(doc_rule_id)
    for rule in load_catalog():
        if rule.doc_rule_id and _normalize(rule.doc_rule_id) == norm_target:
            return rule
    return None


def get_catalog_rules() -> List[CatalogRule]:
    """Return all catalog rules."""
    return list(load_catalog())


def get_catalog_counts() -> Dict[str, int]:
    """Return total/enabled/disabled counts derived from docs/constitution."""
    catalog = load_catalog()
    enabled = sum(1 for rule in catalog if rule.enabled)
    total = enabled
    return {
        "total_rules": total,
        "enabled_rules": enabled,
        "disabled_rules": total - enabled,
    }
