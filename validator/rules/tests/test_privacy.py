"""
Tests for Privacy & Security Validator (Rules 3, 11, 12, 27, 36)

Tests privacy and security compliance validation.
"""

import unittest
from validator.rules.privacy import PrivacyValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestPrivacyValidator(unittest.TestCase):
    """Test suite for privacy and security rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = PrivacyValidator()
        self.test_file_path = "test.py"
    
    # Rule 3: Protect people's privacy
    def test_rule_003_hardcoded_password_violation(self):
        """Test Rule 3: Hardcoded password detection."""
        content = '''
password = "SecretPass123"
db_password = "admin123"
'''
        tree = self.validator._compile_patterns()
        violations = self.validator.validate_protect_privacy(None, content, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
        password_violations = [v for v in violations if v.rule_number == 3]
        self.assertGreater(len(password_violations), 0)
        self.assertEqual(password_violations[0].severity, Severity.ERROR)
        # Message wording may vary by heuristic; assert rule number & severity only
    
    def test_rule_003_hardcoded_api_key_violation(self):
        """Test Rule 3: Hardcoded API key detection."""
        content = '''
api_key = "sk-1234567890abcdef"
secret_key = "my-secret-key-123"
'''
        violations = self.validator.validate_protect_privacy(None, content, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
        api_violations = [v for v in violations if 'api' in v.message.lower() or 'secret' in v.message.lower()]
        self.assertGreater(len(api_violations), 0)
        self.assertEqual(api_violations[0].severity, Severity.ERROR)
    
    def test_rule_003_environment_variables_valid(self):
        """Test Rule 3: Valid - using environment variables."""
        content = '''
import os
password = os.environ.get("DB_PASSWORD")
api_key = os.getenv("API_KEY")
'''
        violations = self.validator.validate_protect_privacy(None, content, self.test_file_path)
        
        # Should have no violations for environment variables
        password_violations = [v for v in violations if v.rule_number == 3]
        self.assertEqual(len(password_violations), 0)
    
    def test_rule_003_pii_email_violation(self):
        """Test Rule 3: PII email detection."""
        content = '''
user_email = "john.doe@example.com"
contact_email = "admin@company.com"
'''
        violations = self.validator.validate_protect_privacy(None, content, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
        email_violations = [v for v in violations if 'email' in v.code_snippet.lower()]
        self.assertGreater(len(email_violations), 0)
    
    def test_rule_003_pii_ssn_violation(self):
        """Test Rule 3: PII SSN detection."""
        content = '''
ssn = "123-45-6789"
social_security = "987-65-4321"
'''
        violations = self.validator.validate_protect_privacy(None, content, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
        ssn_violations = [v for v in violations if 'ssn' in v.code_snippet.lower() or 'social' in v.code_snippet.lower()]
        self.assertGreater(len(ssn_violations), 0)
    
    def test_rule_003_pii_credit_card_violation(self):
        """Test Rule 3: PII credit card detection."""
        content = '''
credit_card = "4532-1234-5678-9010"
card_number = "5678-9012-3456-7890"
'''
        violations = self.validator.validate_protect_privacy(None, content, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
        cc_violations = [v for v in violations if 'credit' in v.code_snippet.lower()]
        self.assertGreater(len(cc_violations), 0)
    
    # Rule 11: Check your data
    def test_rule_011_input_without_validation_violation(self):
        """Test Rule 11: Input without validation."""
        content = '''
user_input = input("Enter your name: ")
process_data(user_input)
'''
        violations = self.validator.validate_check_data(None, content, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
        input_violations = [v for v in violations if v.rule_number == 11]
        self.assertGreater(len(input_violations), 0)
        self.assertEqual(input_violations[0].severity, Severity.WARNING)
    
    def test_rule_011_input_with_validation_valid(self):
        """Test Rule 11: Valid - input with validation."""
        content = '''
user_input = input("Enter your name: ")
validated_input = validate(user_input)
sanitized_input = sanitize(validated_input)
process_data(sanitized_input)
'''
        violations = self.validator.validate_check_data(None, content, self.test_file_path)
        
        # Should have no violations when validation is present
        self.assertEqual(len(violations), 0)
    
    def test_rule_011_sys_stdin_without_validation_violation(self):
        """Test Rule 11: sys.stdin without validation."""
        content = '''
import sys
data = sys.stdin.read()
process(data)
'''
        violations = self.validator.validate_check_data(None, content, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
    
    # Rule 12: Keep AI safe
    def test_rule_012_ai_without_safety_violation(self):
        """Test Rule 12: AI code without safety measures."""
        content = '''
import ai

model = ai.load_model("gpt-4")
result = model.generate(user_prompt)
'''
        violations = self.validator.validate_keep_ai_safe(None, content, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
        ai_violations = [v for v in violations if v.rule_number == 12]
        self.assertGreater(len(ai_violations), 0)
        self.assertEqual(ai_violations[0].severity, Severity.WARNING)
    
    def test_rule_012_ai_with_safety_valid(self):
        """Test Rule 12: Valid - AI with safety measures."""
        content = '''
import ai

model = ai.load_model("gpt-4")
safety_filter = ai.SafetyGuard()
constrained_result = model.generate(user_prompt, safety=safety_filter, constraints=True)
'''
        violations = self.validator.validate_keep_ai_safe(None, content, self.test_file_path)
        
        # Should have no violations when safety measures are present
        self.assertEqual(len(violations), 0)
    
    def test_rule_012_ml_without_bounds_violation(self):
        """Test Rule 12: ML without bounds."""
        content = '''
import machine_learning as ml

model = ml.train(data)
prediction = model.predict(input_data)
'''
        violations = self.validator.validate_keep_ai_safe(None, content, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
    
    # Rule 27: Be smart about data
    def test_rule_027_data_without_optimization_violation(self):
        """Test Rule 27: Data operations without optimization."""
        content = '''
import database

data = database.query("SELECT * FROM large_table")
for row in data:
    process(row)
'''
        violations = self.validator.validate_smart_data_handling(None, content, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
        data_violations = [v for v in violations if v.rule_number == 27]
        self.assertGreater(len(data_violations), 0)
        self.assertIn(data_violations[0].severity, (Severity.INFO, Severity.WARNING))
    
    def test_rule_027_data_with_optimization_valid(self):
        """Test Rule 27: Valid - data with optimization."""
        content = '''
import database

data = database.query("SELECT * FROM large_table WHERE indexed_field = ?", use_index=True)
cached_data = cache.get_or_set("data_key", lambda: data)
for batch in efficient_batch_processor(cached_data):
    process(batch)
'''
        violations = self.validator.validate_smart_data_handling(None, content, self.test_file_path)
        
        # Should have no violations when optimization is present
        self.assertEqual(len(violations), 0)
    
    def test_rule_027_sql_with_cache_valid(self):
        """Test Rule 27: Valid - SQL with cache."""
        content = '''
sql = "SELECT * FROM users"
results = cache.get_or_query(sql, optimize=True)
'''
        violations = self.validator.validate_smart_data_handling(None, content, self.test_file_path)
        
        self.assertEqual(len(violations), 0)
    
    # Rule 36: Be extra careful with private data
    def test_rule_036_private_without_encryption_violation(self):
        """Test Rule 36: Private data without encryption."""
        content = '''
private_data = load_sensitive_data()
save_to_disk(private_data)
'''
        violations = self.validator.validate_extra_careful_private_data(None, content, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
        private_violations = [v for v in violations if v.rule_number == 36]
        self.assertGreater(len(private_violations), 0)
        self.assertEqual(private_violations[0].severity, Severity.WARNING)
    
    def test_rule_036_private_with_encryption_valid(self):
        """Test Rule 36: Valid - private data with encryption."""
        content = '''
private_data = load_sensitive_data()
encrypted_data = encrypt(private_data, key)
save_to_disk(encrypted_data)
'''
        violations = self.validator.validate_extra_careful_private_data(None, content, self.test_file_path)
        
        # Should have no violations when encryption is present
        self.assertEqual(len(violations), 0)
    
    def test_rule_036_confidential_with_secure_valid(self):
        """Test Rule 36: Valid - confidential data with secure handling."""
        content = '''
confidential_data = load_data()
hashed_data = hash_sensitive_fields(confidential_data)
secure_store(hashed_data, cipher='AES-256')
'''
        violations = self.validator.validate_extra_careful_private_data(None, content, self.test_file_path)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_036_sensitive_without_crypto_violation(self):
        """Test Rule 36: Sensitive data without crypto."""
        content = '''
sensitive_info = {"ssn": "123-45-6789", "password": "secret"}
database.save(sensitive_info)
'''
        violations = self.validator.validate_extra_careful_private_data(None, content, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
    
    # Integration test
    def test_validate_all_rules(self):
        """Test validate_all() method runs all privacy rule checks."""
        content = '''
# Multiple violations
password = "hardcoded123"  # Rule 3
user_input = input("Enter data: ")  # Rule 11
process(user_input)  # No validation
import ai  # Rule 12
model = ai.load_model()  # No safety
private_data = load_private()  # Rule 36
save(private_data)  # No encryption
'''
        violations = self.validator.validate_all(None, content, self.test_file_path)
        
        # Should have violations from multiple rules
        rule_numbers = set(v.rule_number for v in violations if v.rule_number)
        self.assertGreater(len(rule_numbers), 1)
        self.assertIn(3, rule_numbers)  # Hardcoded credentials


if __name__ == '__main__':
    unittest.main()

