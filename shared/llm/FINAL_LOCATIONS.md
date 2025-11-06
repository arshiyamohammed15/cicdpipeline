# Final Locations - Ollama and TinyLlama in Shared Plane

## ✅ CORRECT LOCATIONS (Per folder-business-rules.md)

Ollama and TinyLlama are now installed in the **actual shared plane**, NOT in the repository folder structure.

### ZU_ROOT
- **Value**: `D:\ZeroUI\development`
- **Per**: folder-business-rules.md section 2 and environments.json

### Ollama
- **Location**: `D:\ZeroUI\development\shared\llm\ollama\`
- **Executable**: `D:\ZeroUI\development\shared\llm\ollama\bin\ollama.exe`
- **Configuration**: `D:\ZeroUI\development\shared\llm\ollama\config.json`

### TinyLlama
- **Location**: `D:\ZeroUI\development\shared\llm\tinyllama\`
- **Models**: `D:\ZeroUI\development\shared\llm\tinyllama\manifests\`
- **Configuration**: `D:\ZeroUI\development\shared\llm\tinyllama\config.json`

## ❌ INCORRECT LOCATIONS (Removed from Repo)

The following locations in the repository have been **removed**:
- ~~`D:\Projects\ZeroUI2.0\shared\llm\ollama\`~~ (moved to shared plane)
- ~~`D:\Projects\ZeroUI2.0\shared\llm\tinyllama\`~~ (moved to shared plane)

## Environment Variables

- **ZU_ROOT**: `D:\ZeroUI\development` (User environment variable)
- **OLLAMA_MODELS**: `D:\ZeroUI\development\shared\llm\tinyllama` (User environment variable)

## Compliance

✅ **Per folder-business-rules.md section 4.4:**
- Structure: `{ZU_ROOT}/shared/llm/(guardrails|routing|tools|ollama|tinyllama)/`
- All files in actual shared plane: `D:\ZeroUI\development\shared\llm/`
- NOT in repository: `D:\Projects\ZeroUI2.0\shared/`

## Service Code

The service code (`src/cloud-services/shared-services/ollama-ai-agent/services.py`) now:
1. Reads `ZU_ROOT` environment variable
2. Loads configuration from `{ZU_ROOT}/shared/llm/ollama/config.json`
3. Loads configuration from `{ZU_ROOT}/shared/llm/tinyllama/config.json`
4. Falls back to repo location only if ZU_ROOT is not set (for development/testing)

## Usage

```powershell
# Set ZU_ROOT (if not already set)
$env:ZU_ROOT = "D:\ZeroUI\development"

# Start Ollama
D:\ZeroUI\development\shared\llm\ollama\bin\ollama.exe serve

# Use LLM CLI (will use ZU_ROOT automatically)
python tools/llm_cli.py --start-service
python tools/llm_cli.py --prompt "What is Python?"
```

