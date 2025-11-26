# LLM Gateway & Safety Enforcement – Test Plan

Version 1.0 · Updated 2025-11-26

## 1. Scope & Objectives
- Validate every Functional Requirement (FR-1 … FR-13) and Non-Functional Requirement (NFR-1 … NFR-4) in the PRD.
- Enforce schema compatibility for `llm_request_v1`, `llm_response_v1`, `safety_assessment_v1`, `safety_incident_v1`, and `dry_run_decision_v1`.
- Provide deterministic evidence (receipts, logs, corpora hashes) for CI/CD promotion, audits, and policy change reviews.

## 2. Authoritative Artifacts
| Artifact | Purpose |
| --- | --- |
| `contracts/schemas/*.json` listed in §14.1 | Contract validation for request/response bodies. |
| `docs/architecture/tests/golden/llm_gateway/benign_corpus.jsonl` | Clean prompts/contexts that must stay ALLOWED. |
| `docs/architecture/tests/golden/llm_gateway/adversarial_corpus.jsonl` | Injection/PII/exfil attempts used for regression. |
| `docs/architecture/modules/LLM_Gateway_and_Safety_Enforcement_Updated.md` | Normative behaviour + policy blueprint. |

All corpora entries are anonymised and hashed; update via PR reviewed by Governance + Security.

## 3. Test Matrix
| Requirement | Test ID | Type | Description | Evidence |
| --- | --- | --- | --- | --- |
| FR-1 Central Gateway | UT-LLM-01 | Unit | Assert direct provider client is never invoked when gateway disabled; use dependency injection + spy. | Pytest snapshot + call graph. |
| FR-2 Identity & Auth | UT-LLM-02 | Unit | Validate request rejected without mandatory IAM claims; verify `safety_incident_v1` entry created. | Pytest + schema validation. |
| FR-3 Policy Enforcement | IT-LLM-06 | Integration | Simulate policy update → ensure cache invalidation and receipts show new `policy_snapshot_id`. | `test_policy_refresh_integration.py` + FastAPI test client. |
| FR-4 Prompt Injection | UT-LLM-03 | Unit | Replay adversarial corpus R1 cases; expect sanitisation or block decisions. | Pytest param set referencing corpus file. |
| FR-5 PII/Secrets | IT-LLM-03 | Integration | Mock EPC-2 API; ensure redaction counts recorded and raw values never leave process. | HTTP mocked transcripts. |
| FR-6 Meta-Prompt Enforcement | UT-LLM-04 | Unit | Assert user payload cannot override system prompt; meta prompt hash logged. | Snapshot of receipt metadata. |
| FR-7 Output Safety | IT-LLM-05 | Integration | Force provider to emit disallowed text; verify classifier blocks + EPC-4 alert. | Recorded alert payload. |
| FR-8 Tool Safety | UT-LLM-05 | Unit | Feed tool suggestions + policy matrix; ensure blocked actions produce WARN severity. | Policy diff + receipts. |
| FR-9 Budgeting | IT-LLM-05 | Integration | Exhaust budget, expect deterministic BLOCKED decision and `epc6_budget_block_total` increment. | Metrics scrape + receipt. |
| FR-10 Routing & Isolation | IT-LLM-04 | Integration | Dual-tenant scenario verifying no cross-tenant context leakage. | Trace comparison. |
| FR-11 Telemetry/Receipts | OT-LLM-01 | Observability | Validate metrics, logs, traces contain mandatory fields; compare to schema. | OpenTelemetry export + log sample. |
| FR-12 Alerts | IT-LLM-06 | Integration | Trigger repeated injection attempts → dedupe key ensures single EPC-4 alert per window. | Alert log + dedupe key check. |
| FR-13 Fallback | RT-LLM-01 | Resilience | Simulate provider outage + secondary success/failure flows. | Receipts with `degradation_stage` states. |
| NFR-1 Latency | PT-LLM-01 | Perf | Load test safe flows to confirm ≤50 ms p95 overhead. | K6 report + histograms. |
| NFR-2 Availability | RT-LLM-01 | Resilience | Combine chaos faults w/ fail-closed expectations. | Chaos log + receipts. |
| NFR-3 Security | ST-LLM-* | Security | Red-team style prompts derived from adversarial corpus. | Findings log + remediation ticket. |
| NFR-4 Observability | OT-LLM-01 | Observability | Validate instrumentation coverage. | Metrics + trace exports. |

## 4. Golden Corpora Usage
- **Benign corpus**: 20 entries, each containing `prompt`, `context_summary`, `expected_decision="ALLOWED"`. Used in smoke + regression jobs to ensure no accidental tightening.
- **Adversarial corpus**: 25 entries labelled with `risk_class` and `expected_response` (`BLOCKED`, `TRANSFORMED`, or `ALLOWED_WITH_REDACTION`). Each entry references the FR it protects.
- Corpora hashed with SHA-256; CI logs include hash to detect tampering.

## 5. CI Integration & Commands
| Stage | Command | Notes |
| --- | --- | --- |
| Unit | `npm run test:llm-gateway:unit` | Includes schema validation + corpus-driven tests. |
| Integration | `npm run test:llm-gateway:integration` | Spins up FastAPI app + mocks EPC services. |
| Real Services | `USE_REAL_SERVICES=true npm run test:llm-gateway:real-services` | End-to-end tests against actual backend services. Requires all services running. |
| Contract | `python scripts/ci/validate_llm_gateway_schemas.py && pytest tests/llm_gateway/test_clients_contracts.py` | Ensures schema syntax + backwards compatibility + client contract alignment. |
| Observability | `npm run test:llm-gateway:observability:ci` | Runs telemetry scenario + validates required log fields, metrics, traces per §14.4. |
| Performance | `npm run test:llm-gateway:performance` | 10 min soak test; validates latency SLOs (≤50ms p95 simple, ≤80ms p95 full safety). |
| Security Regression | `pytest tests/llm_gateway/test_security_regression.py -m llm_gateway_security` | Replays adversarial corpus; ensures no silent ALLOWED for high-risk cases. |
| Regression Harness | `python scripts/ci/replay_llm_gateway_corpus.py <corpus> <output>` | Replays corpora and generates decision diffs for change management. |

