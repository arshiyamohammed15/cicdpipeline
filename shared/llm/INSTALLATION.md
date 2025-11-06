# LLM Services Installation - Shared Services Plane

This document describes the installation of Ollama and TinyLlama in the shared services plane, per `storage-scripts/folder-business-rules.md`.

## Installation Location

Both Ollama and TinyLlama are installed in the shared services plane storage structure:

- **Ollama**: `shared/llm/ollama/`
- **TinyLlama**: `shared/llm/tinyllama/`

This follows the folder-business-rules.md section 4.4 specification:
`llm/(guardrails|routing|tools|ollama|tinyllama)/`

## Configuration Files

### Ollama Configuration
- **Location**: `shared/llm/ollama/config.json`
- **Contents**: Service base URL, timeout, API endpoints
- **Used by**: `src/cloud-services/shared-services/ollama-ai-agent/services.py`

### TinyLlama Configuration
- **Location**: `shared/llm/tinyllama/config.json`
- **Contents**: Model ID, provider, default options (temperature, top_p, top_k)
- **Used by**: `src/cloud-services/shared-services/ollama-ai-agent/services.py`

## Integration

The Ollama AI Agent service automatically loads configuration from these locations:

1. **Configuration Loading**: The `_load_shared_services_config()` function in `services.py` reads from `shared/llm/ollama/config.json` and `shared/llm/tinyllama/config.json`

2. **Configuration Precedence**:
   - Explicit parameters (highest priority)
   - Environment variables (`OLLAMA_BASE_URL`, `OLLAMA_TIMEOUT`)
   - Shared services configuration files
   - Default values (lowest priority)

3. **CLI Integration**: The `tools/llm_cli.py` connects to the LLM service which uses the shared services configuration.

## Previous Installation

Any previous Ollama/TinyLlama installation outside the shared services folder structure is ignored. The system now exclusively uses the configuration from `shared/llm/ollama/` and `shared/llm/tinyllama/`.

## Verification

To verify the installation:
1. Check that `shared/llm/ollama/config.json` exists
2. Check that `shared/llm/tinyllama/config.json` exists
3. Start the LLM service: `python tools/llm_cli.py --start-service`
4. Test with: `python tools/llm_cli.py --health`

