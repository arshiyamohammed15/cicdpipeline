"""
Positive/negative, table-driven tests for all Constitution rules (415 total).
Goals:
- Positive: every authored rule validates (structure/content).
- Negative: a deterministic mutation per rule fails validation.
- Non-duplication: uses mutation-based negatives (not present in existing suites).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pytest


CONSTITUTION_FILES: Tuple[str, ...] = (
    "MASTER GENERIC RULES.json",
    "VSCODE EXTENSION RULES.json",
    "LOGGING & TROUBLESHOOTING RULES.json",
    "MODULES AND GSMD MAPPING RULES.json",
    "TESTING RULES.json",
    "COMMENTS RULES.json",
    "CURSOR TESTING RULES.json",
)

# Allowed severities per constitution spec
ALLOWED_SEVERITIES = {"Blocker", "Critical", "Major", "Minor"}


def _constitution_base() -> Path:
    """Return absolute path to docs/constitution."""
    return Path(__file__).resolve().parents[2] / "docs" / "constitution"


def _load_rules() -> List[Dict]:
    """Load all rules from all constitution files with file context."""
    base = _constitution_base()
    all_rules: List[Dict] = []
    for filename in CONSTITUTION_FILES:
        data = json.loads((base / filename).read_text(encoding="utf-8"))
        rules = data.get("constitution_rules", [])
        for idx, rule in enumerate(rules):
            all_rules.append(
                {
                    "filename": filename,
                    "index": idx,
                    "rule": rule,
                }
            )
    return all_rules


def _metadata_counts() -> List[Tuple[str, int, int]]:
    """Return (filename, metadata.total_rules, actual_count)."""
    base = _constitution_base()
    results: List[Tuple[str, int, int]] = []
    for filename in CONSTITUTION_FILES:
        data = json.loads((base / filename).read_text(encoding="utf-8"))
        meta_total = data.get("metadata", {}).get("total_rules", 0)
        actual = len(data.get("constitution_rules", []))
        results.append((filename, meta_total, actual))
    return results


def validate_rule(rule: Dict) -> bool:
    """Return True if rule satisfies required structure/content."""
    required_fields = ["rule_id", "title", "category", "enabled", "severity_level", "version"]
    for field in required_fields:
        if field not in rule:
            return False
    if not isinstance(rule["rule_id"], str) or not rule["rule_id"].strip():
        return False
    if not isinstance(rule["title"], str) or not rule["title"].strip():
        return False
    if not isinstance(rule["category"], str) or not rule["category"].strip():
        return False
    if not isinstance(rule["enabled"], bool):
        return False
    if not isinstance(rule["severity_level"], str) or rule["severity_level"] not in ALLOWED_SEVERITIES:
        return False
    if not isinstance(rule["version"], str) or not rule["version"].strip():
        return False

    # Optional fields with type expectations
    if "effective_date" in rule and not isinstance(rule["effective_date"], str):
        return False
    if "last_updated" in rule and not isinstance(rule["last_updated"], str):
        return False
    if "last_updated_by" in rule and not isinstance(rule["last_updated_by"], str):
        return False
    if "description" in rule and not isinstance(rule["description"], str):
        return False
    if "requirements" in rule and not isinstance(rule["requirements"], list):
        return False
    if "validation" in rule and not isinstance(rule["validation"], str):
        return False
    if "error_condition" in rule and not isinstance(rule["error_condition"], str):
        return False
    if "policy_linkage" in rule and not isinstance(rule["policy_linkage"], dict):
        return False
    return True


def mutate_rule(rule: Dict, mutation_selector: int) -> Dict:
    """
    Deterministically mutate a rule to create a negative case.
    selector mod 3 chooses the mutation:
    0: drop rule_id
    1: blank title
    2: invalid severity_level
    """
    mutated = copy.deepcopy(rule)
    choice = mutation_selector % 3
    if choice == 0:
        mutated.pop("rule_id", None)
    elif choice == 1:
        mutated["title"] = ""
    else:
        mutated["severity_level"] = "INVALID-SEVERITY"
    return mutated


# --- Tests ---


@pytest.mark.parametrize("filename,meta_count,actual_count", _metadata_counts())
def test_metadata_counts_match_actual(filename: str, meta_count: int, actual_count: int) -> None:
    """Metadata total_rules must match actual rule count (positive check)."""
    assert meta_count == actual_count, f"{filename} metadata.total_rules={meta_count} actual={actual_count}"


@pytest.mark.parametrize("entry", _load_rules())
def test_rule_positive(entry: Dict) -> None:
    """Positive: every authored rule validates."""
    rule = entry["rule"]
    assert validate_rule(rule), f"{entry['filename']}[{entry['index']}] failed validation"


@pytest.mark.parametrize("entry", _load_rules())
def test_rule_negative_mutation(entry: Dict) -> None:
    """Negative: deterministic mutation per rule must fail validation."""
    mutated = mutate_rule(entry["rule"], entry["index"])
    assert not validate_rule(mutated), f"Mutation should fail: {entry['filename']}[{entry['index']}]"
