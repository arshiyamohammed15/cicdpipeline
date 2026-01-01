# Platform Audit Evidence Pack

## A) Canonical Map Reference
- Path: `ZeroUI_No_Duplicate_Implementation_Map.md`
- Git blob hash (command + output):
```bash
git hash-object ZeroUI_No_Duplicate_Implementation_Map.md
```
```
34658246837e1adf37c825e96d92fff1df86a522
```

## B) Phase Table (5 phases)
| Phase | Owner Module | Primary Choke-Point | Allowed Paths (only) | Reason Codes |
| --- | --- | --- | --- | --- |
| PH-B1 Token Budgets | `src/cloud_services/llm_gateway/` | `src/cloud_services/llm_gateway/services/llm_gateway_service.py::LLMGatewayService._process` | `src/shared_libs/token_budget/`<br>`src/shared_libs/token_counter/`<br>`src/cloud_services/llm_gateway/services/llm_gateway_service.py`<br>`src/cloud_services/llm_gateway/clients/policy_client.py`<br>`config/policies/platform_policy.json` | `TOK_BUDGET_INPUT_EXCEEDED`<br>`TOK_BUDGET_OUTPUT_EXCEEDED`<br>`TOK_BUDGET_TOTAL_EXCEEDED`<br>`TOK_BUDGET_OK` |
| PH-B3/PH-B4 Error Recovery | `src/shared_libs/error_recovery/` | `src/cloud_services/llm_gateway/services/llm_gateway_service.py::LLMGatewayService._call_provider` | `src/shared_libs/error_recovery/`<br>`src/cloud_services/llm_gateway/services/llm_gateway_service.py`<br>`src/cloud_services/llm_gateway/clients/policy_client.py`<br>`src/cloud_services/shared-services/ollama-ai-agent/services.py`<br>`src/cloud_services/shared-services/ollama-ai-agent/llm_manager.py`<br>`config/policies/platform_policy.json` | Not phase-specific; recovery metadata uses `last_error_code` (exception type) in receipts. |
| PH-C5 SSE Stream Limits | `src/shared_libs/sse_guard/` | `src/shared_libs/sse_guard/__init__.py::SSEGuard.wrap` | `src/shared_libs/sse_guard/`<br>`config/policies/platform_policy.json` | `SSE_MAX_EVENTS`<br>`SSE_MAX_BYTES`<br>`SSE_MAX_DURATION` |
| PH-C3 Tool Output Schema Validation | `src/shared_libs/tool_schema_validation/` | `src/cloud_services/client-services/integration-adapters/services/integration_service.py::IntegrationService.execute_action` | `src/shared_libs/tool_schema_validation/`<br>`src/cloud_services/client-services/integration-adapters/services/integration_service.py`<br>`src/cloud_services/client-services/integration-adapters/config.py`<br>`config/policies/platform_policy.json` | `TOOL_OUTPUT_SCHEMA_VIOLATION` (enforcement)<br>`TOOL_SCHEMA_INVALID` (validator) |
| PH-C1 MCP Registration + Pinning | `src/shared_libs/mcp_server_registry/` | `src/shared_libs/mcp_server_registry/__init__.py::MCPClientFactory.create_client` | `src/shared_libs/mcp_server_registry/`<br>`tools/mcp_registry_cli.py`<br>`config/mcp_server_registry.json`<br>`config/policies/platform_policy.json` | `MCP_UNPINNED_SERVER`<br>`MCP_PIN_MISMATCH` |

## C) Choke-point Existence Proof (file + line range)
PH-B1 Token Budgets
```
src/cloud_services/llm_gateway/services/llm_gateway_service.py
lines 114-118:
  114:         }
  115:
  116:     async def _process(self, request: LLMRequest) -> LLMResponse | DryRunDecision:
  117:         scope = f"llm.{request.operation_type.value}"
  118:         await self._run_sync(self.iam_client.validate_actor, request.actor, scope)
```

PH-B3/PH-B4 Error Recovery
```
src/cloud_services/llm_gateway/services/llm_gateway_service.py
lines 296-300:
  296:         return await anyio.to_thread.run_sync(func, *args, **kwargs)
  297:
  298:     async def _call_provider(
  299:         self,
  300:         request: LLMRequest,
```

PH-C5 SSE Stream Limits
```
src/shared_libs/sse_guard/__init__.py
lines 54-58:
  54:         return self._last_termination
  55:
  56:     async def wrap(self, events: AsyncIterator[SSEEvent]) -> AsyncIterator[SSEEvent]:
  57:         """Yield events until a limit is reached, then terminate cleanly."""
  58:         start = self._clock()
```

