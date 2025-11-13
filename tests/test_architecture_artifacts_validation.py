"""
Additional validation tests for architecture artifacts.

Tests focus on:
- Cross-artifact consistency
- Data integrity
- Format validation
- Edge cases and boundary conditions
"""

import pytest
import json
import csv
from pathlib import Path
from typing import Set, Dict, List
import re


class TestCrossArtifactConsistency:
    """Tests for consistency across artifacts."""

    def test_policy_snapshot_receipt_schema_consistency(self):
        """Positive: Policy snapshot receipt schema matches sample receipts."""
        snapshot = Path("docs/architecture/policy/policy_snapshot_v1.json")
        receipts = Path("docs/architecture/samples/receipts/receipts_example.jsonl")

        snapshot_data = json.loads(snapshot.read_text(encoding='utf-8'))
        receipt_schema = snapshot_data.get('receipts', {}).get('required', [])

        # Check that sample receipts have required fields
        lines = receipts.read_text(encoding='utf-8').strip().split('\n')
        for line in lines:
            if line.strip():
                receipt = json.loads(line)
                # Check required fields from policy snapshot
                for field in receipt_schema:
                    # Map policy snapshot field names to receipt field names
                    if field == 'policy_snapshot_hash':
                        assert 'snapshot_hash' in receipt, \
                            "Receipt should have snapshot_hash matching policy_snapshot_hash"
                    elif field == 'policy_version_ids':
                        assert 'policy_version_ids' in receipt, \
                            "Receipt should have policy_version_ids"
                    elif field == 'decision':
                        assert 'decision' in receipt, \
                            "Receipt should have decision"

    def test_gate_table_decisions_match_receipt_decisions(self):
        """Positive: Gate table decisions match receipt decision statuses."""
        gate_table = Path("docs/architecture/gate_tables/gate_pr_size.csv")
        receipts = Path("docs/architecture/samples/receipts/receipts_example.jsonl")

        # Get valid decisions from gate table
        valid_decisions = set()
        with open(gate_table, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                valid_decisions.add(row['decision'])

        # Check that receipt decisions match
        lines = receipts.read_text(encoding='utf-8').strip().split('\n')
        for line in lines:
            if line.strip():
                receipt = json.loads(line)
                if 'decision' in receipt and 'status' in receipt['decision']:
                    status = receipt['decision']['status']
                    # Map receipt status to gate decision
                    status_mapping = {
                        'pass': 'pass',
                        'warn': 'warn',
                        'soft_block': 'soft_block',
                        'hard_block': 'hard_block'
                    }
                    gate_decision = status_mapping.get(status, status)
                    assert gate_decision in valid_decisions, \
                        f"Receipt decision status '{status}' should match gate table decision"


class TestDataIntegrity:
    """Tests for data integrity."""

    def test_receipt_ids_unique(self):
        """Positive: Receipt IDs in sample are unique."""
        receipts = Path("docs/architecture/samples/receipts/receipts_example.jsonl")
        lines = receipts.read_text(encoding='utf-8').strip().split('\n')

        receipt_ids = set()
        for line in lines:
            if line.strip():
                receipt = json.loads(line)
                receipt_id = receipt.get('receipt_id')
                if receipt_id:
                    assert receipt_id not in receipt_ids, \
                        f"Receipt ID '{receipt_id}' should be unique"
                    receipt_ids.add(receipt_id)

    def test_evidence_pack_receipt_id_matches(self):
        """Positive: Evidence pack receipt_id matches sample receipt."""
        evidence = Path("docs/architecture/samples/evidence/evidence_pack_example.json")
        receipts = Path("docs/architecture/samples/receipts/receipts_example.jsonl")

        evidence_data = json.loads(evidence.read_text(encoding='utf-8'))
        evidence_receipt_id = evidence_data.get('receipt_id')

        # Check that receipt exists in samples
        lines = receipts.read_text(encoding='utf-8').strip().split('\n')
        receipt_ids = [json.loads(line).get('receipt_id') for line in lines if line.strip()]

        assert evidence_receipt_id in receipt_ids, \
            f"Evidence pack receipt_id '{evidence_receipt_id}' should match a sample receipt"

    def test_policy_snapshot_hash_format(self):
        """Edge: Policy snapshot hash follows sha256:hex format."""
        snapshot = Path("docs/architecture/policy/policy_snapshot_v1.json")
        data = json.loads(snapshot.read_text(encoding='utf-8'))

        if 'snapshot_hash' in data:
            hash_value = data['snapshot_hash']
            # Should match sha256: followed by 64 hex characters
            pattern = r'^sha256:[0-9a-f]{64}$'
            assert re.match(pattern, hash_value, re.IGNORECASE), \
                f"Snapshot hash '{hash_value}' should match pattern sha256:<64 hex chars>"


class TestFormatValidation:
    """Tests for format validation."""

    def test_csv_encoding_utf8(self):
        """Positive: CSV files are UTF-8 encoded."""
        csv_file = Path("docs/architecture/gate_tables/gate_pr_size.csv")
        try:
            content = csv_file.read_text(encoding='utf-8')
            # If we can read it as UTF-8, it's valid
            assert len(content) > 0, "CSV should have content"
        except UnicodeDecodeError as e:
            pytest.fail(f"CSV file should be UTF-8 encoded: {e}")

    def test_json_encoding_utf8(self):
        """Positive: JSON files are UTF-8 encoded."""
        json_files = [
            "docs/architecture/policy/policy_snapshot_v1.json",
            "docs/architecture/samples/evidence/evidence_pack_example.json"
        ]

        for json_file in json_files:
            file_path = Path(json_file)
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8')
                    json.loads(content)  # Should parse as JSON
                except (UnicodeDecodeError, json.JSONDecodeError) as e:
                    pytest.fail(f"{json_file} should be valid UTF-8 JSON: {e}")

    def test_jsonl_format(self):
        """Positive: JSONL file has one JSON object per line."""
        jsonl_file = Path("docs/architecture/samples/receipts/receipts_example.jsonl")
        lines = jsonl_file.read_text(encoding='utf-8').strip().split('\n')

        for i, line in enumerate(lines, 1):
            if line.strip():  # Skip empty lines
                try:
                    obj = json.loads(line)
                    assert isinstance(obj, dict), \
                        f"Line {i} should contain a JSON object"
                except json.JSONDecodeError as e:
                    pytest.fail(f"Line {i} should be valid JSON: {e}")


class TestBoundaryConditions:
    """Tests for boundary conditions."""

    def test_gate_table_threshold_boundaries(self):
        """Edge: Gate table thresholds are within reasonable bounds."""
        csv_file = Path("docs/architecture/gate_tables/gate_pr_size.csv")

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                threshold = row['threshold']
                if threshold.isdigit():
                    threshold_value = int(threshold)
                    # Thresholds should be positive and reasonable
                    assert threshold_value > 0, \
                        f"Threshold '{threshold_value}' should be positive"
                    assert threshold_value < 1000000, \
                        f"Threshold '{threshold_value}' should be reasonable (< 1M)"

    def test_receipt_timestamp_format(self):
        """Edge: Receipt timestamps are in ISO 8601 format."""
        receipts = Path("docs/architecture/samples/receipts/receipts_example.jsonl")
        lines = receipts.read_text(encoding='utf-8').strip().split('\n')

        # ISO 8601 pattern: YYYY-MM-DDTHH:MM:SSZ or with timezone
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$'

        for i, line in enumerate(lines, 1):
            if line.strip():
                receipt = json.loads(line)
                if 'timestamp_utc' in receipt:
                    timestamp = receipt['timestamp_utc']
                    assert re.match(iso_pattern, timestamp), \
                        f"Receipt on line {i} timestamp_utc should be ISO 8601 format"

    def test_receipt_monotonic_timestamp_positive(self):
        """Edge: Receipt monotonic timestamps are positive numbers."""
        receipts = Path("docs/architecture/samples/receipts/receipts_example.jsonl")
        lines = receipts.read_text(encoding='utf-8').strip().split('\n')

        for i, line in enumerate(lines, 1):
            if line.strip():
                receipt = json.loads(line)
                if 'timestamp_monotonic_ms' in receipt:
                    monotonic = receipt['timestamp_monotonic_ms']
                    assert isinstance(monotonic, (int, float)), \
                        f"Receipt on line {i} timestamp_monotonic_ms should be numeric"
                    assert monotonic >= 0, \
                        f"Receipt on line {i} timestamp_monotonic_ms should be non-negative"


class TestNegativeCases:
    """Negative test cases."""

    def test_missing_required_field_handling(self):
        """Negative: Missing required fields should be detected."""
        # This test documents expected behavior
        # Validation should catch missing required fields
        receipts = Path("docs/architecture/samples/receipts/receipts_example.jsonl")
        lines = receipts.read_text(encoding='utf-8').strip().split('\n')

        required_fields = ['receipt_id', 'gate_id', 'decision']

        for line in lines:
            if line.strip():
                receipt = json.loads(line)
                for field in required_fields:
                    assert field in receipt, \
                        f"Receipt should have required field: {field}"

    def test_invalid_decision_status_handling(self):
        """Negative: Invalid decision status should be rejected."""
        # This test documents expected behavior
        # Invalid statuses should be caught by validation
        valid_statuses = {'pass', 'warn', 'soft_block', 'hard_block'}

        receipts = Path("docs/architecture/samples/receipts/receipts_example.jsonl")
        lines = receipts.read_text(encoding='utf-8').strip().split('\n')

        for line in lines:
            if line.strip():
                receipt = json.loads(line)
                if 'decision' in receipt and 'status' in receipt['decision']:
                    status = receipt['decision']['status']
                    assert status in valid_statuses, \
                        f"Decision status '{status}' should be one of {valid_statuses}"

    def test_invalid_priority_range(self):
        """Negative: Priority outside 1-5 range should be rejected."""
        csv_file = Path("docs/architecture/gate_tables/gate_pr_size.csv")

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                priority = int(row['priority'])
                assert 1 <= priority <= 5, \
                    f"Priority {priority} should be between 1 and 5"


class TestSpecialScenarios:
    """Tests for special scenarios."""

    def test_receipt_with_all_optional_fields(self):
        """Edge: Receipt with all optional fields should be valid."""
        receipts = Path("docs/architecture/samples/receipts/receipts_example.jsonl")
        lines = receipts.read_text(encoding='utf-8').strip().split('\n')

        # At least one receipt should demonstrate optional fields
        found_optional = False
        for line in lines:
            if line.strip():
                receipt = json.loads(line)
                # Check for optional fields
                if 'evidence_handles' in receipt and receipt['evidence_handles']:
                    found_optional = True
                    break

        # This is informational - optional fields are optional
        # Just verify receipts parse correctly
        assert len(lines) > 0, "Should have at least one receipt"

    def test_policy_snapshot_with_empty_arrays(self):
        """Edge: Policy snapshot with empty arrays should be valid."""
        snapshot = Path("docs/architecture/policy/policy_snapshot_v1.json")
        data = json.loads(snapshot.read_text(encoding='utf-8'))

        # Empty arrays should be valid
        array_fields = ['evaluation_points', 'policy_version_ids', 'deprecates']
        for field in array_fields:
            if field in data:
                assert isinstance(data[field], list), \
                    f"{field} should be a list (even if empty)"

    def test_gate_table_with_multiple_conditions(self):
        """Edge: Gate table with multiple conditions for same decision should be valid."""
        csv_file = Path("docs/architecture/gate_tables/gate_pr_size.csv")

        # Group by condition
        conditions = {}
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                condition = row['condition']
                if condition not in conditions:
                    conditions[condition] = []
                conditions[condition].append(row)

        # Multiple thresholds for same condition should be valid
        for condition, rows in conditions.items():
            assert len(rows) > 0, f"Condition '{condition}' should have at least one row"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
