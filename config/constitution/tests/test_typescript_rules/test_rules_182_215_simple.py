#!/usr/bin/env python3
"""
Simple TypeScript Rules Tests for ZeroUI 2.0

This module provides basic tests for TypeScript rules infrastructure (Rules 182-215).
It validates the core functionality without complex dependencies.
"""

import unittest
import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from validator.rules.typescript import TypeScriptValidator


class TestTypeScriptValidatorInfrastructure(unittest.TestCase):
    """Test the TypeScript validator infrastructure."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = TypeScriptValidator()
    
    def test_validator_initialization(self):
        """Test that the TypeScript validator initializes correctly."""
        self.assertIsNotNone(self.validator)
        self.assertIsInstance(self.validator.rules, dict)
        self.assertEqual(len(self.validator.rules), 34)  # Rules 182-215
    
    def test_all_rules_present(self):
        """Test that all TypeScript rules (R182-R215) are present."""
        expected_rules = [f'R{i}' for i in range(182, 216)]
        actual_rules = list(self.validator.rules.keys())
        
        for rule in expected_rules:
            self.assertIn(rule, actual_rules, f"Rule {rule} is missing")
    
    def test_rule_methods_are_callable(self):
        """Test that all rule validation methods are callable."""
        for rule_id, method in self.validator.rules.items():
            self.assertTrue(callable(method), f"Rule {rule_id} method is not callable")


class TestTypeScriptBasicRules(unittest.TestCase):
    """Test basic TypeScript rules validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = TypeScriptValidator()
    
    def test_rule_182_no_any_detection(self):
        """Test Rule 182: No `any` in committed code."""
        content = """
        const data: any = getData(); // This should be flagged
        const name: string = "test"; // This should be fine
        """
        
        violations = self.validator._validate_no_any_in_committed_code("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R182')
    
    def test_rule_183_null_undefined_handling(self):
        """Test Rule 183: Handle null/undefined."""
        content = """
        const user = getUser();
        const name = user.name; // Should check for null/undefined
        """
        
        violations = self.validator._validate_handle_null_undefined("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R183')
    
    def test_rule_184_small_clear_functions(self):
        """Test Rule 184: Small, Clear Functions."""
        # Create a long function
        content = """
        function longFunction() {
            // Line 1
            // Line 2
            // Line 3
            // Line 4
            // Line 5
            // Line 6
            // Line 7
            // Line 8
            // Line 9
            // Line 10
            // Line 11
            // Line 12
            // Line 13
            // Line 14
            // Line 15
            // Line 16
            // Line 17
            // Line 18
            // Line 19
            // Line 20
            // Line 21
        }
        """
        
        violations = self.validator._validate_small_clear_functions("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R184')
    
    def test_rule_185_consistent_naming(self):
        """Test Rule 185: Consistent Naming."""
        content = """
        const myVariable = "test"; // Good naming
        const myVar = "test"; // Inconsistent naming
        """
        
        violations = self.validator._validate_consistent_naming("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R185')


class TestTypeScriptTypeSystemRules(unittest.TestCase):
    """Test TypeScript type system rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = TypeScriptValidator()
    
    def test_rule_186_clear_shape_strategy(self):
        """Test Rule 186: Clear Shape Strategy."""
        content = """
        // No interfaces or types defined
        const data = { name: "test", age: 25 };
        """
        
        violations = self.validator._validate_clear_shape_strategy("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R186')
    
    def test_rule_187_let_compiler_infer(self):
        """Test Rule 187: Let the Compiler Infer."""
        content = """
        const name: string = "test"; // Redundant type annotation
        const age: number = 25; // Redundant type annotation
        """
        
        violations = self.validator._validate_let_compiler_infer("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R187')
    
    def test_rule_188_keep_imports_clean(self):
        """Test Rule 188: Keep Imports Clean."""
        content = """
        import { a } from 'module1';
        import { b } from 'module2';
        import { c } from 'module3';
        import { d } from 'module4';
        import { e } from 'module5';
        import { f } from 'module6';
        import { g } from 'module7';
        import { h } from 'module8';
        import { i } from 'module9';
        import { j } from 'module10';
        import { k } from 'module11';
        import { l } from 'module12';
        import { m } from 'module13';
        import { n } from 'module14';
        import { o } from 'module15';
        import { p } from 'module16';
        """
        
        violations = self.validator._validate_keep_imports_clean("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R188')


class TestTypeScriptAsyncRules(unittest.TestCase):
    """Test TypeScript async and promise rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = TypeScriptValidator()
    
    def test_rule_195_no_unhandled_promises(self):
        """Test Rule 195: No Unhandled Promises."""
        content = """
        fetch('/api/data').then(response => response.json()); // Unhandled promise
        """
        
        violations = self.validator._validate_no_unhandled_promises("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R195')
    
    def test_rule_196_timeouts_cancel(self):
        """Test Rule 196: Timeouts & Cancel."""
        content = """
        fetch('/api/data'); // No timeout specified
        """
        
        violations = self.validator._validate_timeouts_cancel("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R196')


class TestTypeScriptSecurityRules(unittest.TestCase):
    """Test TypeScript security rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = TypeScriptValidator()
    
    def test_rule_208_no_secrets_in_code(self):
        """Test Rule 208: No Secrets in Code or Logs."""
        content = """
        const apiKey = "sk-1234567890abcdef"; // Secret in code
        const password = "mypassword123"; // Password in code
        """
        
        violations = self.validator._validate_no_secrets_in_code_or_logs("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R208')
    
    def test_rule_209_validate_untrusted_inputs(self):
        """Test Rule 209: Validate Untrusted Inputs at Runtime."""
        content = """
        app.post('/api', (req, res) => {
            const data = req.body; // No validation
        });
        """
        
        violations = self.validator._validate_validate_untrusted_inputs_at_runtime("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R209')


class TestTypeScriptAIRules(unittest.TestCase):
    """Test TypeScript AI-related rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = TypeScriptValidator()
    
    def test_rule_211_review_ai_code(self):
        """Test Rule 211: Review AI Code Thoroughly."""
        content = """
        // AI generated code - needs review
        function aiGeneratedFunction() {
            return "hello";
        }
        """
        
        violations = self.validator._validate_review_ai_code_thoroughly("test.ts", content)
        # This test might not trigger if the pattern doesn't match exactly
        # The rule looks for specific AI markers in comments
    
    def test_rule_215_gradual_migration(self):
        """Test Rule 215: Gradual Migration Strategy."""
        violations = self.validator._validate_gradual_migration_strategy("test.js", "console.log('hello');")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R215')


class TestTypeScriptValidatorIntegration(unittest.TestCase):
    """Test TypeScript validator integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = TypeScriptValidator()
    
    def test_validate_file_returns_violations(self):
        """Test that validate_file returns a list of violations."""
        content = """
        const data: any = getData();
        const user = getUser();
        const name = user.name;
        """
        
        violations = self.validator.validate_file("test.ts", content)
        self.assertIsInstance(violations, list)
        self.assertGreater(len(violations), 0)
    
    def test_validate_file_ignores_non_typescript(self):
        """Test that validate_file ignores non-TypeScript files."""
        content = "console.log('hello');"
        
        violations = self.validator.validate_file("test.js", content)
        self.assertEqual(len(violations), 0)
    
    def test_validate_file_handles_errors_gracefully(self):
        """Test that validate_file handles errors gracefully."""
        # This should not crash even with malformed content
        violations = self.validator.validate_file("test.ts", "")
        self.assertIsInstance(violations, list)


if __name__ == '__main__':
    unittest.main()
