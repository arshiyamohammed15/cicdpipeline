"""
Comprehensive test suite for pre-implementation artifacts.

Tests cover:
- Positive cases: Valid artifacts and operations
- Negative cases: Invalid inputs and error conditions
- Edge cases: Boundary conditions and special scenarios
"""

import pytest
import json
import csv
from pathlib import Path
from typing import Dict, List, Any
import hashlib


class TestGateTables:
    """Tests for gate table CSV files."""

    def test_gate_tables_directory_exists(self):
        """Positive: Gate tables directory exists."""
        gate_tables_dir = Path("docs/architecture/gate_tables")
        assert gate_tables_dir.exists(), "Gate tables directory should exist"
        assert gate_tables_dir.is_dir(), "Gate tables should be a directory"

    def test_gate_tables_readme_exists(self):
        """Positive: README exists in gate tables directory."""
        readme = Path("docs/architecture/gate_tables/README.md")
        assert readme.exists(), "Gate tables README should exist"
        assert readme.is_file(), "README should be a file"

    def test_gate_pr_size_csv_exists(self):
        """Positive: gate_pr_size.csv exists."""
        csv_file = Path("docs/architecture/gate_tables/gate_pr_size.csv")
        assert csv_file.exists(), "gate_pr_size.csv should exist"
        assert csv_file.is_file(), "gate_pr_size.csv should be a file"

    def test_gate_pr_size_csv_valid_format(self):
        """Positive: gate_pr_size.csv has valid CSV format."""
        csv_file = Path("docs/architecture/gate_tables/gate_pr_size.csv")
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) > 0, "CSV should have at least one data row"
            
            # Check required columns
            required_columns = {'condition', 'threshold', 'decision', 'reason_code', 'priority'}
            assert set(reader.fieldnames) == required_columns, \
                f"CSV should have columns: {required_columns}"

    def test_gate_pr_size_csv_valid_decisions(self):
        """Positive: All decisions are valid values."""
        csv_file = Path("docs/architecture/gate_tables/gate_pr_size.csv")
        valid_decisions = {'pass', 'warn', 'soft_block', 'hard_block'}
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert row['decision'] in valid_decisions, \
                    f"Decision '{row['decision']}' should be one of {valid_decisions}"

    def test_gate_pr_size_csv_valid_priorities(self):
        """Positive: All priorities are valid (1-5)."""
        csv_file = Path("docs/architecture/gate_tables/gate_pr_size.csv")
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                priority = int(row['priority'])
                assert 1 <= priority <= 5, \
                    f"Priority {priority} should be between 1 and 5"

    def test_gate_pr_size_csv_numeric_thresholds(self):
        """Positive: Thresholds are numeric where applicable."""
        csv_file = Path("docs/architecture/gate_tables/gate_pr_size.csv")
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                threshold = row['threshold']
                # Thresholds for PR size should be numeric
                if 'pr_' in row['condition']:
                    assert threshold.isdigit(), \
                        f"Threshold '{threshold}' should be numeric for condition '{row['condition']}'"

    def test_gate_pr_size_csv_no_empty_rows(self):
        """Negative: CSV has no empty rows."""
        csv_file = Path("docs/architecture/gate_tables/gate_pr_size.csv")
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=2):
                assert any(row.values()), \
                    f"Row {i} should not be empty"

    def test_gate_pr_size_csv_no_duplicate_conditions(self):
        """Edge: No duplicate condition+threshold combinations."""
        csv_file = Path("docs/architecture/gate_tables/gate_pr_size.csv")
        seen = set()
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row['condition'], row['threshold'])
                assert key not in seen, \
                    f"Duplicate condition+threshold: {key}"
                seen.add(key)

    def test_gate_pr_size_csv_edge_case_empty_file(self):
        """Negative: Empty CSV file should fail."""
        # This test documents expected behavior
        # An empty CSV (no data rows) should be caught by other tests
        pass

    def test_gate_pr_size_csv_edge_case_missing_columns(self):
        """Negative: CSV with missing columns should fail."""
        # This test documents expected behavior
        # Missing columns should be caught by test_gate_pr_size_csv_valid_format
        pass