PH-C3 Tool Output Schema Validation
```
src/cloud_services/client-services/integration-adapters/services/integration_service.py
lines 546-550:
  546:
  547:     # FR-7: Outbound Actions
  548:     def execute_action(
  549:         self, tenant_id: str, action_data: Dict[str, Any]
  550:     ) -> Optional[NormalisedAction]:
```

PH-C1 MCP Registration + Pinning
```
src/shared_libs/mcp_server_registry/__init__.py
lines 318-322:
  318:         self._verifier = verifier or MCPVerifier()
  319:
  320:     def create_client(
  321:         self,
  322:         server_id: str,
```

## D) Smoke Test Proof
Command executed:
```bash
python -m pytest -q tests/platform_smoke/
```
Final summary line:
```
.....                                                                    [100%]
```
Results file: `platform_smoke_results.txt`

## E) Receipts Proof
Receipt assertion logic (required fields):
```
tests/shared_harness/receipt_assertions.py
lines 35-120:
  35: def assert_enforcement_receipt_fields(
  36:     receipt: Mapping[str, Any],
  37:     *,
  38:     require_correlation: bool = False,
  39: ) -> None:
  40:     event_type = _find_first(
  41:         receipt,
  42:         (
  43:             ("event_type",),
  44:             ("type",),
  45:             ("operation_type",),
  46:             ("gate_id",),
  47:         ),
  48:     )
  49:     assert event_type is not None, "Missing event_type/type/operation_type"
  50:
  51:     decision = _find_first(
  52:         receipt,
  53:         (
  54:             ("decision",),
  55:             ("outcome",),
  56:             ("metadata", "decision"),
  57:             ("metadata", "outcome"),
  58:             ("decision", "status"),
  59:             ("result", "decision"),
  60:             ("result", "outcome"),
  61:             ("result", "status"),
  62:         ),
  63:     )
  64:     assert decision is not None, "Missing decision/outcome"
  65:
  66:     reason_code = _find_first(
  67:         receipt,
  68:         (
  69:             ("reason_code",),
  70:             ("metadata", "reason_code"),
  71:             ("decision", "reason_code"),
  72:             ("result", "reason_code"),
  73:         ),
  74:     )
  75:     assert reason_code is not None, "Missing reason_code"
  76:
  77:     policy_ref = _find_first(
  78:         receipt,
  79:         (
  80:             ("policy_snapshot_id",),
  81:             ("policy_version_ids",),
  82:             ("policy_snapshot_hash",),
  83:             ("inputs", "policy_snapshot_id"),
  84:             ("inputs", "policy_version_ids"),
  85:             ("inputs", "policy_snapshot_hash"),
  86:             ("policy_schema_version",),
  87:             ("schema_version",),
  88:             ("result", "schema_version"),
  89:             ("metadata", "policy_schema_version"),
  90:             ("policy_id",),
  91:             ("metadata", "policy_id"),
  92:             ("policy_ref",),
  93:             ("metadata", "policy_ref"),
  94:             ("pinned_version",),
  95:             ("pinned_digest",),
  96:             ("metadata", "pinned_version"),
  97:             ("metadata", "pinned_digest"),
  98:         ),
  99:     )
 100:     assert policy_ref is not None, "Missing policy reference"
 101:
 102:     timestamp = _find_first(
 103:         receipt,
 104:         (
 105:             ("timestamp_utc",),
 106:             ("timestamp",),
 107:             ("metadata", "timestamp_utc"),
 108:             ("metadata", "timestamp"),
 109:             ("result", "timestamp"),
 110:         ),
 111:     )
 112:     assert timestamp is not None, "Missing timestamp"
 113:
 114:     if require_correlation:
 115:         correlation = _find_first(
 116:             receipt,
 117:             (
 118:                 ("correlation_id",),
 119:                 ("trace_id",),
 120:                 ("request_id",),
```

Sample receipts (redacted to metadata only; payload content omitted):

PH-B1 Token Budgets
```json
{
  "budget_spec": {
    "max_input_tokens": 2048,
    "max_output_tokens": 2048,
    "max_tool_tokens_optional": null,
    "max_total_tokens": 4096
  },
  "decision": "deny",
  "estimated_input_tokens": 12,
  "event_type": "llm_gateway_decision",
  "policy_snapshot_id": "tenantA-snapshot-test",
  "policy_version_ids": [
    "pol-tena-v1"
  ],
  "reason_code": "TOK_BUDGET_OUTPUT_EXCEEDED",
  "request_id": "req-platform-audit",
  "requested_output_tokens": 4096,
  "tenant_id": "tenantA",
  "timestamp_utc": "2026-01-01T09:07:58.536525+00:00"
}
```

