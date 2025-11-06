# Quick Reference: Getting Concise LLM Responses

## Problem
By default, LLM responses can be verbose and include unnecessary explanations. You want direct, factual answers.

## Solution: Use Lower Temperature and Response Limits

### Method 1: Use Concise Options Flag (Recommended)

```bash
# Direct answer - "New Delhi"
python tools/llm_cli.py --prompt "What is the capital of India?" --options '{\"temperature\": 0.1, \"num_predict\": 50, \"top_p\": 0.5, \"top_k\": 10}'
```

### Method 2: Use Updated Default Configuration

The default configuration has been updated to be more concise:
- Temperature: 0.2 (was 0.7) - More deterministic
- num_predict: 100 - Limits response length
- top_p: 0.6 (was 0.9) - More focused sampling

So even without `--options`, responses will be more concise than before.

### Method 3: Shorter Prompts

Keep your prompts short and direct:
```bash
# Good: Direct question
python tools/llm_cli.py --prompt "Capital of India?"

# Avoid: Long explanations in prompt
python tools/llm_cli.py --prompt "What is the capital of India? Please provide a detailed explanation with historical context..."
```

## Key Parameters for Concise Responses

| Parameter | Default | Concise | Effect |
|-----------|---------|---------|--------|
| `temperature` | 0.2 | 0.1 | Lower = more deterministic, less creative |
| `num_predict` | 100 | 50 | Limits max response length |
| `top_p` | 0.6 | 0.5 | Narrower sampling = more focused |
| `top_k` | 20 | 10 | Fewer token choices = more direct |
| `repeat_penalty` | 1.1 | 1.2 | Reduces repetition |

## Examples

```bash
# Very concise (one-word answer expected)
python tools/llm_cli.py --prompt "Capital of India?" --options '{\"temperature\": 0.1, \"num_predict\": 20}'

# Balanced concise (short answer)
python tools/llm_cli.py --prompt "What is Python?" --options '{\"temperature\": 0.2, \"num_predict\": 50}'

# Default (already optimized for conciseness)
python tools/llm_cli.py --prompt "What is Python?"
```

## Answer to Your Question

**Capital of India: New Delhi**

The concise options (`temperature: 0.1, num_predict: 50`) will give you direct answers like "New Delhi" instead of verbose explanations.