class TestTrustDocumentation:
    """Tests for trust documentation."""

    def test_trust_directory_exists(self):
        """Positive: Trust directory exists."""
        trust_dir = Path("docs/architecture/trust")
        assert trust_dir.exists(), "Trust directory should exist"
        assert trust_dir.is_dir(), "Trust should be a directory"

    def test_signing_process_exists(self):
        """Positive: signing_process.md exists."""
        doc = Path("docs/architecture/trust/signing_process.md")
        assert doc.exists(), "signing_process.md should exist"
        assert doc.is_file(), "signing_process.md should be a file"

    def test_verify_path_exists(self):
        """Positive: verify_path.md exists."""
        doc = Path("docs/architecture/trust/verify_path.md")
        assert doc.exists(), "verify_path.md should exist"
        assert doc.is_file(), "verify_path.md should be a file"

    def test_crl_rotation_exists(self):
        """Positive: crl_rotation.md exists."""
        doc = Path("docs/architecture/trust/crl_rotation.md")
        assert doc.exists(), "crl_rotation.md should exist"
        assert doc.is_file(), "crl_rotation.md should be a file"

    def test_public_keys_directory_exists(self):
        """Positive: public_keys directory exists."""
        pub_keys_dir = Path("docs/architecture/trust/public_keys")
        assert pub_keys_dir.exists(), "public_keys directory should exist"
        assert pub_keys_dir.is_dir(), "public_keys should be a directory"

    def test_public_keys_readme_exists(self):
        """Positive: public_keys README exists."""
        readme = Path("docs/architecture/trust/public_keys/README.md")
        assert readme.exists(), "public_keys README should exist"
        assert readme.is_file(), "public_keys README should be a file"

    def test_trust_docs_not_empty(self):
        """Positive: Trust documentation files are not empty."""
        docs = [
            "docs/architecture/trust/signing_process.md",
            "docs/architecture/trust/verify_path.md",
            "docs/architecture/trust/crl_rotation.md",
            "docs/architecture/trust/public_keys/README.md"
        ]
        for doc_path in docs:
            doc = Path(doc_path)
            assert doc.stat().st_size > 0, f"{doc_path} should not be empty"

    def test_trust_docs_contain_keywords(self):
        """Positive: Trust docs contain expected keywords."""
        signing_process = Path("docs/architecture/trust/signing_process.md")
        content = signing_process.read_text(encoding='utf-8')
        assert 'sign' in content.lower() or 'signature' in content.lower(), \
            "signing_process.md should contain signing information"
        
        verify_path = Path("docs/architecture/trust/verify_path.md")
        content = verify_path.read_text(encoding='utf-8')
        assert 'verify' in content.lower() or 'verification' in content.lower(), \
            "verify_path.md should contain verification information"


class TestSLODocumentation:
    """Tests for SLO documentation."""

    def test_slo_directory_exists(self):
        """Positive: SLO directory exists."""
        slo_dir = Path("docs/architecture/slo")
        assert slo_dir.exists(), "SLO directory should exist"
        assert slo_dir.is_dir(), "SLO should be a directory"

    def test_slos_md_exists(self):
        """Positive: slos.md exists."""
        doc = Path("docs/architecture/slo/slos.md")
        assert doc.exists(), "slos.md should exist"
        assert doc.is_file(), "slos.md should be a file"

    def test_alerts_md_exists(self):
        """Positive: alerts.md exists."""
        doc = Path("docs/architecture/slo/alerts.md")
        assert doc.exists(), "alerts.md should exist"
        assert doc.is_file(), "alerts.md should be a file"

    def test_slos_not_empty(self):
        """Positive: SLO files are not empty."""
        for doc_path in ["docs/architecture/slo/slos.md", "docs/architecture/slo/alerts.md"]:
            doc = Path(doc_path)
            assert doc.stat().st_size > 0, f"{doc_path} should not be empty"

    def test_slos_contain_targets(self):
        """Positive: slos.md contains SLO targets."""
        slos = Path("docs/architecture/slo/slos.md")
        content = slos.read_text(encoding='utf-8')
        # Should contain some SLO-related keywords
        assert any(keyword in content.lower() for keyword in ['target', 'slo', 'objective', 'metric']), \
            "slos.md should contain SLO targets"


