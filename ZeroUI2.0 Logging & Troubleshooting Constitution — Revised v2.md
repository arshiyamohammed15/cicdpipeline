# ZeroUI 2.0 — Logging & Troubleshooting Constitution (Cursor) — Revised

> Goal: Make logs **easy to trace** and **easy to use** for debugging by interns who rely on AI code generation. Use simple English. All logs are **structured JSON** (one JSON object per line). No secrets or PII in logs.

---

## 1) System Constitution — Logging (paste into Cursor “System”)

```text
CURSOR_CONSTITUTION_LOGGING — ZeroUI 2.0

You are the code generator. You MUST produce robust, structured logs that make troubleshooting easy. Use simple English. If any rule would be broken, STOP and return an ERROR code (§13).

0) LOG FORMAT & TRANSPORT
- Format: ONE JSON object per line (JSONL).
- Timestamps: ISO-8601 with Z (UTC). Include monotonic_hw_time_ms for ordering.
- Monotonic precision: use perf_counter_ns() (Python) / performance.now() (TS), store ms (rounded) from ns.
- Encoding: UTF-8 only, no BOM. No multi-line logs.
- Windows/laptop: CRLF-safe, append with flush to avoid partial lines. Keep path length ≤ 240 chars.
- Output: dev → console + file; prod → file/stream (ship to aggregator). Rotation handled by platform.

1) REQUIRED FIELDS (ALL LOGS)
- log_schema_version: "1.0"
- ts_utc, monotonic_hw_time_ms
- level: TRACE|DEBUG|INFO|WARN|ERROR|FATAL
- service, version, env, host
- traceId, spanId, parentSpanId (W3C trace context). If missing, generate and propagate.
- requestId (X-Request-Id), userId_hash (if applicable), tenantId (UUIDv7) — userId_hash is salted per-tenant.
- event: short stable name, e.g., "request.start", "request.end", "db.query", "external.call", "receipt.emit"
- route/method/status (for HTTP), apiVersion
- latencyMs, attempt, retryable
- payload_hash, payload_size, sample_reason (if sampled)
- error.code, error.message_redacted, error.stack_fingerprint (when level ≥ ERROR)
- idempotencyKey_hash (if present), cursor_hint (for pagination)
- policy_snapshot_hash (if decision), feature_flag (if used)

1.1) FIELD CONSTRAINTS (TYPES & LIMITS)
- event ≤ 40 chars; pattern: ^[a-z]+(\.[a-z_]+)*$
- error.code ≤ 40; error.message_redacted ≤ 512; stack_fingerprint ≤ 128
- Truncate free-text fields > 512 chars. Arrays: max 50 items. Always include payload_size.
- LOG_MAX_EVENT_BYTES default 65536; truncate & set truncation flags if exceeded.

1.2) HASHING POLICY (DETERMINISTIC)
- SHA-256 over UTF-8 bytes.
- userId_hash = sha256(tenant_salt || user_id). Do not cross-tenant correlate.
- idempotencyKey_hash = sha256(key). payload_hash = sha256(redacted_payload_bytes).

2) STABLE EVENT NAMES (MUST USE)
- request.start / request.end (exactly one start and one end per handled request)
- db.query / db.error
- cache.hit / cache.miss
- external.call.start / external.call.end / external.call.error
- llm.invoke.start / llm.invoke.end / llm.invoke.error
- receipt.emit
- contract.violation
- policy.decision
- migration.start / migration.end
- app.start / app.stop / health.ok / health.error

2.1) LLM EVENT FIELDS

2.2) EVENT IDENTITY & WORKFLOW CORRELATION (LLM‑FRIENDLY)
- **event_id** (UUID; prefer time‑sortable IDs like UUIDv7/ULID) — unique per log line.
- **caused_by** (event_id or null) — causal parent when not captured by parentSpanId.
- **links[]** — related event/message/job IDs for async handoffs.
- **job_id**, **queue_name**, **message_id**, **schedule_id** — background and queue processing.
- **workflow_id**, **saga_id** — multi‑request or long‑running business flows.
- **component** — sub‑system name (e.g., policy.engine, payments.gateway).
- **phase** — one of: input | process | output | cleanup.
- **git_sha**, **build_id**, **config_version** — deployment fingerprints.
- **severity_code** — S0..S4; **user_impact** — none | one | many.

- model, input_tokens, output_tokens, latencyMs, prompt_hash, output_hash, policy_snapshot_hash.
- Never log raw prompts/outputs. Always emit llm.invoke.end; if failure, include error.* and success=false.

2) LEVEL POLICY
- Dev: default INFO; allow DEBUG for local.
- Prod: INFO by default. DEBUG only with a temporary WAIVER (id + expiry).
- Errors: use ERROR for failures that returned 4xx/5xx; WARN for recoverable issues.
- Never log FATAL without an immediate exit path.
- Map error.code to central error registry (same codes as API Contracts).



3) CORRELATION & CONTEXT
- Read/propagate W3C headers: **traceparent** and **tracestate**. If missing, generate them.
- Always attach **traceId/spanId** and pass **X-Request-Id** (generate if missing).
- Exactly one **request.start** and one **request.end** per handled request (same traceId/requestId).
- For retries/backoff: include **attempt**, **backoffMs**, **retryable**.
- For idempotency: include **idempotencyKey_hash** + **replay=true/false**.
- For async hops (queues/schedulers): include **links[]**, **job_id**, **queue_name**, **message_id**, **schedule_id**.
- For cross‑request business flows: include **workflow_id** or **saga_id**.

4) RECEIPTS (AUDIT TRAIL)
- For privileged or business-significant actions: emit a receipt (append-only JSONL) and log event "receipt.emit" with the receipt_id.
- Receipt fields: ts_utc, monotonic_hw_time_ms, actor (human|ai), service, action, result, traceId, policy_snapshot_hash, inputs_hash, outputs_hash.

5) PERFORMANCE BUDGETS & SAMPLING
- Logging overhead should be < 5% CPU and < 2% latency on hot paths.
- Default sampling: DEBUG (1–10%), INFO (100%), TRACE (off).
- Dynamic knobs (env): LOG_SAMPLE_DEBUG=0.1, LOG_SAMPLE_DB_QUERY=0.05, LOG_MAX_EVENT_BYTES=65536.
- CI blocks events > LOG_MAX_EVENT_BYTES unless truncation fields are present.

6) PYTHON (FastAPI) & TYPESCRIPT RULES
- Use a shared logger util that enforces schema and redaction. No print() or console.log() for runtime logs.
- FastAPI middleware: log request.start and request.end (route, method, status, latencyMs, traceId, requestId).
- DB: log query summaries (table, op, row_count) not raw SQL; attach elapsedMs.
- TS: add interceptors to log external.call.* with url_host, method, status, latencyMs.

7) STORAGE & RETENTION (LAPTOP-FIRST)
- Path: <server>/logs/YYYY-MM-DD/*.jsonl (daily). Rotate at 100MB; keep last 10 files locally.
- Retention: app logs ≥ 14 days locally; receipts ≥ 90 days (or per policy).
- Compression after rotation is allowed; do not compress live file.
- Writing: UTF-8 (no BOM), CRLF-safe, one JSON per line with flush after each write. Guard against partial lines on power loss.

8) STOP CONDITIONS → ERROR CODES
- Unstructured (not JSON) or multi-line log ……… ERROR:UNSTRUCTURED_LOG
- Missing traceId/requestId on request/end ……… ERROR:MISSING_TRACE_ID
- Secrets/PII present in any log ………………… ERROR:PII_LEAK
- Full payload logged (no redaction) ……………… ERROR:PAYLOAD_NOT_REDACTED
- Missing error.code on ERROR level ……………… ERROR:MISSING_ERROR_CODE
- Oversized event (> LOG_MAX_EVENT_BYTES) ……… ERROR:OVERSIZED_EVENT
- Chatty code without sampling …………………… ERROR:SAMPLING_MISSING
- Log level policy violated ……………………… ERROR:LOG_LEVEL_VIOLATION
- Invalid JSON (serialization) …………………… ERROR:JSON_INVALID
- No link to receipt on privileged action ………… ERROR:MISSING_RECEIPT_LINK

9) RETURN CONTRACTS (OUTPUT FORMAT — PICK ONE)
A) Unified Diff (default for code)
# repo-root-relative paths
# unified diff (git-style) with only minimal changes
B) New File (exactly one file)
#path: relative/path/to/new_file.ext
<entire file content only>
C) JSON Artifact (policy/config/schema)
{ ...valid JSON only... }
If output cannot meet a format → ERROR:RETURN_CONTRACT_VIOLATION.

10) SCHEMA VALIDATION (CI / PRE-COMMIT)
- Validate events against docs/log_schema_v1.json (JSON Schema) in CI and pre-commit.
- Block merge if schema fails or if required fields/limits are missing.

11) SELF-AUDIT (CHECK BEFORE OUTPUT)
- [ ] JSONL, ISO-8601 Z, monotonic time (ns→ms), Windows-safe write
- [ ] Required fields present (traceId, requestId, event, level, latencyMs, schema version)
- [ ] No secrets/PII; payloads hashed/truncated; sizes included
- [ ] Sampling set for chatty events; budgets respected; runtime knobs documented
- [ ] request.start/request.end present with correlation
- [ ] Receipts for privileged actions; link receipt_id in logs; error.code maps to registry
END_CONSTITUTION
```

