# Ollama Configuration - Shared Services Plane

This directory contains the Ollama LLM service configuration for the shared services plane, as per `storage-scripts/folder-business-rules.md`.

## Configuration

The `config.json` file contains:
- Service base URL and endpoints
- Timeout settings
- API endpoint paths

## Usage

The Ollama AI Agent service (`src/cloud-services/shared-services/ollama-ai-agent/`) automatically loads configuration from this location.

Configuration precedence:
1. Explicit parameter (if provided)
2. Environment variable (`OLLAMA_BASE_URL`, `OLLAMA_TIMEOUT`)
3. This configuration file (`shared/llm/ollama/config.json`)
4. Default values

## Location

This configuration is part of the shared services plane storage structure:
- Path: `shared/llm/ollama/`
- Per folder-business-rules.md section 4.4: `llm/(guardrails|routing|tools|ollama|tinyllama)/`

