"""
Additional positive/negative coverage for all Constitution rules (415 total).
This suite is table-driven and uses controlled mutations to avoid duplicating
existing structure/semantics tests while ensuring each rule ID is exercised
with a positive (as-authored) and a negative (mutated) check.
"""
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest


# All constitution source files (7)
CONSTITUTION_FILES = [
    "MASTER GENERIC RULES.json",
    "VSCODE EXTENSION RULES.json",
    "LOGGING & TROUBLESHOOTING RULES.json",
    "MODULES AND GSMD MAPPING RULES.json",
    "TESTING RULES.json",
    "COMMENTS RULES.json",
    "CURSOR TESTING RULES.json",
]

# Required fields checked by this suite (kept minimal to avoid overlap)
REQUIRED_FIELDS = ["rule_id", "title", "category", "enabled", "severity_level", "version"]
ALLOWED_SEVERITIES = {"Blocker", "Critical", "Major", "Minor"}


def constitution_dir() -> Path:
    # tests/constitution_positive_negative/ -> tests -> repo_root -> docs/constitution
    return Path(__file__).resolve().parents[2] / "docs" / "constitution"


def load_all_rules() -> Tuple[List[Dict[str, Any]], Counter]:
    """Load all rules from the seven constitution files."""
    rules: List[Dict[str, Any]] = []
    id_counter: Counter = Counter()
    base = constitution_dir()

    for filename in CONSTITUTION_FILES:
        file_path = base / filename
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for rule in data.get("constitution_rules", []):
            rules.append({"file": filename, "rule": rule})
            rule_id = rule.get("rule_id")
            if rule_id:
                id_counter[rule_id] += 1

    return rules, id_counter


def validate_rule(rule: Dict[str, Any]) -> List[str]:
    """Lightweight validation used by this suite (distinct from existing tests)."""
    errors: List[str] = []
    for field in REQUIRED_FIELDS:
        if field not in rule:
            errors.append(f"missing:{field}")
            continue
        value = rule[field]
        if isinstance(value, str) and not value.strip():
            errors.append(f"empty:{field}")
        if field == "enabled" and not isinstance(value, bool):
            errors.append("invalid:enabled_type")
        if field == "severity_level" and value not in ALLOWED_SEVERITIES:
            errors.append("invalid:severity")
    return errors


def mutate_rule(rule: Dict[str, Any], idx: int) -> Dict[str, Any]:
    """Create a negative variant per rule (pattern varies by index to reduce duplication)."""
    mutated = deepcopy(rule)
    # Rotate mutation types for diversity
    if idx % 3 == 0 and "rule_id" in mutated:
        mutated["rule_id"] = ""  # empty ID
    elif idx % 3 == 1 and "severity_level" in mutated:
        mutated["severity_level"] = "INVALID-SEVERITY"
    else:
        # Remove a required field (title) to ensure failure
        mutated.pop("title", None)
    return mutated


@pytest.fixture(scope="module")
def canonical_rules() -> List[Dict[str, Any]]:
    rules, id_counter = load_all_rules()
    # Assert total count matches expectation (415) before yielding
    assert len(rules) == 415, f"Expected 415 rules, found {len(rules)}"
    assert all(count == 1 for count in id_counter.values()), "Rule IDs must be globally unique"
    return rules


@pytest.fixture(scope="module")
def rule_id_counter() -> Counter:
    _, counter = load_all_rules()
    return counter


@pytest.mark.parametrize(
    "entry",
    [pytest.param(e, id=f"{e['file']}::{e['rule'].get('rule_id','NO_ID')}") for e in load_all_rules()[0]],
)
def test_rule_positive_invariants(entry: Dict[str, Any], rule_id_counter: Counter):
    """Positive: as-authored rule satisfies required invariants and global uniqueness."""
    rule = entry["rule"]
    errors = validate_rule(rule)
    assert not errors, f"Rule {rule.get('rule_id')} failed validation: {errors}"
    rule_id = rule.get("rule_id")
    if rule_id:
        assert rule_id_counter[rule_id] == 1, f"Rule ID not unique: {rule_id}"


@pytest.mark.parametrize(
    "idx, entry",
    [
        pytest.param(idx, e, id=f"{e['file']}::{e['rule'].get('rule_id','NO_ID')}")
        for idx, e in enumerate(load_all_rules()[0])
    ],
)
def test_rule_negative_mutations(idx: int, entry: Dict[str, Any]):
    """Negative: mutated rule must fail validation (one mutation per rule)."""
    rule = entry["rule"]
    mutated = mutate_rule(rule, idx)
    errors = validate_rule(mutated)
    assert errors, f"Mutated rule unexpectedly passed validation: {mutated.get('rule_id')}"
