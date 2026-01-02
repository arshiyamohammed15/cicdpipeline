# Trust as a Capability (EPC-14)

Minimal shared-service stub for trust evaluation.

- FastAPI app with `/health` and `/trust/evaluate` endpoints.
- Deterministic rules:
  - `subject_id` required (400 if missing).
  - `context.workspace_trust == false` → `trust_level="untrusted"` and reason `WORKSPACE_UNTRUSTED`.
  - Otherwise `trust_level="unknown"` with reason `NO_ATTESTATION_EVIDENCE`.
- Returns `decision_id` (UUID4) per request. No external integrations.