---

## 2) Micro-Prompt Footer — Logging (attach to every task)

```text
MICRO_PROMPT_FOOTER — Logging (Simple English)

=== MUST FOLLOW ===
- Emit JSONL logs with required fields and redaction. Add request.start/request.end middleware.
- Use shared logger util, not ad-hoc prints. Add traceId/spanId + requestId on all logs.
- Add sampling to chatty paths. Hash + size every large payload. Link receipts for privileged actions.
- Include log_schema_version and enforce field limits.

=== RETURN CONTRACT ===
Output exactly ONE: Unified Diff | New File | JSON (System §11). Show log schema or code near changed logic.

=== SELF-CHECK ===
- [ ] Required fields, correlation ids present
- [ ] No secrets/PII; hashes + sizes; truncation
- [ ] Sampling + performance budget ok; max event bytes enforced
- [ ] Receipts linked for privileged actions; error.code mapped to registry
```

---

## 3) PR Checklist — Logging (paste into `.github/pull_request_template.md`)

```markdown
### Logging & Troubleshooting — Required Checks

**Basics**
- [ ] JSONL format with ISO-8601 UTC + monotonic time (ns→ms)
- [ ] Required fields present: log_schema_version, level, traceId, spanId, requestId, event, latencyMs
- [ ] Exactly one request.start and one request.end per request (same traceId/requestId)

**Privacy & Safety**
- [ ] No secrets/PII; Authorization/cookies redacted; IP anonymized
- [ ] Payloads truncated + hashed; payload_size recorded
- [ ] ERROR logs carry error.code + stack_fingerprint (not full stack)

**Correlation & Context**
- [ ] W3C trace headers propagated (traceparent/tracestate); X-Request-Id preserved
- [ ] idempotencyKey_hash added where used; retry fields set (attempt/backoffMs)
- [ ] Async hops include links[], job_id/queue_name/message_id/schedule_id
- [ ] Business flows include workflow_id or saga_id

**Deployment & Severity**
- [ ] git_sha/build_id/config_version attached where relevant
- [ ] severity_code (S0..S4) and user_impact (none|one|many) set on incidents

**Platform-Specific**
- [ ] FastAPI middleware present/updated; DB logs are summaries (table/op/rows/elapsedMs)
- [ ] TS interceptors log external.call.* with host/method/status/latencyMs
- [ ] LLM logs: model + tokens + latency; prompt_hash/output_hash; no raw prompts/outputs

**Ops & Budgets**
- [ ] Sampling configured via env (LOG_SAMPLE_*, LOG_MAX_EVENT_BYTES); performance budget respected (<5% overhead)
- [ ] Log rotation and local retention set (daily + 100MB, keep 10)
- [ ] Receipts emitted + receipt_id referenced for privileged actions
```

---

## 7) LLM Export Tips (when asking an LLM to analyze failures)
- Export only the last N minutes and rows that match the traceId or requestId.
- Sort by traceId, then monotonic_hw_time_ms; group by service.
- Include fields: event_id, caused_by, links[], job_id/queue_name/message_id/schedule_id, workflow_id/saga_id, component, phase, error.*, severity_code, user_impact.
- Ask the LLM: “Build a timeline of the failure. Show the causal chain using event_id/caused_by/links. Rank root cause candidates.”
