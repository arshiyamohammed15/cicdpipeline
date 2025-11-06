# TinyLlama Model Configuration - Shared Services Plane

This directory contains the TinyLlama model configuration for the shared services plane, as per `storage-scripts/folder-business-rules.md`.

## Configuration

The `config.json` file contains:
- Model name and ID
- Provider information
- Default model options (optimized for concise, direct responses)
- Concise options preset for even more focused answers

### Default Options (for balanced responses):
- `temperature: 0.2` - Lower for more deterministic, focused responses
- `top_p: 0.6` - Focused sampling
- `top_k: 20` - Fewer token options
- `num_predict: 100` - Limit response length
- `repeat_penalty: 1.1` - Reduce repetition

### Concise Options (for very direct, no-fluff responses):
- `temperature: 0.1` - Very deterministic
- `top_p: 0.5` - Narrow sampling
- `top_k: 10` - Very few token options
- `num_predict: 50` - Short responses
- `repeat_penalty: 1.2` - Strong anti-repetition

## Usage

The Ollama AI Agent service (`src/cloud-services/shared-services/ollama-ai-agent/`) automatically loads TinyLlama configuration from this location and uses it as the default model.

### Getting Concise Responses

For direct, no-fluff answers, use the `--options` flag with concise settings:

```bash
# Very concise response
python tools/llm_cli.py --prompt "What is the capital of India?" --options '{"temperature": 0.1, "num_predict": 50, "top_p": 0.5}'

# Or use the concise preset from config
python tools/llm_cli.py --prompt "Capital of India?" --options '{"temperature": 0.1, "top_p": 0.5, "top_k": 10, "num_predict": 50}'
```

## Location

This configuration is part of the shared services plane storage structure:
- Path: `shared/llm/tinyllama/`
- Per folder-business-rules.md section 4.4: `llm/(guardrails|routing|tools|ollama|tinyllama)/`

