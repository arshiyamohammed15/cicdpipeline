#!/usr/bin/env python3
"""
Replay LLM Gateway golden corpora and record decisions for regression testing.

Usage:
    python scripts/ci/replay_llm_gateway_corpus.py <corpus_file> <results_out>

The script:
- Loads entries from the specified JSONL corpus file
- Sends each entry as a /api/v1/llm/chat request to the in-process FastAPI app
- Writes one JSON line per request to <results_out> containing:
  - id, expected_decision (if present), actual_decision

This file can then be compared across builds to detect behavioural drift.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from fastapi.testclient import TestClient

from scripts.ci.run_llm_gateway_telemetry_scenario import (  # type: ignore  # pylint: disable=import-error
    _ensure_cloud_services_package,  # reuse wiring
)

_ensure_cloud_services_package()

from cloud_services.llm_gateway.main import app  # type: ignore  # pylint: disable=import-error
from cloud_services.llm_gateway.models import (  # type: ignore  # pylint: disable=import-error
    Actor,
    Budget,
    LLMRequest,
    OperationType,
    SafetyOverrides,
    Tenant,
)


def _build_request_from_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    operation_type = OperationType(entry.get("operation_type", "chat"))
    req = LLMRequest(
        request_id=f"req-{entry['id']}",
        actor=Actor(
            actor_id="actor-regression",
            actor_type="human",
            roles=["developer"],
            capabilities=["llm.invoke"],
            scopes=[f"llm.{operation_type.value}"],
            session_assurance_level="high",
            workspace_id="workspace-regression",
        ),
        tenant=Tenant(tenant_id="tenantRegression", region="us-west"),
        logical_model_id="default_chat",
        operation_type=operation_type,
        intended_capability="analysis",
        sensitivity_level="medium",
        system_prompt_id="sys-default",
        user_prompt=entry["prompt"],
        context_segments=[],
        policy_snapshot_id="policy-snap-regression",
        policy_version_ids=["policy-v1"],
        budget=Budget(
            max_tokens=512,
            timeout_ms=2000,
            priority="normal",
            temperature=0.2,
        ),
        safety_overrides=SafetyOverrides(),
    )
    return req.model_dump(mode="json")


def replay_corpus(corpus_file: Path, results_out: Path) -> int:
    client = TestClient(app)
    entries = [
        json.loads(line)
        for line in corpus_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    results_out.parent.mkdir(parents=True, exist_ok=True)
    with results_out.open("w", encoding="utf-8") as out:
        for entry in entries:
            body = _build_request_from_entry(entry)
            resp = client.post("/api/v1/llm/chat", json=body)
            if resp.status_code != 200:
                decision = f"HTTP_{resp.status_code}"
            else:
                decision = resp.json().get("decision")

            record = {
                "id": entry["id"],
                "expected_decision": entry.get("expected_decision"),
                "actual_decision": decision,
            }
            out.write(json.dumps(record) + "\n")

    return 0


def main() -> int:
    import sys

    if len(sys.argv) != 3:
        print(
            "Usage: replay_llm_gateway_corpus.py <corpus_file> <results_out>",
        )
        return 1

    corpus_file = Path(sys.argv[1])
    results_out = Path(sys.argv[2])

    if not corpus_file.exists():
        print(f"Corpus file not found: {corpus_file}")
        return 1

    return replay_corpus(corpus_file, results_out)


if __name__ == "__main__":
    raise SystemExit(main())


