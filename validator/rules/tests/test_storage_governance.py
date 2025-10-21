"""
Tests for Storage Governance Validator (Rules 216-228)

Tests the 4-plane storage architecture compliance validation.
"""

import unittest
from validator.rules.storage_governance import StorageGovernanceValidator
from validator.models import Severity


class TestStorageGovernanceValidator(unittest.TestCase):
    """Test suite for storage governance rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = StorageGovernanceValidator()
    
    # Rule 216: Kebab-Case Naming
    def test_rule_216_kebab_case_valid(self):
        """Test Rule 216: Valid kebab-case names."""
        content = '''
path = "storage/my-folder/user-data"
folder = "agent-receipts"
'''
        violations = self.validator._validate_name_casing(content, "test.py")
        kebab_violations = [v for v in violations if 'uppercase' in v.message.lower() or 'underscore' in v.message.lower()]
        self.assertEqual(len(kebab_violations), 0)
    
    def test_rule_216_kebab_case_violation_uppercase(self):
        """Test Rule 216: Uppercase in folder names."""
        content = '''
path = "storage/MyFolder/userData"
'''
        violations = self.validator._validate_name_casing(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R216')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    def test_rule_216_kebab_case_violation_underscore(self):
        """Test Rule 216: Underscores in folder names."""
        content = '''
path = "storage/my_folder/user_data"
'''
        violations = self.validator._validate_name_casing(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R216')
    
    # Rule 217: No Code/PII in Stores
    def test_rule_217_no_code_in_storage(self):
        """Test Rule 217: No source code in storage."""
        content = '''
storage_path = "evidence/receipts/"
data = "def my_function():"
file.write(data)
'''
        violations = self.validator._validate_no_code_pii(content, "test.py")
        code_violations = [v for v in violations if v.rule_id == 'R217' and 'code' in v.message.lower()]
        self.assertGreater(len(code_violations), 0)
    
    def test_rule_217_no_pii_in_storage(self):
        """Test Rule 217: No PII in storage."""
        content = '''
storage_path = "evidence/receipts/"
email = "user@example.com"
ssn = "123-45-6789"
'''
        violations = self.validator._validate_no_code_pii(content, "test.py")
        pii_violations = [v for v in violations if v.rule_id == 'R217' and 'pii' in v.message.lower()]
        self.assertGreater(len(pii_violations), 0)
    
    # Rule 218: No Secrets on Disk
    def test_rule_218_no_secrets_valid(self):
        """Test Rule 218: Valid - using environment variables."""
        content = '''
api_key = os.environ.get("API_KEY")
password = os.getenv("DB_PASSWORD")
'''
        violations = self.validator._validate_no_secrets(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_218_no_secrets_violation_password(self):
        """Test Rule 218: Hardcoded password."""
        content = '''
password = "SecretPass123"
'''
        violations = self.validator._validate_no_secrets(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R218')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    def test_rule_218_no_secrets_violation_api_key(self):
        """Test Rule 218: Hardcoded API key."""
        content = '''
api_key = "sk-1234567890abcdef"
'''
        violations = self.validator._validate_no_secrets(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R218')
    
    # Rule 219: JSONL Receipts
    def test_rule_219_jsonl_format_valid(self):
        """Test Rule 219: Valid JSONL format."""
        content = '''
receipt = json.dumps(data) + "\\n"
file.write(receipt)
'''
        violations = self.validator._validate_jsonl_receipts(content, "test.py")
        format_violations = [v for v in violations if 'format' in v.message.lower()]
        self.assertEqual(len(format_violations), 0)
    
    def test_rule_219_append_only_violation(self):
        """Test Rule 219: Receipt overwrite violation."""
        content = '''
receipt_file = open("receipt.jsonl", "w")
receipt_data = {"id": 123}
'''
        violations = self.validator._validate_jsonl_receipts(content, "test.py")
        append_violations = [v for v in violations if 'append' in v.message.lower()]
        self.assertGreater(len(append_violations), 0)
    
    # Rule 220: Time Partitions
    def test_rule_220_time_partition_valid(self):
        """Test Rule 220: Valid UTC time partition."""
        content = '''
path = "observability/metrics/dt=2025-10-20/"
'''
        violations = self.validator._validate_time_partitions(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_220_time_partition_invalid_format(self):
        """Test Rule 220: Invalid partition format."""
        content = '''
path = "observability/metrics/dt=20251020/"
'''
        violations = self.validator._validate_time_partitions(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R220')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    def test_rule_220_date_instead_of_dt(self):
        """Test Rule 220: Using 'date=' instead of 'dt='."""
        content = '''
path = "observability/metrics/date=2025-10-20/"
'''
        violations = self.validator._validate_time_partitions(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R220')
    
    # Rule 221: Policy Signatures
    def test_rule_221_policy_signature_valid(self):
        """Test Rule 221: Valid signed policy."""
        content = '''
policy_data = load_policy()
signature = sign(policy_data)
save_policy_with_signature(policy_data, signature)
'''
        violations = self.validator._validate_policy_signatures(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_221_policy_signature_missing(self):
        """Test Rule 221: Unsigned policy snapshot."""
        content = '''
policy_snapshot = get_policy()
save_policy(policy_snapshot)
'''
        violations = self.validator._validate_policy_signatures(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R221')
    
    # Rule 222: Dual Storage
    def test_rule_222_dual_storage_warning(self):
        """Test Rule 222: DB without JSONL warning."""
        content = '''
receipt = {"id": 123, "action": "commit"}
cursor.execute("INSERT INTO evidence (data) VALUES (?)", (receipt,))
'''
        violations = self.validator._validate_dual_storage(content, "test.py")
        dual_violations = [v for v in violations if v.rule_id == 'R222']
        self.assertGreater(len(dual_violations), 0)
    
    # Rule 223: Path Resolution
    def test_rule_223_path_resolution_valid(self):
        """Test Rule 223: Valid path resolution via ZU_ROOT."""
        content = '''
zu_root = os.environ.get("ZU_ROOT")
storage_path = os.path.join(zu_root, "tenant", "evidence")
'''
        violations = self.validator._validate_path_resolution(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_223_path_resolution_hardcoded(self):
        """Test Rule 223: Hardcoded storage path."""
        content = '''
storage_path = "D:\\\\ZeroUI\\\\tenant\\\\evidence"
'''
        violations = self.validator._validate_path_resolution(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R223')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    # Rule 224: Receipts Validation
    def test_rule_224_receipt_verification(self):
        """Test Rule 224: Receipt without signature verification."""
        content = '''
receipts_file = open("receipts/data.jsonl", "r")
receipt = receipts_file.readline()
process(receipt)
'''
        violations = self.validator._validate_receipts_validation(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R224')
    
    # Rule 225: Evidence Watermarks
    def test_rule_225_watermark_structure_valid(self):
        """Test Rule 225: Valid per-consumer watermark."""
        content = '''
watermark_path = "evidence/watermarks/metrics/"
'''
        violations = self.validator._validate_evidence_watermarks(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_225_watermark_structure_missing_consumer(self):
        """Test Rule 225: Watermark without consumer-id."""
        content = '''
watermark_path = "evidence/watermarks/"
save_watermark(watermark_path)
'''
        violations = self.validator._validate_evidence_watermarks(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R225')
    
    # Rule 226: RFC Fallback
    def test_rule_226_rfc_fallback_pattern(self):
        """Test Rule 226: RFC fallback pattern warning."""
        content = '''
unclassified_data = load_data()
save_to_unclassified(unclassified_data)
'''
        violations = self.validator._validate_rfc_fallback(content, "test.py")
        # Should warn about 24h resolution
        info_violations = [v for v in violations if v.severity == Severity.INFO]
        self.assertGreater(len(info_violations), 0)
    
    # Rule 227: Observability Partitions
    def test_rule_227_observability_partition_valid(self):
        """Test Rule 227: Valid observability partition."""
        content = '''
metrics_path = "observability/metrics/dt=2025-10-20/"
'''
        violations = self.validator._validate_observability_partitions(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_227_observability_partition_missing(self):
        """Test Rule 227: Observability path without partition."""
        content = '''
metrics_path = "observability/metrics/"
save_metrics(metrics_path)
'''
        violations = self.validator._validate_observability_partitions(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R227')
    
    # Rule 228: Laptop Receipts Partitioning
    def test_rule_228_laptop_receipts_valid(self):
        """Test Rule 228: Valid laptop receipts partitioning."""
        content = '''
receipt_path = "ide/agent/receipts/repo-id/2025/10/"
'''
        violations = self.validator._validate_laptop_receipts_partitioning(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_228_laptop_receipts_missing_partition(self):
        """Test Rule 228: Laptop receipts without month partition."""
        content = '''
receipt_path = "ide/agent/receipts/repo-id/"
save_receipt(receipt_path)
'''
        violations = self.validator._validate_laptop_receipts_partitioning(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R228')
    
    # Integration test
    def test_validate_all_rules(self):
        """Test validate() method runs all rule checks."""
        content = '''
# Test file with various storage operations
path = "MyFolder/userData"  # Rule 216 violation
password = "secret123"  # Rule 218 violation
storage = "D:\\\\ZeroUI\\\\tenant"  # Rule 223 violation
'''
        violations = self.validator.validate("test.py", content)
        
        # Should have violations from multiple rules
        rule_ids = set(v.rule_id for v in violations)
        self.assertGreater(len(rule_ids), 1)
        self.assertIn('R216', rule_ids)
        self.assertIn('R218', rule_ids)
        self.assertIn('R223', rule_ids)


if __name__ == '__main__':
    unittest.main()

