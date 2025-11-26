#!/usr/bin/env python3
"""
Observability validation script for LLM Gateway.

Per §14.4 and OT-LLM-01, validates that logs, metrics, and traces contain
all required fields:
- Metrics: epc6_requests_total{decision}, epc6_latency_ms{workflow}, epc6_degradation_total
- Structured log fields: tenant_id, risk_class, policy_snapshot_id
- Trace attributes: actor, tenant, logical_model_id, policy_snapshot_id, decision
- ERIS receipts: all fields PM-7 ingestion mandates

Test Plan Reference: OT-LLM-01
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set

# Required fields per §14.4
REQUIRED_METRICS = {
    "epc6_requests_total",
    "epc6_latency_ms",
    "epc6_degradation_total",
}

REQUIRED_LOG_FIELDS = {
    "tenant_id",
    "risk_class",
    "policy_snapshot_id",
}

REQUIRED_TRACE_ATTRIBUTES = {
    "actor",
    "tenant",
    "logical_model_id",
    "policy_snapshot_id",
    "decision",
}

REQUIRED_RECEIPT_FIELDS = {
    "receipt_id",
    "request_id",
    "decision",
    "policy_snapshot_id",
    "policy_version_ids",
    "risk_flags",
    "fail_open",
    "tenant_id",
    "timestamp_utc",
}


def validate_metrics(log_content: str) -> List[str]:
    """Validate Prometheus metrics contain required fields."""
    errors = []
    found_metrics: Set[str] = set()

    # Check for metric patterns
    for metric in REQUIRED_METRICS:
        pattern = rf"{re.escape(metric)}\{{[^}}]*\}}"
        if re.search(pattern, log_content):
            found_metrics.add(metric)
        else:
            errors.append(f"Missing required metric: {metric}")

    # Check for decision label in requests_total
    if "epc6_requests_total" in found_metrics:
        if not re.search(r'epc6_requests_total\{[^}]*decision=', log_content):
            errors.append("epc6_requests_total missing 'decision' label")

    # Check for workflow label in latency_ms
    if "epc6_latency_ms" in found_metrics:
        if not re.search(r'epc6_latency_ms\{[^}]*workflow=', log_content):
            errors.append("epc6_latency_ms missing 'workflow' label")

    return errors


def validate_structured_logs(log_content: str) -> List[str]:
    """Validate structured log entries contain required fields."""
    errors = []
    log_entries = []

    # Extract JSON log entries
    for line in log_content.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Try to parse as JSON
        try:
            # Handle both pure JSON and log lines with JSON
            json_match = re.search(r'\{.*\}', line)
            if json_match:
                entry = json.loads(json_match.group())
                log_entries.append(entry)
        except (json.JSONDecodeError, AttributeError):
            continue

    if not log_entries:
        errors.append("No structured log entries found")
        return errors

    # Check required fields in at least one entry
    found_fields: Set[str] = set()
    for entry in log_entries:
        for field in REQUIRED_LOG_FIELDS:
            if field in entry:
                found_fields.add(field)

    for field in REQUIRED_LOG_FIELDS:
        if field not in found_fields:
            errors.append(f"Missing required log field: {field}")

    # Check for sensitive content (should be redacted)
    for entry in log_entries:
        entry_str = json.dumps(entry)
        if re.search(r'sk_[A-Za-z0-9]{20,}', entry_str):
            errors.append("Log contains unredacted API key pattern")
        if re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', entry_str):
            errors.append("Log contains unredacted email pattern")

    return errors


def validate_traces(trace_content: str) -> List[str]:
    """Validate trace attributes contain required fields."""
    errors = []
    found_attributes: Set[str] = set()

    # Check for trace attribute patterns (OpenTelemetry format)
    for attr in REQUIRED_TRACE_ATTRIBUTES:
        # Look for attribute in various formats
        patterns = [
            rf'"{re.escape(attr)}"\s*:\s*"[^"]*"',
            rf'{re.escape(attr)}\s*=\s*"[^"]*"',
            rf'\.{re.escape(attr)}\s*=\s*"[^"]*"',
        ]
        found = False
        for pattern in patterns:
            if re.search(pattern, trace_content, re.IGNORECASE):
                found = True
                break
        if found:
            found_attributes.add(attr)
        else:
            errors.append(f"Missing required trace attribute: {attr}")

    # Check for sensitive content in traces
    if re.search(r'sk_[A-Za-z0-9]{20,}', trace_content):
        errors.append("Trace contains unredacted API key pattern")

    return errors


def validate_receipts(receipt_file: Path) -> List[str]:
    """Validate ERIS receipts contain all required fields."""
    errors = []

    if not receipt_file.exists():
        errors.append(f"Receipt file not found: {receipt_file}")
        return errors

    try:
        with receipt_file.open("r", encoding="utf-8") as f:
            content = f.read()
            # Try to parse as JSONL (one receipt per line)
            receipts = []
            for line in content.split("\n"):
                line = line.strip()
                if not line:
                    continue
                try:
                    receipt = json.loads(line)
                    receipts.append(receipt)
                except json.JSONDecodeError:
                    continue

            if not receipts:
                errors.append("No valid receipts found in file")
                return errors

            # Check required fields in each receipt
            for i, receipt in enumerate(receipts):
                missing_fields = []
                for field in REQUIRED_RECEIPT_FIELDS:
                    if field not in receipt:
                        missing_fields.append(field)

                if missing_fields:
                    errors.append(
                        f"Receipt {i+1} missing fields: {', '.join(missing_fields)}"
                    )

                # Check for sensitive content (should not be in receipts)
                receipt_str = json.dumps(receipt)
                if re.search(r'sk_[A-Za-z0-9]{20,}', receipt_str):
                    errors.append(f"Receipt {i+1} contains unredacted API key")
                if re.search(
                    r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', receipt_str
                ):
                    errors.append(f"Receipt {i+1} contains unredacted email")

    except Exception as exc:
        errors.append(f"Error reading receipt file: {exc}")

    return errors


def main():
    """Main validation function."""
    if len(sys.argv) < 2:
        print("Usage: validate_llm_gateway_observability.py <log_file> [receipt_file]")
        sys.exit(1)

    log_file = Path(sys.argv[1])
    receipt_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if not log_file.exists():
        print(f"ERROR: Log file not found: {log_file}")
        sys.exit(1)

    all_errors: List[str] = []

    # Read log content
    with log_file.open("r", encoding="utf-8") as f:
        log_content = f.read()

    # Validate metrics
    print("Validating metrics...")
    metric_errors = validate_metrics(log_content)
    all_errors.extend(metric_errors)
    if metric_errors:
        print(f"  FAILED: {len(metric_errors)} metric validation errors")
    else:
        print("  PASSED: All required metrics present")

    # Validate structured logs
    print("Validating structured logs...")
    log_errors = validate_structured_logs(log_content)
    all_errors.extend(log_errors)
    if log_errors:
        print(f"  FAILED: {len(log_errors)} log validation errors")
    else:
        print("  PASSED: All required log fields present")

    # Validate traces
    print("Validating traces...")
    trace_errors = validate_traces(log_content)
    all_errors.extend(trace_errors)
    if trace_errors:
        print(f"  FAILED: {len(trace_errors)} trace validation errors")
    else:
        print("  PASSED: All required trace attributes present")

    # Validate receipts if provided
    if receipt_file:
        print("Validating receipts...")
        receipt_errors = validate_receipts(receipt_file)
        all_errors.extend(receipt_errors)
        if receipt_errors:
            print(f"  FAILED: {len(receipt_errors)} receipt validation errors")
        else:
            print("  PASSED: All required receipt fields present")

    # Summary
    print("\n" + "=" * 60)
    if all_errors:
        print(f"VALIDATION FAILED: {len(all_errors)} errors found")
        print("\nErrors:")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("VALIDATION PASSED: All observability requirements met")
        sys.exit(0)


if __name__ == "__main__":
    main()

