#!/usr/bin/env python3
"""
K6 SLO validation script.

Validates that k6 performance test results meet latency SLOs from NFR-1:
- ≤50ms p95 / 10ms p50 for simple chat requests
- ≤80ms p95 / 20ms p50 for full safety suite requests

Test Plan Reference: PT-LLM-01
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SLO_THRESHOLDS = {
    "llm_gateway_simple_chat_latency_ms": {"p95": 50, "p50": 10},
    "llm_gateway_full_safety_latency_ms": {"p95": 80, "p50": 20},
}


def validate_k6_results(results_file: Path) -> list[str]:
    """Validate k6 JSON results against SLO thresholds."""
    errors = []
    
    if not results_file.exists():
        return [f"K6 results file not found: {results_file}"]
    
    try:
        with results_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        metrics = data.get("metrics", {})
        
        for metric_name, thresholds in SLO_THRESHOLDS.items():
            if metric_name not in metrics:
                errors.append(f"Missing required metric: {metric_name}")
                continue
            
            metric = metrics[metric_name]
            values = metric.get("values", {})
            
            p95 = values.get("p(95)")
            p50 = values.get("p(50)")
            
            if p95 is None or p50 is None:
                errors.append(f"{metric_name}: Missing p95 or p50 values")
                continue
            
            if p95 > thresholds["p95"]:
                errors.append(
                    f"{metric_name}: p95 latency {p95:.2f}ms exceeds SLO {thresholds['p95']}ms"
                )
            
            if p50 > thresholds["p50"]:
                errors.append(
                    f"{metric_name}: p50 latency {p50:.2f}ms exceeds SLO {thresholds['p50']}ms"
                )
        
        # Check error rate
        error_rate_metric = metrics.get("llm_gateway_errors", {})
        error_rate = error_rate_metric.get("values", {}).get("rate", 0)
        if error_rate > 0.01:  # 1% threshold
            errors.append(f"Error rate {error_rate:.2%} exceeds 1% threshold")
    
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in results file: {exc}")
    except Exception as exc:
        errors.append(f"Error parsing k6 results: {exc}")
    
    return errors


def main() -> int:
    """Main validation function."""
    if len(sys.argv) < 2:
        print("Usage: validate_k6_slo.py <k6_results.json>")
        sys.exit(1)
    
    results_file = Path(sys.argv[1])
    errors = validate_k6_results(results_file)
    
    if errors:
        print("SLO VALIDATION FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1
    else:
        print("SLO VALIDATION PASSED: All latency thresholds met")
        return 0


if __name__ == "__main__":
    sys.exit(main())