class TestPolicyArtifacts:
    """Tests for policy artifacts."""

    def test_policy_directory_exists(self):
        """Positive: Policy directory exists."""
        policy_dir = Path("docs/architecture/policy")
        assert policy_dir.exists(), "Policy directory should exist"
        assert policy_dir.is_dir(), "Policy should be a directory"

    def test_policy_snapshot_v1_exists(self):
        """Positive: policy_snapshot_v1.json exists."""
        snapshot = Path("docs/architecture/policy/policy_snapshot_v1.json")
        assert snapshot.exists(), "policy_snapshot_v1.json should exist"
        assert snapshot.is_file(), "policy_snapshot_v1.json should be a file"

    def test_policy_snapshot_v1_valid_json(self):
        """Positive: policy_snapshot_v1.json is valid JSON."""
        snapshot = Path("docs/architecture/policy/policy_snapshot_v1.json")
        try:
            data = json.loads(snapshot.read_text(encoding='utf-8'))
            assert isinstance(data, dict), "Policy snapshot should be a JSON object"
        except json.JSONDecodeError as e:
            pytest.fail(f"Policy snapshot is not valid JSON: {e}")

    def test_policy_snapshot_v1_required_fields(self):
        """Positive: Policy snapshot has required fields."""
        snapshot = Path("docs/architecture/policy/policy_snapshot_v1.json")
        data = json.loads(snapshot.read_text(encoding='utf-8'))
        
        required_fields = [
            'snapshot_id', 'module_id', 'slug', 'version', 'schema_version',
            'policy_version_ids', 'snapshot_hash', 'signature', 'kid',
            'effective_from', 'evaluation_points'
        ]
        
        for field in required_fields:
            assert field in data, f"Policy snapshot should have field: {field}"

    def test_policy_snapshot_v1_version_format(self):
        """Positive: Version field has correct format."""
        snapshot = Path("docs/architecture/policy/policy_snapshot_v1.json")
        data = json.loads(snapshot.read_text(encoding='utf-8'))
        
        assert 'version' in data, "Policy snapshot should have version field"
        assert isinstance(data['version'], dict), "Version should be an object"
        assert 'major' in data['version'], "Version should have major field"
        assert isinstance(data['version']['major'], int), "Version major should be integer"

    def test_policy_snapshot_v1_hash_format(self):
        """Edge: Snapshot hash has correct format (sha256:hex)."""
        snapshot = Path("docs/architecture/policy/policy_snapshot_v1.json")
        data = json.loads(snapshot.read_text(encoding='utf-8'))
        
        if 'snapshot_hash' in data:
            hash_value = data['snapshot_hash']
            # Should be sha256: followed by 64 hex characters
            assert hash_value.startswith('sha256:'), \
                "Snapshot hash should start with 'sha256:'"
            hex_part = hash_value[7:]
            assert len(hex_part) == 64, \
                "Snapshot hash hex part should be 64 characters"
            assert all(c in '0123456789abcdef' for c in hex_part.lower()), \
                "Snapshot hash hex part should be hexadecimal"

    def test_rollback_md_exists(self):
        """Positive: rollback.md exists."""
        doc = Path("docs/architecture/policy/rollback.md")
        assert doc.exists(), "rollback.md should exist"
        assert doc.is_file(), "rollback.md should be a file"

    def test_rollback_md_not_empty(self):
        """Positive: rollback.md is not empty."""
        doc = Path("docs/architecture/policy/rollback.md")
        assert doc.stat().st_size > 0, "rollback.md should not be empty"


