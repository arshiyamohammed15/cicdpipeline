# ZeroUI No-Duplicate Implementation Map
## 0) Repo anchors (observed paths; confirm in your working tree)
The following module directories were observed in the current repository snapshot (confirm locally via `git ls-files` if needed):

Single source of truth. PRs must reference this file.

This map assigns a single owner module per enforcement phase. If behavior needs to change, edit
only the owner module and the listed paths. Do not re-implement the phase elsewhere.

## PH-B1 Token Budgets (Token runtime enforcement)
Owner Module: `src/cloud_services/llm_gateway/`

Enforcement Choke-Point(s):
- `src/cloud_services/llm_gateway/services/llm_gateway_service.py::LLMGatewayService._process`

Allowed Repo Paths (ONLY these):
- `src/shared_libs/token_budget/`
- `src/shared_libs/token_counter/`
- `src/cloud_services/llm_gateway/services/llm_gateway_service.py`
- `src/cloud_services/llm_gateway/clients/policy_client.py`
- `config/policies/platform_policy.json`

Config/Policy Source:
- `config/policies/platform_policy.json` keys `token_budgets.max_input_tokens`, `token_budgets.max_output_tokens`, `token_budgets.max_total_tokens` (fallback to `bounds.*` in the same file; see `src/cloud_services/llm_gateway/clients/policy_client.py`)
- `LLM_GATEWAY_POLICY_PATH` overrides the policy file path (`src/cloud_services/llm_gateway/clients/policy_client.py`)

Receipt required fields (metadata only):
- event_type: `llm_gateway_decision`
- decision, reason_code
- policy_snapshot_id, policy_version_ids
- request_id
- timestamp_utc
- estimated_input_tokens, requested_output_tokens, budget_spec
- trace_id when present

Boundary Rule: enforcement elsewhere = duplication bug.

Tests:
- `tests/shared_libs/test_token_budget.py` -> `python -m pytest tests/shared_libs/test_token_budget.py`
- `tests/shared_libs/test_token_counter.py` -> `python -m pytest tests/shared_libs/test_token_counter.py`
- `tests/llm_gateway/test_budget_enforcement_unit.py` -> `python -m pytest tests/llm_gateway/test_budget_enforcement_unit.py`
- `tests/llm_gateway/test_policy_config_budget_override.py` -> `python -m pytest tests/llm_gateway/test_policy_config_budget_override.py`

Do NOT Touch modules:
- `src/cloud_services/shared-services/alerting-notification-service/`
- `src/cloud_services/client-services/integration-adapters/`
- `src/cloud_services/shared-services/ollama-ai-agent/`

## PH-B3 / PH-B4 Error Recovery Patterns
Owner Module: `src/shared_libs/error_recovery/`

Enforcement Choke-Point(s):
- `src/cloud_services/llm_gateway/services/llm_gateway_service.py::LLMGatewayService._call_provider`
- `src/cloud_services/shared-services/ollama-ai-agent/services.py::OllamaAIService.check_ollama_available`
- `src/cloud_services/shared-services/ollama-ai-agent/services.py::OllamaAIService.process_prompt`
- `src/cloud_services/shared-services/ollama-ai-agent/llm_manager.py::_is_ollama_running`

Allowed Repo Paths (ONLY these):
- `src/shared_libs/error_recovery/`
- `src/cloud_services/llm_gateway/services/llm_gateway_service.py`
- `src/cloud_services/llm_gateway/clients/policy_client.py`
- `src/cloud_services/shared-services/ollama-ai-agent/services.py`
- `src/cloud_services/shared-services/ollama-ai-agent/llm_manager.py`
- `config/policies/platform_policy.json`

Config/Policy Source:
- LLM Gateway: `config/policies/platform_policy.json` keys `recovery.max_attempts`, `recovery.base_delay_ms`, `recovery.max_delay_ms` (via `_extract_recovery`)
- Ollama AI Agent: `_DEFAULT_RECOVERY_POLICY` in `src/cloud_services/shared-services/ollama-ai-agent/services.py` and `src/cloud_services/shared-services/ollama-ai-agent/llm_manager.py` (no policy file)

Receipt required fields (metadata only):
- event_type: `llm_gateway_decision`
- decision, reason_code
- policy_snapshot_id, policy_version_ids
- request_id
- timestamp_utc
- recovery.primary.recovery_applied, recovery.primary.attempts_made, recovery.primary.final_outcome, recovery.primary.last_error_code, recovery.primary.timeout_applied_ms
- recovery.fallback.* when present
- trace_id when present

