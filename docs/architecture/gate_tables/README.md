# Gate Tables

This directory contains deterministic gate decision tables in CSV format. Each gate has its own CSV file defining the rubric for decision-making.

## Gate Table Format

Each CSV file follows this structure:

```csv
condition,threshold,decision,reason_code,priority
```

### Columns

- **condition**: The condition to evaluate (e.g., "pr_size_lines", "risk_score")
- **threshold**: The threshold value for the condition
- **decision**: The decision outcome (pass, warn, soft_block, hard_block)
- **reason_code**: A code identifying the reason for the decision
- **priority**: Priority level (1-5, where 5 is highest)

### Decision Values

- `pass`: Gate passes, no action required
- `warn`: Gate passes with warning, user should review
- `soft_block`: Gate blocks but can be overridden
- `hard_block`: Gate blocks and cannot be overridden

## Available Gates

1. **gate_pr_size.csv** - PR Size Gate
   - Evaluates pull request size (lines changed, files changed)
   - Thresholds: Small (< 100 lines), Medium (100-500), Large (500-1000), Very Large (> 1000)

## Adding New Gates

To add a new gate:

1. Create a CSV file named `gate_<name>.csv`
2. Define the rubric rows with conditions, thresholds, and decisions
3. Update this README to list the new gate
4. Ensure the gate table loader can parse the CSV format

## Validation

Gate tables must:
- Be valid CSV format
- Have required columns (condition, threshold, decision, reason_code, priority)
- Have valid decision values (pass, warn, soft_block, hard_block)
- Have numeric thresholds where applicable
- Have priority values between 1-5