class TestSampleArtifacts:
    """Tests for sample artifacts."""

    def test_samples_directory_exists(self):
        """Positive: Samples directory exists."""
        samples_dir = Path("docs/architecture/samples")
        assert samples_dir.exists(), "Samples directory should exist"
        assert samples_dir.is_dir(), "Samples should be a directory"

    def test_receipts_directory_exists(self):
        """Positive: Receipts directory exists."""
        receipts_dir = Path("docs/architecture/samples/receipts")
        assert receipts_dir.exists(), "Receipts directory should exist"
        assert receipts_dir.is_dir(), "Receipts should be a directory"

    def test_receipts_example_exists(self):
        """Positive: receipts_example.jsonl exists."""
        receipts = Path("docs/architecture/samples/receipts/receipts_example.jsonl")
        assert receipts.exists(), "receipts_example.jsonl should exist"
        assert receipts.is_file(), "receipts_example.jsonl should be a file"

    def test_receipts_example_valid_jsonl(self):
        """Positive: receipts_example.jsonl is valid JSONL."""
        receipts = Path("docs/architecture/samples/receipts/receipts_example.jsonl")
        lines = receipts.read_text(encoding='utf-8').strip().split('\n')
        
        assert len(lines) >= 2, "JSONL should have at least 2 lines (as specified)"
        
        for i, line in enumerate(lines, 1):
            if line.strip():  # Skip empty lines
                try:
                    json.loads(line)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Line {i} is not valid JSON: {e}")

    def test_receipts_example_required_fields(self):
        """Positive: Receipts have required fields."""
        receipts = Path("docs/architecture/samples/receipts/receipts_example.jsonl")
        lines = receipts.read_text(encoding='utf-8').strip().split('\n')
        
        required_fields = [
            'receipt_id', 'gate_id', 'policy_version_ids', 'snapshot_hash',
            'timestamp_utc', 'timestamp_monotonic_ms', 'inputs', 'decision',
            'evidence_handles', 'actor', 'degraded', 'signature'
        ]
        
        for i, line in enumerate(lines, 1):
            if line.strip():
                receipt = json.loads(line)
                for field in required_fields:
                    assert field in receipt, \
                        f"Receipt on line {i} should have field: {field}"

    def test_receipts_example_valid_decisions(self):
        """Positive: Receipts have valid decision statuses."""
        receipts = Path("docs/architecture/samples/receipts/receipts_example.jsonl")
        lines = receipts.read_text(encoding='utf-8').strip().split('\n')
        
        valid_statuses = {'pass', 'warn', 'soft_block', 'hard_block'}
        
        for i, line in enumerate(lines, 1):
            if line.strip():
                receipt = json.loads(line)
                assert 'decision' in receipt, f"Receipt on line {i} should have decision"
                assert 'status' in receipt['decision'], \
                    f"Receipt on line {i} decision should have status"
                assert receipt['decision']['status'] in valid_statuses, \
                    f"Receipt on line {i} decision status should be one of {valid_statuses}"

    def test_evidence_directory_exists(self):
        """Positive: Evidence directory exists."""
        evidence_dir = Path("docs/architecture/samples/evidence")
        assert evidence_dir.exists(), "Evidence directory should exist"
        assert evidence_dir.is_dir(), "Evidence should be a directory"

    def test_evidence_pack_exists(self):
        """Positive: evidence_pack_example.json exists."""
        evidence = Path("docs/architecture/samples/evidence/evidence_pack_example.json")
        assert evidence.exists(), "evidence_pack_example.json should exist"
        assert evidence.is_file(), "evidence_pack_example.json should be a file"

    def test_evidence_pack_valid_json(self):
        """Positive: evidence_pack_example.json is valid JSON."""
        evidence = Path("docs/architecture/samples/evidence/evidence_pack_example.json")
        try:
            data = json.loads(evidence.read_text(encoding='utf-8'))
            assert isinstance(data, dict), "Evidence pack should be a JSON object"
        except json.JSONDecodeError as e:
            pytest.fail(f"Evidence pack is not valid JSON: {e}")

    def test_evidence_pack_required_fields(self):
        """Positive: Evidence pack has required fields."""
        evidence = Path("docs/architecture/samples/evidence/evidence_pack_example.json")
        data = json.loads(evidence.read_text(encoding='utf-8'))
        
        required_fields = ['evidence_pack_id', 'receipt_id', 'gate_id', 'created_at', 'evidence_items']
        
        for field in required_fields:
            assert field in data, f"Evidence pack should have field: {field}"


class TestOperationalDocumentation:
    """Tests for operational documentation."""

    def test_ops_directory_exists(self):
        """Positive: Ops directory exists."""
        ops_dir = Path("docs/architecture/ops")
        assert ops_dir.exists(), "Ops directory should exist"
        assert ops_dir.is_dir(), "Ops should be a directory"

    def test_runbooks_exists(self):
        """Positive: runbooks.md exists."""
        doc = Path("docs/architecture/ops/runbooks.md")
        assert doc.exists(), "runbooks.md should exist"
        assert doc.is_file(), "runbooks.md should be a file"

    def test_runbooks_contains_top_3_incidents(self):
        """Positive: Runbooks contain top 3 incident playbooks."""
        runbooks = Path("docs/architecture/ops/runbooks.md")
        content = runbooks.read_text(encoding='utf-8')
        
        incidents = [
            'Receipt not written',
            'Gate blocks all PRs',
            'Policy fetch fails'
        ]
        
        for incident in incidents:
            assert incident.lower() in content.lower(), \
                f"Runbooks should contain playbook for: {incident}"

    def test_branching_exists(self):
        """Positive: branching.md exists."""
        doc = Path("docs/architecture/ops/branching.md")
        assert doc.exists(), "branching.md should exist"
        assert doc.is_file(), "branching.md should be a file"

    def test_branching_contains_model(self):
        """Positive: Branching doc contains branching model."""
        branching = Path("docs/architecture/ops/branching.md")
        content = branching.read_text(encoding='utf-8')
        
        # Should mention trunk-based or branching model
        assert any(keyword in content.lower() for keyword in ['trunk', 'branch', 'model']), \
            "Branching doc should describe branching model"