PH-B3/PH-B4 Error Recovery
```json
{
  "decision": "ALLOWED",
  "event_type": "llm_gateway_decision",
  "policy_snapshot_id": "tenantA-snapshot-test",
  "policy_version_ids": [
    "pol-tena-v1"
  ],
  "reason_code": "TOK_BUDGET_OK",
  "recovery": {
    "attempts_made": 2,
    "final_outcome": "success",
    "last_error_code": "TimeoutError",
    "recovery_applied": true,
    "timeout_applied_ms": 1500
  },
  "request_id": "req-platform-audit",
  "tenant_id": "tenantA",
  "timestamp_utc": "2026-01-01T09:07:58.610883+00:00"
}
```

PH-C5 SSE Stream Limits
```json
{
  "metadata": {
    "decision": "terminate",
    "limits": {
      "max_bytes": null,
      "max_duration_ms": null,
      "max_events": 1
    },
    "observed": {
      "bytes": 78,
      "duration_ms": 0,
      "events": 1
    },
    "policy_ref": "1.0.0",
    "reason_code": "SSE_MAX_EVENTS",
    "stream_id": "sub-1767238678.614755"
  },
  "tenant_id": "tenant-platform",
  "timestamp": "2026-01-01T09:07:58.614755",
  "type": "sse_guard_terminated"
}
```

PH-C3 Tool Output Schema Validation
```json
{
  "connection_id": "2a2f6e34-4126-4282-aa5a-4cc01a66d935",
  "correlation_id": "corr-1",
  "operation_type": "integration.action.platform-smoke-invalid.post_chat_message.output_validation",
  "provider_id": "platform-smoke-invalid",
  "result": {
    "outcome": "blocked",
    "reason_code": "TOOL_OUTPUT_SCHEMA_VIOLATION",
    "schema_version": "1.0.0",
    "timestamp": "2026-01-01T09:07:59.926279",
    "tool_id": "platform-smoke-invalid.post_chat_message",
    "validation_summary": {
      "error_count": 1,
      "summary": "13 validation errors for NormalisedActionResponse"
    }
  },
  "tenant_id": "tenant-tool"
}
```

PH-C1 MCP Registration + Pinning
```json
{
  "decision": "deny",
  "event_type": "mcp_verification",
  "pinned_digest": null,
  "pinned_version": null,
  "policy_ref": "mcp.unpinned",
  "reason_code": "MCP_UNPINNED_SERVER",
  "server_id": "mcp.unpinned",
  "timestamp_utc": "2026-01-01T09:07:59.930024+00:00"
}
```

## F) CI Gate Proof
Workflow: `.github/workflows/platform_gate.yml`
- Job name: `platform_gate`
- Boundary check command: `python scripts/boundary_check.py --diff-range ${{ github.event.pull_request.base.sha }}...${{ github.sha }} --strict`
- Smoke test command: `python -m pytest tests/platform_smoke/`
```yaml
name: Platform Gate

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  platform_gate:
    name: Platform Gate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Run boundary check
        if: github.event_name == 'pull_request'
        run: |
          python scripts/boundary_check.py --diff-range ${{ github.event.pull_request.base.sha }}...${{ github.sha }} --strict
      - name: Run platform smoke tests
        run: |
          python -m pytest tests/platform_smoke/
```

### Branch Protection Verification (Out-of-Repo)
Branch protection / required checks are NOT stored in the repo; they cannot be proven from code alone.

UI verification checklist (GitHub):
1) Open any PR -> Checks tab -> copy exact check names for the platform gate and boundary check.
2) Repo Settings -> Branches -> Branch protection rules -> ensure:
   - Require a pull request before merging (ON)
   - Require status checks to pass before merging (ON)
   - Select the exact gate checks (platform gate + boundary check)
   - (Recommended) Require branches to be up to date before merging (ON)
3) Save the rule.

CLI verification (GitHub CLI) with placeholders:
```bash
gh api -H "Accept: application/vnd.github+json" repos/{OWNER}/{REPO}/branches/{BRANCH}/protection > branch_protection.json
```

Evidence artifacts to capture:
- Screenshot: PR Checks tab showing gate checks passing
- Screenshot: Branch protection rule showing required checks selected
- OR file: `branch_protection.json` (CLI output)
