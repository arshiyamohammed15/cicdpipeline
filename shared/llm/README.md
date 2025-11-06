# LLM Services - Shared Plane

**IMPORTANT**: This directory in the repository is for **configuration templates only**. 

The actual Ollama and TinyLlama installations are in the **shared plane** at:
- `{ZU_ROOT}/shared/llm/ollama/`
- `{ZU_ROOT}/shared/llm/tinyllama/`

Where `ZU_ROOT` is typically `D:\ZeroUI\development` for development environment.

## Actual Installation Locations

### Development Environment
- **ZU_ROOT**: `D:\ZeroUI\development`
- **Ollama**: `D:\ZeroUI\development\shared\llm/ollama/`
- **TinyLlama**: `D:\ZeroUI\development\shared\llm/tinyllama/`

### Configuration Files
Configuration files are stored in the actual shared plane locations, not in the repository.

## Repository Structure

The `shared/llm/` directory in the repository contains:
- Documentation files (README.md, INSTALLATION.md, etc.)
- **NOT** the actual Ollama executable or TinyLlama model files

## Per folder-business-rules.md

Per section 4.4, the structure is:
- `{ZU_ROOT}/shared/llm/(guardrails|routing|tools|ollama|tinyllama)/`

All actual installations and model files are in `{ZU_ROOT}/shared/llm/`, not in the repository.

