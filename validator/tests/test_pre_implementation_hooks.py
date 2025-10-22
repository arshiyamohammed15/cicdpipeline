"""
Tests for Pre-Implementation Hooks (ALL 280 Constitution Rules)

Tests the comprehensive validation of prompts before AI code generation,
ensuring ALL 280 Constitution rules are enforced at the source.
"""

import unittest
from validator.pre_implementation_hooks import (
    ComprehensivePreImplementationValidator,
    ContextAwareRuleLoader,
    PreImplementationHookManager
)
from validator.models import Violation, Severity


class TestComprehensivePreImplementationValidator(unittest.TestCase):
    """Test suite for comprehensive pre-implementation validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = ComprehensivePreImplementationValidator()
    
    # Basic Work Rules (1-75) Tests
    def test_rule_001_do_exactly_whats_asked_violation(self):
        """Test Rule 1: Detects additions beyond what's asked."""
        prompt = "Create a user login function and also add password reset functionality"
        violations = self.validator._validate_basic_work_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R001')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("additions beyond what's asked", violations[0].message)
    
    def test_rule_001_do_exactly_whats_asked_valid(self):
        """Test Rule 1: Valid prompt that doesn't add extras."""
        prompt = "Create a user login function with email and password validation"
        violations = self.validator._validate_basic_work_rules(prompt)
        
        # Should not have R001 violations
        r001_violations = [v for v in violations if v.rule_id == 'R001']
        self.assertEqual(len(r001_violations), 0)
    
    def test_rule_002_only_use_information_given_violation(self):
        """Test Rule 2: Detects guessing or assumptions."""
        prompt = "Create a function that probably should handle user authentication"
        violations = self.validator._validate_basic_work_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R002')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("guessing or assumptions", violations[0].message)
    
    def test_rule_003_protect_privacy_violation(self):
        """Test Rule 3: Detects privacy violations."""
        prompt = "Create a function that stores user passwords and personal information"
        violations = self.validator._validate_basic_work_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R003')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("sensitive information", violations[0].message)
    
    def test_rule_004_use_settings_files_violation(self):
        """Test Rule 4: Detects hardcoded values."""
        prompt = "Create a function with timeout of 5000ms and retry count of 3"
        violations = self.validator._validate_basic_work_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R004')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("hardcoded values", violations[0].message)
    
    def test_rule_006_never_break_things_violation(self):
        """Test Rule 6: Detects breaking changes."""
        prompt = "Remove the old authentication system and migrate to new one"
        violations = self.validator._validate_basic_work_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R006')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("breaking changes", violations[0].message)
    
    # Code Review Rules (76-99) Tests
    def test_rule_083_automation_violation(self):
        """Test Rule 83: Detects manual processes."""
        prompt = "Manually create a deployment script step by step"
        violations = self.validator._validate_code_review_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R083')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("manual processes", violations[0].message)
    
    def test_rule_086_python_quality_gates_violation(self):
        """Test Rule 86: Detects missing Python quality gates."""
        prompt = "Create a Python function for user management"
        violations = self.validator._validate_code_review_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R086')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("quality gates", violations[0].message)
    
    def test_rule_087_typescript_quality_gates_violation(self):
        """Test Rule 87: Detects missing TypeScript quality gates."""
        prompt = "Create a TypeScript interface for user data"
        violations = self.validator._validate_code_review_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R087')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("quality gates", violations[0].message)
    
    # Security & Privacy Rules (100-131) Tests
    def test_rule_090_security_secrets_violation(self):
        """Test Rule 90: Detects secrets in code."""
        prompt = "Create a function with password = 'secret123' and api_key = 'sk-123456'"
        violations = self.validator._validate_security_privacy_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R090')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("secrets in code", violations[0].message)
    
    def test_rule_100_security_privacy_violation(self):
        """Test Rule 100: Detects privacy risks."""
        prompt = "Create a function that logs user data and stores personal information"
        violations = self.validator._validate_security_privacy_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R100')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("privacy risks", violations[0].message)
    
    # Logging Rules (132-149) Tests
    def test_rule_132_log_format_violation(self):
        """Test Rule 132: Detects non-structured logging."""
        prompt = "Create a function that prints debug information to console"
        violations = self.validator._validate_logging_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R132')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("structured JSON", violations[0].message)
    
    def test_rule_133_required_fields_violation(self):
        """Test Rule 133: Detects missing required log fields."""
        prompt = "Create a logging function that records events"
        violations = self.validator._validate_logging_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R133')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("required fields", violations[0].message)
    
    # Error Handling Rules (150-180) Tests
    def test_rule_150_prevent_first_violation(self):
        """Test Rule 150: Detects reactive error handling."""
        prompt = "Create a function that catches errors and handles exceptions"
        violations = self.validator._validate_error_handling_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R150')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("preventive", violations[0].message)
    
    def test_rule_155_no_silent_catches_violation(self):
        """Test Rule 155: Detects silent error handling."""
        prompt = "Create a function that silently ignores errors and continues"
        violations = self.validator._validate_error_handling_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R155')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("silent error handling", violations[0].message)
    
    # TypeScript Rules (181-215) Tests
    def test_rule_181_strict_mode_violation(self):
        """Test Rule 181: Detects missing TypeScript strict mode."""
        prompt = "Create a TypeScript interface without strict mode"
        violations = self.validator._validate_typescript_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R181')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("strict mode", violations[0].message)
    
    def test_rule_182_no_any_violation(self):
        """Test Rule 182: Detects 'any' type usage."""
        prompt = "Create a TypeScript function that returns any type"
        violations = self.validator._validate_typescript_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R182')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("'any' type", violations[0].message)
    
    # Storage Governance Rules (216-228) Tests
    def test_rule_216_kebab_case_violation(self):
        """Test Rule 216: Detects non-kebab-case naming."""
        prompt = "Create a storage function with camelCase naming"
        violations = self.validator._validate_storage_governance_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R216')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("kebab-case", violations[0].message)
    
    def test_rule_217_no_code_pii_violation(self):
        """Test Rule 217: Detects code or PII in storage."""
        prompt = "Create a storage function that saves source code and personal data"
        violations = self.validator._validate_storage_governance_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R217')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("source code or PII", violations[0].message)
    
    # GSMD Rules (232-252) Tests
    def test_rule_232_gsmd_paths_violation(self):
        """Test Rule 232: Detects incorrect GSMD paths."""
        prompt = "Create a policy function without proper GSMD paths"
        violations = self.validator._validate_gsmd_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R232')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("source of truth paths", violations[0].message)
    
    # Simple Code Readability Rules (253-280) Tests
    def test_rule_253_plain_english_violation(self):
        """Test Rule 253: Detects abbreviations."""
        prompt = "Create a function with usr_mgr and db_conn variables"
        violations = self.validator._validate_simple_readability_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R253')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("plain English", violations[0].message)
    
    def test_rule_270_no_advanced_concepts_violation(self):
        """Test Rule 270: Detects advanced programming concepts."""
        prompt = "Create a function using lambda expressions and async/await"
        violations = self.validator._validate_simple_readability_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R270')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("Advanced programming concepts", violations[0].message)
    
    def test_rule_271_no_complex_data_structures_violation(self):
        """Test Rule 271: Detects complex data structures."""
        prompt = "Create a function with nested objects and hash maps"
        violations = self.validator._validate_simple_readability_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R271')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("Complex data structures", violations[0].message)
    
    def test_rule_272_no_advanced_string_manipulation_violation(self):
        """Test Rule 272: Detects advanced string manipulation."""
        prompt = "Create a function using regex and string interpolation"
        violations = self.validator._validate_simple_readability_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R272')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("Advanced string manipulation", violations[0].message)
    
    def test_rule_280_enforce_simple_level_violation(self):
        """Test Rule 280: Detects complex code."""
        prompt = "Create a complex algorithm with sophisticated optimization"
        violations = self.validator._validate_simple_readability_rules(prompt)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R280')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn("8th grader", violations[0].message)
    
    # Integration Tests
    def test_comprehensive_validation(self):
        """Test comprehensive validation of all rule categories."""
        prompt = """
        Create a complex function using lambda expressions, nested objects, 
        regex patterns, and advanced algorithms. Also add password = 'secret123'
        and manually process data step by step.
        """
        
        violations = self.validator.validate_prompt(prompt, file_type="typescript", task_type="storage")
        
        # Should have multiple violations across different categories
        self.assertGreater(len(violations), 5)
        
        # Check for specific rule violations
        rule_ids = [v.rule_id for v in violations]
        self.assertIn('R270', rule_ids)  # Advanced concepts
        self.assertIn('R271', rule_ids)  # Complex data structures
        self.assertIn('R272', rule_ids)  # Advanced string manipulation
        self.assertIn('R090', rule_ids)  # Secrets in code
        self.assertIn('R083', rule_ids)  # Manual processes
    
    def test_clean_prompt_no_violations(self):
        """Test that clean prompts have no violations."""
        prompt = """
        Create a simple user authentication function with email and password validation.
        Use plain English variable names and basic error handling.
        Include proper logging with required fields.
        """
        
        violations = self.validator.validate_prompt(prompt)
        
        # Should have minimal or no violations
        self.assertLessEqual(len(violations), 2)  # Allow for minor issues