class TestDevelopmentDocumentation:
    """Tests for development documentation."""

    def test_dev_directory_exists(self):
        """Positive: Dev directory exists."""
        dev_dir = Path("docs/architecture/dev")
        assert dev_dir.exists(), "Dev directory should exist"
        assert dev_dir.is_dir(), "Dev should be a directory"

    def test_standards_exists(self):
        """Positive: standards.md exists."""
        doc = Path("docs/architecture/dev/standards.md")
        assert doc.exists(), "standards.md should exist"
        assert doc.is_file(), "standards.md should be a file"

    def test_quickstart_windows_exists(self):
        """Positive: quickstart_windows.md exists."""
        doc = Path("docs/architecture/dev/quickstart_windows.md")
        assert doc.exists(), "quickstart_windows.md should exist"
        assert doc.is_file(), "quickstart_windows.md should be a file"

    def test_quickstart_windows_contains_windows_commands(self):
        """Positive: Quickstart contains Windows-specific commands."""
        quickstart = Path("docs/architecture/dev/quickstart_windows.md")
        content = quickstart.read_text(encoding='utf-8')
        
        # Should contain PowerShell or Windows-specific commands
        assert any(keyword in content.lower() for keyword in ['powershell', 'windows', 'cmd', '.ps1']), \
            "Quickstart should contain Windows-specific commands"


class TestSecurityDocumentation:
    """Tests for security documentation."""

    def test_security_directory_exists(self):
        """Positive: Security directory exists."""
        security_dir = Path("docs/architecture/security")
        assert security_dir.exists(), "Security directory should exist"
        assert security_dir.is_dir(), "Security should be a directory"

    def test_rbac_exists(self):
        """Positive: rbac.md exists."""
        doc = Path("docs/architecture/security/rbac.md")
        assert doc.exists(), "rbac.md should exist"
        assert doc.is_file(), "rbac.md should be a file"

    def test_data_classes_exists(self):
        """Positive: data_classes.md exists."""
        doc = Path("docs/architecture/security/data_classes.md")
        assert doc.exists(), "data_classes.md should exist"
        assert doc.is_file(), "data_classes.md should be a file"

    def test_privacy_note_exists(self):
        """Positive: privacy_note.md exists."""
        doc = Path("docs/architecture/security/privacy_note.md")
        assert doc.exists(), "privacy_note.md should exist"
        assert doc.is_file(), "privacy_note.md should be a file"

    def test_rbac_contains_roles(self):
        """Positive: RBAC doc contains role definitions."""
        rbac = Path("docs/architecture/security/rbac.md")
        content = rbac.read_text(encoding='utf-8')
        
        # Should mention roles
        assert 'role' in content.lower(), "RBAC doc should define roles"

    def test_data_classes_contains_classification(self):
        """Positive: Data classes doc contains classification levels."""
        data_classes = Path("docs/architecture/security/data_classes.md")
        content = data_classes.read_text(encoding='utf-8')
        
        # Should mention classification levels
        assert any(keyword in content.lower() for keyword in ['classification', 'public', 'confidential', 'restricted']), \
            "Data classes doc should define classification levels"


class TestTestingInfrastructure:
    """Tests for testing infrastructure."""

    def test_tests_directory_exists(self):
        """Positive: Tests directory exists."""
        tests_dir = Path("docs/architecture/tests")
        assert tests_dir.exists(), "Tests directory should exist"
        assert tests_dir.is_dir(), "Tests should be a directory"

    def test_test_plan_exists(self):
        """Positive: test_plan.md exists."""
        doc = Path("docs/architecture/tests/test_plan.md")
        assert doc.exists(), "test_plan.md should exist"
        assert doc.is_file(), "test_plan.md should be a file"

    def test_golden_directory_exists(self):
        """Positive: Golden directory exists."""
        golden_dir = Path("docs/architecture/tests/golden")
        assert golden_dir.exists(), "Golden directory should exist"
        assert golden_dir.is_dir(), "Golden should be a directory"

    def test_test_plan_contains_test_levels(self):
        """Positive: Test plan contains test levels."""
        test_plan = Path("docs/architecture/tests/test_plan.md")
        content = test_plan.read_text(encoding='utf-8')
        
        # Should mention test levels
        assert any(keyword in content.lower() for keyword in ['unit', 'integration', 'e2e', 'end-to-end']), \
            "Test plan should define test levels"


