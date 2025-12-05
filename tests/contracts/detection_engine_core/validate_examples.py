"""
Contract validation tests for Detection Engine Core

Validates example files per PRD §3.7
Coverage: All example files
"""

import json
import pathlib
from typing import Dict, Any, List

base = pathlib.Path(__file__).resolve().parents[3] / "contracts" / "detection_engine_core" / "examples"
names = [
    "decision_response_ok.json",
    "decision_response_error.json",
    "evidence_link_valid.json",
    "feedback_receipt_valid.json",
    "receipt_valid.json"
]


def validate_decision_response(data: Dict[str, Any]) -> None:
    """Validate decision response structure"""
    assert "receipt" in data or "error" in data, "Decision response must have receipt or error"
    if "receipt" in data:
        receipt = data["receipt"]
        assert "receipt_id" in receipt, "Receipt must have receipt_id"
        assert "decision" in receipt, "Receipt must have decision"
        assert "status" in receipt["decision"], "Decision must have status"


def validate_evidence_link(data: Dict[str, Any]) -> None:
    """Validate evidence link structure"""
    assert "type" in data, "Evidence link must have type"
    assert "href" in data, "Evidence link must have href"
    assert "label" in data, "Evidence link must have label"


def validate_feedback_receipt(data: Dict[str, Any]) -> None:
    """Validate feedback receipt structure"""
    assert "feedback_id" in data, "Feedback receipt must have feedback_id"
    assert "decision_receipt_id" in data, "Feedback receipt must have decision_receipt_id"
    assert "pattern_id" in data, "Feedback receipt must have pattern_id"
    assert data["pattern_id"] in ["FB-01", "FB-02", "FB-03", "FB-04"], "Invalid pattern_id"
    assert "choice" in data, "Feedback receipt must have choice"
    assert data["choice"] in ["worked", "partly", "didnt"], "Invalid choice"
    assert "actor" in data, "Feedback receipt must have actor"
    assert "repo_id" in data["actor"], "Actor must have repo_id"


def validate_receipt(data: Dict[str, Any]) -> None:
    """Validate receipt structure"""
    assert "receipt_id" in data, "Receipt must have receipt_id"
    assert "gate_id" in data, "Receipt must have gate_id"
    assert "evaluation_point" in data, "Receipt must have evaluation_point"
    assert data["evaluation_point"] in ["pre-commit", "pre-merge", "pre-deploy", "post-deploy"], "Invalid evaluation_point"
    assert "decision" in data, "Receipt must have decision"
    assert "status" in data["decision"], "Decision must have status"
    assert data["decision"]["status"] in ["pass", "warn", "soft_block", "hard_block"], "Invalid decision status"


def test_all_examples():
    """Test all example files"""
    for n in names:
        p = base / n
        assert p.exists(), f"Example file {n} does not exist"
        data = json.loads(p.read_text(encoding="utf-8"))
        assert isinstance(data, (dict, list)), f"Example {n} is not JSON object/list"

        if isinstance(data, dict):
            if "decision_response" in n or "decision_response" in str(data):
                validate_decision_response(data)
            elif "evidence_link" in n:
                validate_evidence_link(data)
            elif "feedback_receipt" in n:
                validate_feedback_receipt(data)
            elif "receipt" in n and "feedback" not in n:
                validate_receipt(data)

    print("OK: loaded and validated 5 examples for detection_engine_core")


if __name__ == "__main__":
    test_all_examples()
