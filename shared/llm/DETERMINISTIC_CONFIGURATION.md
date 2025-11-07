# 100% Deterministic LLM Response Configuration

## Configuration Location

The configuration file is located at:
- **Path**: `{ZU_ROOT}/shared/llm/tinyllama/config.json`
- **ZU_ROOT**: `D:\ZeroUI\development` (per project configuration)

## Exact Configuration for 100% Deterministic Responses

Edit the `config.json` file and set the `default_options` field with these exact parameters:

```json
{
  "model_id": "tinyllama:latest",
  "model_name": "Tinyllama",
  "provider": "ollama",
  "default_options": {
    "temperature": 0,
    "top_k": 1,
    "top_p": 0,
    "seed": 42,
    "num_predict": 512,
    "repeat_penalty": 1.0,
    "repeat_last_n": 64,
    "tfs_z": 1.0,
    "typical_p": 1.0,
    "mirostat": 0,
    "mirostat_eta": 0.1,
    "mirostat_tau": 5.0
  }
}
```

## Parameter Explanation

### Critical Parameters for Determinism

1. **`temperature: 0`**
   - **Effect**: Completely deterministic - always selects the highest probability token
   - **Range**: 0.0 to 1.0 (0 = most deterministic)

2. **`top_k: 1`**
   - **Effect**: Only considers the top 1 token (most deterministic)
   - **Range**: 1 to infinity (1 = most deterministic)

3. **`top_p: 0`**
   - **Effect**: Disables nucleus sampling (most deterministic)
   - **Range**: 0.0 to 1.0 (0 = most deterministic)

4. **`seed: 42`**
   - **Effect**: Fixed random seed ensures identical outputs for identical inputs
   - **Note**: Use any fixed integer value (42 is example)

### Additional Parameters

5. **`num_predict: 512`**
   - **Effect**: Maximum number of tokens to generate
   - **Adjust**: Based on desired response length

6. **`repeat_penalty: 1.0`**
   - **Effect**: No penalty for repetition (1.0 = neutral)
   - **Range**: 1.0 to 2.0

7. **`repeat_last_n: 64`**
   - **Effect**: Number of tokens to consider for repetition penalty
   - **Range**: 0 to context size

8. **`tfs_z: 1.0`**
   - **Effect**: Tail-free sampling disabled (1.0 = disabled)
   - **Range**: 0.0 to 1.0

9. **`typical_p: 1.0`**
   - **Effect**: Typical sampling disabled (1.0 = disabled)
   - **Range**: 0.0 to 1.0

10. **`mirostat: 0`**
    - **Effect**: Mirostat sampling disabled (0 = disabled)
    - **Range**: 0, 1, or 2

## Implementation Steps

### Step 1: Locate Configuration File

```powershell
# Set ZU_ROOT if not already set
$env:ZU_ROOT = "D:\ZeroUI\development"

# Navigate to config location
$configPath = Join-Path $env:ZU_ROOT "shared\llm\tinyllama\config.json"
```

### Step 2: Edit Configuration File

1. Open `{ZU_ROOT}/shared/llm/tinyllama/config.json`
2. Add or update the `default_options` field with the parameters above
3. Save the file

### Step 3: Restart Service

```powershell
# Stop existing service (if running)
# Then restart
python tools/llm_cli.py --start-service
```

## Verification

Test determinism by running the same prompt twice:

```powershell
# Run same prompt twice - should produce identical output
python tools/llm_cli.py --prompt "What is 2+2?"
python tools/llm_cli.py --prompt "What is 2+2?"
```

Both responses should be **identical** (character-for-character match).

## Alternative: Per-Request Deterministic Options

If you don't want to change the default configuration, you can pass deterministic options per request:

```powershell
python tools/llm_cli.py --prompt "What is Python?" --options '{"temperature": 0, "top_k": 1, "top_p": 0, "seed": 42}'
```

## Important Notes

1. **Temperature = 0** is the most critical parameter for determinism
2. **Seed** must be fixed and consistent across requests for reproducibility
3. **top_k = 1** ensures only the highest probability token is selected
4. **top_p = 0** disables nucleus sampling completely
5. Even with these settings, model weights and prompt must be identical for 100% reproducibility

## Code Reference

The configuration is loaded in:
- **File**: `src/cloud-services/shared-services/ollama-ai-agent/services.py`
- **Line**: 131 - `model_options = self.tinyllama_config.get("default_options", {}).copy()`
- **Applied**: When `request.options` is not provided (line 141)