Boundary Rule: enforcement elsewhere = duplication bug.

Tests:
- `tests/shared_libs/test_error_recovery.py` -> `python -m pytest tests/shared_libs/test_error_recovery.py`
- `tests/llm_gateway/test_recovery_receipts_unit.py` -> `python -m pytest tests/llm_gateway/test_recovery_receipts_unit.py`
- `tests/platform_smoke/test_platform_smoke.py` -> `python -m pytest tests/platform_smoke/test_platform_smoke.py`

Do NOT Touch modules:
- `src/cloud_services/client-services/integration-adapters/`
- `src/cloud_services/shared-services/alerting-notification-service/`
- `src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/`

## PH-C5 SSE Stream Limits
Scope: Outbound SSE/tool streams only. Inbound SSE endpoints are tracked under "Inbound SSE limits" below.

Owner Module (outbound SSE/tool streams): `src/shared_libs/sse_guard/`

Enforcement Choke-Point(s):
- TODO: No outbound SSE/tool stream enforcement found as of 2026-01-01. Search: `rg -n "event-stream|EventSourceResponse|EventSource" -S .`

Allowed Repo Paths (ONLY these):
- `src/shared_libs/sse_guard/`
- `config/policies/platform_policy.json`

Config/Policy Source (when wired):
- `config/policies/platform_policy.json` keys `sse_limits.max_events`, `sse_limits.max_bytes`, `sse_limits.max_duration_ms`

Receipt required fields (metadata only):
- type: `sse_guard_terminated`
- tenant_id
- timestamp
- metadata.reason_code, metadata.decision, metadata.stream_id
- metadata.limits, metadata.observed
- metadata.policy_ref when present

Boundary Rule: enforcement elsewhere = duplication bug.

Tests:
- `tests/shared_libs/test_sse_guard.py` -> `python -m pytest tests/shared_libs/test_sse_guard.py`

Do NOT Touch modules:
- `src/cloud_services/llm_gateway/`
- `src/cloud_services/client-services/integration-adapters/`
- `src/cloud_services/shared-services/ollama-ai-agent/`

### Inbound SSE limits
Owner Module: `src/cloud_services/shared-services/alerting-notification-service/`

Enforcement Choke-Point(s):
- `src/cloud_services/shared-services/alerting-notification-service/routes/v1.py::stream_alerts`

Allowed Repo Paths (ONLY these):
- `src/shared_libs/sse_guard/`
- `src/cloud_services/shared-services/alerting-notification-service/routes/v1.py`
- `src/cloud_services/shared-services/alerting-notification-service/clients/policy_client.py`
- `src/cloud_services/shared-services/alerting-notification-service/config.py`
- `config/policies/platform_policy.json`

Config/Policy Source:
- `config/policies/platform_policy.json` keys `sse_limits.max_events`, `sse_limits.max_bytes`, `sse_limits.max_duration_ms` (policy client also accepts `stream_limits.*`)
- `AGENT_STREAM_MAX_DURATION_MS`, `AGENT_STREAM_MAX_EVENTS`, `AGENT_STREAM_MAX_BYTES` in `src/cloud_services/shared-services/alerting-notification-service/config.py`

Receipt required fields (metadata only):
- type: `sse_guard_terminated`
- tenant_id
- timestamp
- metadata.reason_code, metadata.decision, metadata.stream_id
- metadata.limits, metadata.observed
- metadata.policy_ref when present

Boundary Rule: enforcement elsewhere = duplication bug.

Tests:
- `tests/shared_libs/test_sse_guard.py` -> `python -m pytest tests/shared_libs/test_sse_guard.py`
- `tests/cloud_services/shared_services/alerting_notification_service/integration/test_stream_guard_limits.py` -> `python -m pytest tests/cloud_services/shared_services/alerting_notification_service/integration/test_stream_guard_limits.py`
- `tests/platform_smoke/test_platform_smoke.py` -> `python -m pytest tests/platform_smoke/test_platform_smoke.py`

Do NOT Touch modules:
- `src/cloud_services/llm_gateway/`
- `src/cloud_services/client-services/integration-adapters/`
- `src/cloud_services/shared-services/ollama-ai-agent/`

