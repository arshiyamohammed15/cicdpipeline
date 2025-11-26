## LLM Gateway – Pre‑Production Validation Runbook

Version 1.0 · Updated 2025‑11‑26

### 1. Purpose

This runbook defines the required steps to validate the LLM Gateway & Safety Enforcement module in a pre‑production environment before promotion to production.

### 2. Environment Setup

- **Gateway service**: Deployed in pre‑prod (FastAPI app, backing services reachable).
- **Dependent services**:
  - IAM (EPC‑1)
  - Data Governance & Privacy (EPC‑2)
  - Configuration & Policy / Gold Standards (EPC‑3/EPC‑10)
  - Budgeting, Rate‑Limiting & Cost Observability (EPC‑13)
  - ERIS (PM‑7)
  - Alerting (EPC‑4)

Configure the following environment variables for test jobs (replace hostnames with your pre‑prod endpoints):

```bash
export IAM_SERVICE_URL="https://preprod-iam.example.com/iam/v1"
export POLICY_SERVICE_URL="https://preprod-policy.example.com"
export DATA_GOVERNANCE_SERVICE_URL="https://preprod-dg.example.com/privacy/v1"
export BUDGET_SERVICE_URL="https://preprod-budget.example.com"
export ERIS_SERVICE_URL="https://preprod-eris.example.com"
export ALERTING_SERVICE_URL="https://preprod-alerts.example.com/v1"
export USE_REAL_SERVICES="true"
```

### 3. Real‑Service Functional Validation

From the repo root (CI job or pre‑prod bastion), run:

```bash
python -m pytest tests/llm_gateway -m "llm_gateway_real_integration" -v
```

**Pass criteria**:
- All tests in `tests/llm_gateway/test_real_services_integration.py` pass.
- No tests are skipped due to service health check failures.

### 4. Performance Validation (k6)

Ensure the k6 script points at the pre‑prod LLM Gateway base URL (configure via env or script parameter).

```bash
npm run test:llm-gateway:performance
```

**Pass criteria** (per PRD §8):
- p95 latency ≤ 50 ms for simple chat flows.
- p95 latency ≤ 80 ms for full safety flows.
- No sustained 5xx error rate > 0.1 % during the run.

### 5. Observability Validation

Run the telemetry scenario + observability validator:

```bash
python scripts/ci/run_llm_gateway_telemetry_scenario.py artifacts/llm_gateway_telemetry.log
python scripts/ci/validate_llm_gateway_observability.py artifacts/llm_gateway_telemetry.log
```

**Pass criteria**:
- Validator exits with status code 0.
- All required metrics/log fields/trace attributes are present.
- No unredacted PII/secrets detected in logs or receipts.

### 6. Regression Harness (Golden Corpora)

Replay benign and adversarial corpora against the pre‑prod gateway:

```bash
python scripts/ci/replay_llm_gateway_corpus.py \
  docs/architecture/tests/golden/llm_gateway/benign_corpus.jsonl \
  artifacts/llm_gateway_benign_results.jsonl

python scripts/ci/replay_llm_gateway_corpus.py \
  docs/architecture/tests/golden/llm_gateway/adversarial_corpus.jsonl \
  artifacts/llm_gateway_adversarial_results.jsonl
```

Compare results with a known‑good baseline (from last approved release) using your diff tooling of choice.

**Pass criteria**:
- No previously BLOCKED/TRANSFORMED adversarial prompts become ALLOWED.
- Previously ALLOWED benign prompts remain ALLOWED unless an intentional policy tightening is documented.

### 7. Security / Red‑Team Sweep

Optionally run the security‑tagged tests:

```bash
python -m pytest tests/llm_gateway/test_security_regression.py -m "llm_gateway_security" -v
```

**Pass criteria**:
- No adversarial corpus entry with `expected_decision != "ALLOWED"` yields `Decision.ALLOWED`.

### 8. Promotion Go/No‑Go Rules

Do **not** promote to production unless all of the following hold:

1. **Functional**: Real‑service integration tests pass with no skips.
2. **Performance**: k6 perf job meets p95 latency SLOs and error‑rate thresholds.
3. **Observability**: Observability validator passes; no PII/secret findings.
4. **Regression**: Corpus replay shows no unintended loosening/tightening.
5. **Security** (if run): Security regression tests report no violations.

Document any exceptions (e.g. temporary SLO relaxations) in the change‑management ticket with explicit approval from owning leads (IAM, Policy, Data Governance, Observability, Security Architecture).