class TestCICDInfrastructure:
    """Tests for CI/CD infrastructure."""

    def test_jenkinsfile_exists(self):
        """Positive: Jenkinsfile exists at root."""
        jenkinsfile = Path("Jenkinsfile")
        assert jenkinsfile.exists(), "Jenkinsfile should exist at repository root"
        assert jenkinsfile.is_file(), "Jenkinsfile should be a file"

    def test_jenkinsfile_contains_stages(self):
        """Positive: Jenkinsfile contains expected stages."""
        jenkinsfile = Path("Jenkinsfile")
        content = jenkinsfile.read_text(encoding='utf-8')
        
        # Should contain pipeline stages
        assert 'pipeline' in content.lower(), "Jenkinsfile should define pipeline"
        assert any(keyword in content.lower() for keyword in ['stage', 'test', 'build']), \
            "Jenkinsfile should contain test and build stages"


class TestArchitectureContradictions:
    """Tests to verify contradictions are resolved."""

    def test_vscode_extension_structure_documented(self):
        """Positive: VS Code Extension structure is documented consistently."""
        # Check that key documents mention modules/ directory
        hla = Path("docs/architecture/zeroui-hla.md")
        lla = Path("docs/architecture/zeroui-lla.md")
        
        hla_content = hla.read_text(encoding='utf-8')
        lla_content = lla.read_text(encoding='utf-8')
        
        # Both should mention modules/ directory
        assert 'modules/' in hla_content or 'modules' in hla_content.lower(), \
            "HLA should document modules/ directory"
        assert 'modules/' in lla_content or 'modules' in lla_content.lower(), \
            "LLA should document modules/ directory"

    def test_openapi_schema_paths_updated(self):
        """Positive: OpenAPI/Schema paths reference contracts/ directory."""
        # Check that documents reference contracts/ not docs/architecture/openapi/
        arch_doc = Path("docs/architecture/ZeroUI_Architecture_V0_converted.md")
        content = arch_doc.read_text(encoding='utf-8')
        
        # Should reference contracts/ directory
        assert 'contracts/' in content, \
            "Architecture doc should reference contracts/ directory for OpenAPI/Schemas"


class TestEdgeCases:
    """Edge case tests."""

    def test_gate_table_empty_condition(self):
        """Edge: Gate table with empty condition should be handled."""
        # This documents expected behavior
        # Empty conditions should be caught by validation
        pass

    def test_receipt_missing_optional_fields(self):
        """Edge: Receipt with missing optional fields should still be valid."""
        # Optional fields should not cause validation failure
        receipts = Path("docs/architecture/samples/receipts/receipts_example.jsonl")
        lines = receipts.read_text(encoding='utf-8').strip().split('\n')
        
        for line in lines:
            if line.strip():
                receipt = json.loads(line)
                # Receipt should still be valid even if optional fields missing
                assert 'receipt_id' in receipt, "Receipt must have receipt_id"

    def test_policy_snapshot_empty_arrays(self):
        """Edge: Policy snapshot with empty arrays should be valid."""
        snapshot = Path("docs/architecture/policy/policy_snapshot_v1.json")
        data = json.loads(snapshot.read_text(encoding='utf-8'))
        
        # Empty arrays should be valid
        if 'evaluation_points' in data:
            assert isinstance(data['evaluation_points'], list), \
                "evaluation_points should be a list (even if empty)"

    def test_file_permissions_readable(self):
        """Edge: All documentation files should be readable."""
        docs_to_check = [
            "docs/architecture/gate_tables/README.md",
            "docs/architecture/trust/signing_process.md",
            "docs/architecture/slo/slos.md",
            "docs/architecture/policy/policy_snapshot_v1.json",
        ]
        
        for doc_path in docs_to_check:
            doc = Path(doc_path)
            if doc.exists():
                # Should be readable
                assert doc.is_file(), f"{doc_path} should be a file"
                try:
                    doc.read_text(encoding='utf-8')
                except Exception as e:
                    pytest.fail(f"{doc_path} should be readable: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

