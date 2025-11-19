## CCCS EPC/PM Adapter Smoke Test Plan

### Purpose
Validate that the EPC-1/3/11/13 and PM-7 façade adapters still match the live control planes once connectivity is available. This plan supplements PRD §7–§9 by providing deterministic smoke checks before enabling CCCS in an environment that talks to real EPC services.

### Preconditions
1. Reachable base URLs for EPC-1, EPC-3, EPC-11, EPC-13, and PM-7 (TLS + auth tokens provisioned).
2. CCCS runtime config populated with those URLs plus timeouts ≤ 5s.
3. Ability to run curl/httpie (or the `scripts/cccs_adapter_smoke.py` harness once available) from the same network segment as CCCS.
4. A tenant/actor tuple that is safe to exercise (non-production identities).

### Adapter Checks

#### EPC-1 Identity Adapter
1. `POST /iam/{api_version}/verify` with a known actor context; expect 200 with `actor_id`, `tenant_id`, `user_id`.
2. `POST /iam/{api_version}/decision` for `get_provenance`; expect signed provenance metadata (Ed25519 signature chain, salt version).
3. Record latency; ensure < PRD §5.1 SLA (≤ 250 ms p95). If identity data mismatches mocks, update `tests/cccs/mocks.py::MockEPC1Adapter`.

#### EPC-3 Policy Adapter
1. `POST /policy/{api_version}/snapshots:validate` with a current snapshot + signature; expect `valid=true`.
2. `POST /policy/{api_version}/snapshots:load` and capture returned `snapshot_hash`.
3. `POST /policy/{api_version}/rules:negotiate` for each module; confirm negotiated version matches GSMD manifest.
4. `POST /policy/{api_version}/evaluate` with canned inputs; ensure decision/rationale pair mirrors GSMD expectations.

#### EPC-13 Budget Adapter
1. `POST /budget/{api_version}/check` with a low-cost action; expect `allowed=true` and remaining budget decreases.
2. Repeat with an over-budget cost; expect `BudgetExceededError` payload that maps to `budget_exceeded`.
3. `POST /budget/{api_version}/snapshots` to persist and retrieve snapshot IDs.

#### EPC-11 Signing Adapter
1. `POST /kms/{api_version}/sign` with a canonical receipt payload; expect an Ed25519 signature string.
2. `POST /kms/{api_version}/verify` using the prior signature; expect `valid=true`, and a tampered payload must return `valid=false`.
3. Verify the key_id matches HSM inventory managed by EPC-1.

#### PM-7 Ledger Adapter
1. `POST /evidence/{api_version}/receipts` with signed receipts from EPC-11; expect Merkle batch ID + root hash.
2. `POST /evidence/{api_version}/batches` for multi-receipt ingestion.
3. `POST /evidence/{api_version}/merkle-proof` for a known receipt; ensure path/hash responses validate locally.

### Runtime Validation
1. Deploy CCCSRuntime with live configs, call `bootstrap(...)`, and execute a low-impact flow.
2. Call `runtime.drain_courier()`; confirm PM-7 indexing occurs and WAL sequences advance.
3. Trigger process shutdown (SIGINT) and verify `CCCSRuntime.shutdown()` logs adapter close events with no hanging daemon threads.

### Reporting
Create a short report capturing:
- Endpoint URLs + versions exercised.
- Request/response samples (sanitized).
- Latency measurements.
- Any deltas from mocks/tests and resulting action items.

Run these smoke tests before enabling new EPC releases and whenever adapter mocks change, ensuring parity between offline tests and live control planes.