### 5.1 Real Service Integration Testing

Real service integration tests (`test_real_services_integration.py`) validate end-to-end workflows against actual backend service implementations. These tests require:

1. **Environment Setup**: Set `USE_REAL_SERVICES=true` environment variable
2. **Service URLs**: Configure via environment variables (defaults to localhost):
   - `IAM_SERVICE_URL` (default: `http://localhost:8001/iam/v1`)
   - `POLICY_SERVICE_URL` (default: `http://localhost:8003`)
   - `DATA_GOVERNANCE_SERVICE_URL` (default: `http://localhost:8002/privacy/v1`)
   - `BUDGET_SERVICE_URL` (default: `http://localhost:8035`)
   - `ERIS_SERVICE_URL` (default: `http://localhost:8007`)
   - `ALERTING_SERVICE_URL` (default: `http://localhost:8004/v1`)
3. **Service Health**: All services must be running and healthy (health checks performed automatically)
4. **Test Coverage**: Exercises IT-LLM-01 through IT-LLM-07:
   - IT-LLM-01: Benign prompt allowed through real stack
   - IT-LLM-02: Adversarial prompt blocked by real safety pipeline
   - IT-LLM-03: IAM validation failure handling
   - IT-LLM-04: Budget enforcement
   - IT-LLM-05: Data governance redaction
   - IT-LLM-06: ERIS receipt emission
   - IT-LLM-07: Policy snapshot caching

Tests automatically skip if services are unavailable, allowing CI to run mocked integration tests when real services are not deployed.

### 5.2 CI Pipeline Configuration

The LLM Gateway CI pipeline (`.github/workflows/llm_gateway_ci.yml`) includes the following stages:

1. **Unit Tests**: `npm run test:llm-gateway:unit`
2. **Integration Tests**: `npm run test:llm-gateway:integration`
3. **Schema & Contract Validation**: `python scripts/ci/validate_llm_gateway_schemas.py` + contract tests
4. **Observability Validation**: `npm run test:llm-gateway:observability:ci`
5. **Performance Tests**: k6 run with SLO validation via `scripts/ci/validate_k6_slo.py`
6. **Security Regression**: `pytest -m llm_gateway_security`
7. **Regression Harness**: Corpus replay for decision tracking

All artifacts (telemetry logs, k6 results, corpus replay outputs, security findings) are stored for ≥180 days per §6.

### 5.3 Client Contract Tests

Client contract tests (`tests/llm_gateway/test_clients_contracts.py`) validate that HTTP clients send payloads conforming to external service contracts per §14.3:

- **IAMClient**: Validates `/decision` endpoint payload with required claims (subject_id, roles, capabilities, scopes)
- **DataGovernanceClient**: Validates `/compliance` endpoint payload for PII redaction
- **PolicyClient**: Validates `/standards` endpoint query parameters
- **BudgetClient**: Validates `/budgets/check` endpoint payload structure
- **ErisClient**: Validates `/receipts` endpoint payload with required fields
- **AlertingClient**: Validates `/alerts` endpoint payload with `alert_safety_incident_v1` schema

These tests use mocked HTTP clients to capture request payloads without requiring real services.

### 5.4 Security Regression Suite

Security regression tests (`tests/llm_gateway/test_security_regression.py`) marked with `@pytest.mark.llm_gateway_security`:

- Replay adversarial corpus entries and assert high-risk cases (R1 prompt injection, R4 tool abuse) are never silently ALLOWED
- Generate structured findings artifacts for AI risk/compliance review
- Reference: ST-LLM-* in test matrix

### 5.5 Regression Harness

The regression harness script (`scripts/ci/replay_llm_gateway_corpus.py`) enables:

- Replaying benign + adversarial corpora against the gateway
- Generating JSONL decision records for before/after comparison
- Detecting unintended behaviour changes during model/policy upgrades
- Reference: RG-LLM-01 in test matrix

Job gating rules:
- Fail build if any schema drift occurs relative to `contracts/schemas/*.json`.
- Perf job allowed ±5 ms variance; anything higher opens a Sev-2 defect.
- Observability job parses logs ensuring required fields exist (see §14.4).
- Real service tests are optional in CI but required for pre-production validation.
- Security regression failures block promotion; findings must be reviewed.
- Regression harness diffs must show no unexpected loosening/tightening.

## 6. Evidence & Retention
- Store receipts, logs, metrics summaries, and corpus hashes in `${ZU_ROOT}/shared/evidence/llm_gateway/{build_id}` for ≥180 days.
- Attach summary report to change-management ticket with links to CI run, detector versions, and policy snapshot IDs.
- CI artifacts (telemetry logs, k6 results, corpus replay outputs, security findings) are automatically uploaded and retained per `.github/workflows/llm_gateway_ci.yml`.

## 7. Ownership
- QA Lead: ZeroUI Safety QA
- Approvers: IAM lead (EPC-1), Policy lead (EPC-3), Data Governance lead (EPC-2), Observability lead (PM-3/CCP-4)

Any change to detectors, schemas, or corpora requires sign-off from all approvers above plus Security Architecture.

