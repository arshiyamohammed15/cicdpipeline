"""
End-to-End Validation Tests

Tests complete validation workflow and integration.
"""

import unittest
import ast
from pathlib import Path
from validator.models import Violation, Severity


class TestEndToEndValidation(unittest.TestCase):
    """Test suite for end-to-end validation workflows."""
    
    def test_storage_governance_end_to_end(self):
        """Test complete storage governance validation workflow."""
        from validator.rules.storage_governance import StorageGovernanceValidator
        
        validator = StorageGovernanceValidator()
        
        # Test with code containing multiple violations
        content = '''
# Multiple storage violations
path = "storage/MyFolder/userData"  # R216: kebab-case violation
password = "secret123"  # R218: hardcoded secret
storage_path = "D:\\\\ZeroUI\\\\tenant"  # R223: hardcoded path
'''
        
        violations = validator.validate("test.py", content)
        
        self.assertIsInstance(violations, list)
        self.assertGreater(len(violations), 0, "Should detect violations")
        
        # Check that violations have proper structure
        for violation in violations:
            self.assertIsInstance(violation, Violation)
            self.assertIsNotNone(violation.rule_id)
            self.assertIsNotNone(violation.severity)
            self.assertIsNotNone(violation.message)
    
    def test_privacy_validation_end_to_end(self):
        """Test complete privacy validation workflow."""
        from validator.rules.privacy import PrivacyValidator
        
        validator = PrivacyValidator()
        
        content = '''
password = "SecretPass123"
api_key = "sk-1234567890"
user_input = input("Enter data: ")
process(user_input)
'''
        
        violations = validator.validate_all(None, content, "test.py")
        
        self.assertIsInstance(violations, list)
        self.assertGreater(len(violations), 0)
        
        # Verify violation types
        rule_numbers = [v.rule_number for v in violations if v.rule_number]
        self.assertIn(3, rule_numbers)  # Privacy rule
    
    def test_architecture_validation_end_to_end(self):
        """Test complete architecture validation workflow."""
        from validator.rules.architecture import ArchitectureValidator
        
        validator = ArchitectureValidator()
        
        content = '''
def ui_function():
    user = database.query("SELECT * FROM users")
    return render(user)
'''
        
        tree = ast.parse(content)
        violations = validator.validate_all(tree, content, "ui/view.py")
        
        self.assertIsInstance(violations, list)
        # Architecture violations depend on file path and content patterns
    
    def test_exception_handling_validation_end_to_end(self):
        """Test complete exception handling validation workflow."""
        from validator.rules.exception_handling import ExceptionHandlingValidator
        
        validator = ExceptionHandlingValidator()
        
        content = '''
try:
    risky_operation()
except Exception:
    pass  # Silent catch

import requests
response = requests.get(url)  # No timeout
'''
        
        violations = validator.validate("test.py", content)
        
        self.assertIsInstance(violations, list)
        self.assertGreater(len(violations), 0)
    
    def test_api_contracts_validation_end_to_end(self):
        """Test complete API contracts validation workflow."""
        from validator.rules.api_contracts import APIContractsValidator
        
        validator = APIContractsValidator()
        
        content = '''
@app.route('/api/users', methods=['POST'])
def create_user():
    return {"id": 123}
'''
        
        violations = validator.validate("test.py", content)
        
        self.assertIsInstance(violations, list)
        # Should detect versioning violations
    
    def test_multiple_validators_integration(self):
        """Test integration of multiple validators."""
        from validator.rules.privacy import PrivacyValidator
        from validator.rules.architecture import ArchitectureValidator
        
        content = '''
password = "hardcoded"
def ui_function():
    db.query("SELECT * FROM users")
'''
        
        privacy_validator = PrivacyValidator()
        arch_validator = ArchitectureValidator()
        
        privacy_violations = privacy_validator.validate_all(None, content, "test.py")
        tree = ast.parse(content)
        arch_violations = arch_validator.validate_all(tree, content, "ui/test.py")
        
        total_violations = privacy_violations + arch_violations
        self.assertIsInstance(total_violations, list)
    
    def test_violation_severity_levels(self):
        """Test that violations have proper severity levels."""
        from validator.rules.storage_governance import StorageGovernanceValidator
        
        validator = StorageGovernanceValidator()
        
        content = '''
password = "secret"  # ERROR
path = "MyFolder"  # ERROR
'''
        
        violations = validator.validate("test.py", content)
        
        severities = [v.severity for v in violations]
        self.assertTrue(all(isinstance(s, Severity) for s in severities))
    
    def test_performance_with_large_file(self):
        """Test validation performance with larger code samples."""
        from validator.rules.privacy import PrivacyValidator
        
        validator = PrivacyValidator()
        
        # Create larger content
        lines = []
        for i in range(100):
            lines.append(f"def function_{i}():")
            lines.append(f"    return {i}")
        
        content = '\n'.join(lines)
        
        import time
        start = time.time()
        violations = validator.validate_all(None, content, "test.py")
        duration = time.time() - start
        
        # Should complete within reasonable time
        self.assertLess(duration, 5.0, "Validation should complete within 5 seconds")
        self.assertIsInstance(violations, list)


if __name__ == '__main__':
    unittest.main()