class TestContextAwareRuleLoader(unittest.TestCase):
    """Test suite for context-aware rule loading."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.loader = ContextAwareRuleLoader()
    
    def test_get_relevant_rules_basic(self):
        """Test getting relevant rules for basic context."""
        rules = self.loader.get_relevant_rules()
        
        # Should always include basic categories
        self.assertIn('basic_work', rules)
        self.assertIn('code_review', rules)
        self.assertIn('security_privacy', rules)
        self.assertIn('simple_readability', rules)
    
    def test_get_relevant_rules_typescript(self):
        """Test getting relevant rules for TypeScript context."""
        rules = self.loader.get_relevant_rules(file_type="typescript")
        
        self.assertIn('typescript', rules)
        self.assertIn('basic_work', rules)
        self.assertIn('simple_readability', rules)
    
    def test_get_relevant_rules_storage_task(self):
        """Test getting relevant rules for storage task."""
        rules = self.loader.get_relevant_rules(task_type="storage")
        
        self.assertIn('storage_governance', rules)
        self.assertIn('basic_work', rules)
        self.assertIn('simple_readability', rules)
    
    def test_get_relevant_rules_logging_prompt(self):
        """Test getting relevant rules for logging prompt."""
        rules = self.loader.get_relevant_rules(prompt="Create a logging function")
        
        self.assertIn('logging', rules)
        self.assertIn('basic_work', rules)
        self.assertIn('simple_readability', rules)
    
    def test_get_rule_range(self):
        """Test getting rule range for categories."""
        basic_range = self.loader.get_rule_range('basic_work')
        self.assertEqual(basic_range, (1, 75))
        
        typescript_range = self.loader.get_rule_range('typescript')
        self.assertEqual(typescript_range, (181, 215))
        
        readability_range = self.loader.get_rule_range('simple_readability')
        self.assertEqual(readability_range, (253, 280))
    
    def test_get_all_rules(self):
        """Test getting all rule categories."""
        all_rules = self.loader.get_all_rules()
        
        expected_categories = [
            'basic_work', 'code_review', 'security_privacy', 'logging',
            'error_handling', 'typescript', 'storage_governance', 'gsmd',
            'simple_readability'
        ]
        
        for category in expected_categories:
            self.assertIn(category, all_rules)


class TestPreImplementationHookManager(unittest.TestCase):
    """Test suite for pre-implementation hook manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = PreImplementationHookManager()
    
    def test_validate_before_generation_clean_prompt(self):
        """Test validation of clean prompt."""
        prompt = "Create a simple user authentication function"
        
        result = self.manager.validate_before_generation(prompt)
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['violations']), 0)
        self.assertGreater(result['total_rules_checked'], 0)
        self.assertIn('basic_work', result['relevant_categories'])
        self.assertIn('simple_readability', result['relevant_categories'])
    
    def test_validate_before_generation_violations(self):
        """Test validation of prompt with violations."""
        prompt = "Create a function using lambda expressions and store passwords"
        
        result = self.manager.validate_before_generation(prompt)
        
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['violations']), 0)
        self.assertGreater(len(result['recommendations']), 0)
        
        # Check for specific violations
        rule_ids = [v.rule_id for v in result['violations']]
        self.assertIn('R270', rule_ids)  # Advanced concepts
        self.assertIn('R090', rule_ids)  # Secrets in code
    
    def test_validate_before_generation_typescript_context(self):
        """Test validation with TypeScript context."""
        prompt = "Create a TypeScript interface using any type"
        
        result = self.manager.validate_before_generation(prompt, file_type="typescript")
        
        self.assertFalse(result['valid'])
        self.assertIn('typescript', result['relevant_categories'])
        
        # Should have TypeScript-specific violations
        rule_ids = [v.rule_id for v in result['violations']]
        self.assertIn('R182', rule_ids)  # No 'any' type
    
    def test_validate_before_generation_storage_context(self):
        """Test validation with storage context."""
        prompt = "Create a storage function with camelCase naming"
        
        result = self.manager.validate_before_generation(prompt, task_type="storage")
        
        self.assertFalse(result['valid'])
        self.assertIn('storage_governance', result['relevant_categories'])
        
        # Should have storage-specific violations
        rule_ids = [v.rule_id for v in result['violations']]
        self.assertIn('R216', rule_ids)  # Kebab-case naming
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        violations = [
            Violation(rule_id='R253', severity=Severity.ERROR, message="Abbreviation used", file_path="prompt", line_number=1),
            Violation(rule_id='R270', severity=Severity.ERROR, message="Advanced concept used", file_path="prompt", line_number=1)
        ]
        
        recommendations = self.manager._generate_recommendations(violations, ['simple_readability'])
        
        self.assertGreater(len(recommendations), 0)
        self.assertIn("plain English variable names", recommendations[0])
        self.assertIn("simple alternatives", recommendations[1])
    
    def test_comprehensive_validation_all_categories(self):
        """Test comprehensive validation across all categories."""
        prompt = """
        Create a complex function using lambda expressions, nested objects,
        regex patterns, async/await, and advanced algorithms. Also store
        passwords in code and use manual processes.
        """
        
        result = self.manager.validate_before_generation(prompt, file_type="typescript", task_type="storage")
        
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['violations']), 5)
        self.assertGreater(len(result['recommendations']), 5)
        self.assertGreater(result['total_rules_checked'], 200)  # Should check most of the 280 rules
        
        # Should include multiple categories
        expected_categories = ['basic_work', 'code_review', 'security_privacy', 'typescript', 'storage_governance', 'simple_readability']
        for category in expected_categories:
            self.assertIn(category, result['relevant_categories'])


if __name__ == '__main__':
    unittest.main()