## PH-C3 Tool Output Schema Validation
Owner Module (validation logic): `src/shared_libs/tool_schema_validation/` (EPC-12)
Invoker Module (acceptance point): `src/cloud_services/client-services/integration-adapters/` (PM-5)

Enforcement Choke-Point(s):
- `src/cloud_services/client-services/integration-adapters/services/integration_service.py::IntegrationService.execute_action`

Invocation Rule:
- PM-5 calls EPC-12 validator at the single acceptance point; PM-5 must not implement schema rules.

Allowed Repo Paths (ONLY these):
- `src/shared_libs/tool_schema_validation/`
- `src/cloud_services/client-services/integration-adapters/services/integration_service.py`
- `src/cloud_services/client-services/integration-adapters/config.py`
- `config/policies/platform_policy.json`

Config/Policy Source:
- `config/policies/platform_policy.json` keys `tool_schema_registry.default_schema_version`, `tool_schema_registry.tools.{tool_id}.schema_version`
- `INTEGRATION_ADAPTERS_TOOL_SCHEMA_REGISTRY_PATH` path override in `src/cloud_services/client-services/integration-adapters/config.py`

Receipt required fields (metadata only):
- operation_type: `integration.action.{provider_id}.{canonical_type}.output_validation`
- tenant_id, connection_id, provider_id
- request_metadata (redacted)
- result.tool_id, result.reason_code, result.validation_summary, result.schema_version, result.outcome, result.timestamp
- correlation_id when present

Boundary Rule: enforcement elsewhere = duplication bug.

Tests:
- `tests/shared_libs/test_tool_schema_validation.py` -> `python -m pytest tests/shared_libs/test_tool_schema_validation.py`
- `tests/cloud_services/client_services/integration_adapters/unit/test_tool_output_validation.py` -> `python -m pytest tests/cloud_services/client_services/integration_adapters/unit/test_tool_output_validation.py`
- `tests/platform_smoke/test_platform_smoke.py` -> `python -m pytest tests/platform_smoke/test_platform_smoke.py`

Do NOT Touch modules:
- No module besides EPC-12 can implement schema validation logic.
- `src/cloud_services/llm_gateway/`
- `src/cloud_services/shared-services/alerting-notification-service/`
- `src/cloud_services/shared-services/ollama-ai-agent/`

## PH-C1 MCP Server Registration + Pinning
Owner Module: `src/shared_libs/mcp_server_registry/`

Enforcement Choke-Point(s):
- `src/shared_libs/mcp_server_registry/__init__.py::MCPClientFactory.create_client`
- `src/shared_libs/mcp_server_registry/__init__.py::MCPVerifier.verify`

Allowed Repo Paths (ONLY these):
- `src/shared_libs/mcp_server_registry/`
- `tools/mcp_registry_cli.py`
- `config/mcp_server_registry.json`
- `config/policies/platform_policy.json`

Config/Policy Source:
- `config/mcp_server_registry.json` keys `servers[*].server_id`, `servers[*].endpoint`, `servers[*].enabled`, `servers[*].pinned_version`, `servers[*].pinned_digest`
- `config/policies/platform_policy.json` keys `mcp_registry.servers[*].server_id`, `mcp_registry.servers[*].endpoint`, `mcp_registry.servers[*].enabled`, `mcp_registry.servers[*].pinned_version`, `mcp_registry.servers[*].pinned_digest`

Receipt required fields (metadata only):
- event_type: `mcp_verification`
- decision, reason_code
- server_id, pinned_version, pinned_digest
- policy_ref
- timestamp_utc

Boundary Rule: enforcement elsewhere = duplication bug.

Tests:
- `tests/shared_libs/test_mcp_server_registry.py` -> `python -m pytest tests/shared_libs/test_mcp_server_registry.py`
- `tests/shared_libs/test_mcp_server_verifier.py` -> `python -m pytest tests/shared_libs/test_mcp_server_verifier.py`
- `tests/shared_libs/test_mcp_registry_cli.py` -> `python -m pytest tests/shared_libs/test_mcp_registry_cli.py`
- `tests/platform_smoke/test_platform_smoke.py` -> `python -m pytest tests/platform_smoke/test_platform_smoke.py`

Do NOT Touch modules:
- `src/cloud_services/llm_gateway/`
- `src/cloud_services/client-services/integration-adapters/`
- `src/cloud_services/shared-services/alerting-notification-service/`
