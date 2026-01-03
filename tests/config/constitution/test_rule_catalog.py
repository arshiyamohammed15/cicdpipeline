from __future__ import annotations

import json
from pathlib import Path

import pytest

from config.constitution import rule_catalog


@pytest.fixture(autouse=True)
def clear_catalog_cache():
    rule_catalog.load_catalog.cache_clear()
    yield
    rule_catalog.load_catalog.cache_clear()


def _write_docs(tmp_dir: Path) -> None:
    data = {
        "constitution_rules": [
            {
                "title": "Structured Logs",
                "category": "Platform / Security",
                "priority": "High",
                "enabled": True,
                "rule_id": "DOC-001",
                "description": "Ensure logs are structured."
            },
            {
                "title": "Optional Rule",
                "category": "Misc",
                "priority": "Low",
                "enabled": False
            },
        ]
    }
    (tmp_dir / "rules.json").write_text(json.dumps(data), encoding="utf-8")


def _write_config(tmp_file: Path) -> None:
    payload = {
        "rules": {
            "rule_010": {
                "title": "Structured Logs",
                "rule_number": 10
            }
        }
    }
    tmp_file.write_text(json.dumps(payload), encoding="utf-8")


def test_catalog_loads_from_docs_and_config(tmp_path, monkeypatch):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    _write_docs(docs_dir)

    config_file = tmp_path / "constitution_rules.json"
    _write_config(config_file)

    monkeypatch.setattr(rule_catalog, "CANDIDATE_CONSTITUTION_DIRS", [docs_dir])
    monkeypatch.setattr(rule_catalog, "CONFIG_CONSTITUTION_JSON", config_file)

    catalog = rule_catalog.load_catalog()

    # Structured Logs picks up rule_number from config and preserves doc id
    structured = rule_catalog.get_rule_by_title("structured logs")
    assert structured is not None
    assert structured.rule_number == 10
    assert structured.rule_id == "rule_010"
    assert structured.doc_rule_id == "DOC-001"
    assert structured.category == "platform___security"
    assert structured.priority == "high"

    # Optional rule falls back to deterministic numbering
    optional = rule_catalog.get_rule_by_title("Optional Rule")
    assert optional is not None
    assert optional.rule_number == 1
    assert optional.enabled is False

    # Doc-id lookup works with normalization
    by_doc = rule_catalog.get_rule_by_doc_id("doc-001")
    assert by_doc is structured

    counts = rule_catalog.get_catalog_counts()
    assert counts == {"total_rules": 2, "enabled_rules": 1, "disabled_rules": 1}
