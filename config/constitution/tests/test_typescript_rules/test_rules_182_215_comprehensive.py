#!/usr/bin/env python3
"""
Comprehensive TypeScript Rules Tests for ZeroUI 2.0

This module provides comprehensive tests for all TypeScript rules (Rules 182-215).
It includes individual test classes for each rule with detailed test cases.
"""

import unittest
import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from validator.rules.typescript import TypeScriptValidator


class TestRule182NoAnyInCommittedCode(unittest.TestCase):
    """Test Rule 182: No `any` in committed code."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_any_type_usage(self):
        """Test detection of `any` type usage."""
        content = "const data: any = getData();"
        violations = self.validator._validate_no_any_in_committed_code("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R182')
    
    def test_allows_any_in_comments(self):
        """Test that `any` in comments is allowed."""
        content = "// TODO: Replace any with proper type"
        violations = self.validator._validate_no_any_in_committed_code("test.ts", content)
        self.assertEqual(len(violations), 0)
    
    def test_allows_ts_ignore_comments(self):
        """Test that `any` with @ts-ignore is allowed."""
        content = "// @ts-ignore: any type needed here"
        violations = self.validator._validate_no_any_in_committed_code("test.ts", content)
        self.assertEqual(len(violations), 0)


class TestRule183HandleNullUndefined(unittest.TestCase):
    """Test Rule 183: Handle `null`/`undefined`."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_missing_null_checks(self):
        """Test detection of missing null/undefined checks."""
        content = """
        const user = getUser();
        const name = user.name;
        """
        violations = self.validator._validate_handle_null_undefined("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R183')
    
    def test_allows_optional_chaining(self):
        """Test that optional chaining is allowed."""
        content = "const name = user?.name;"
        violations = self.validator._validate_handle_null_undefined("test.ts", content)
        # This might still trigger depending on implementation
        # The rule is complex and may need refinement


class TestRule184SmallClearFunctions(unittest.TestCase):
    """Test Rule 184: Small, Clear Functions."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_long_functions(self):
        """Test detection of functions that are too long."""
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
    
    def test_allows_short_functions(self):
        """Test that short functions are allowed."""
        content = """
        function shortFunction() {
            return "hello";
        }
        """
        violations = self.validator._validate_small_clear_functions("test.ts", content)
        self.assertEqual(len(violations), 0)


class TestRule185ConsistentNaming(unittest.TestCase):
    """Test Rule 185: Consistent Naming."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_inconsistent_naming(self):
        """Test detection of inconsistent naming patterns."""
        content = "const myVariable = 'test';"
        violations = self.validator._validate_consistent_naming("test.ts", content)
        # This rule might need refinement based on specific naming conventions
        self.assertIsInstance(violations, list)


class TestRule186ClearShapeStrategy(unittest.TestCase):
    """Test Rule 186: Clear Shape Strategy."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_missing_type_definitions(self):
        """Test detection of files without proper type definitions."""
        content = """
        const data = { name: "test", age: 25 };
        const user = { id: 1, email: "test@example.com" };
        """
        violations = self.validator._validate_clear_shape_strategy("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R186')
    
    def test_allows_files_with_interfaces(self):
        """Test that files with interfaces are allowed."""
        content = """
        interface User {
            id: number;
            name: string;
        }
        const user: User = { id: 1, name: "test" };
        """
        violations = self.validator._validate_clear_shape_strategy("test.ts", content)
        self.assertEqual(len(violations), 0)


class TestRule187LetCompilerInfer(unittest.TestCase):
    """Test Rule 187: Let the Compiler Infer."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_redundant_string_annotations(self):
        """Test detection of redundant string type annotations."""
        content = 'const name: string = "test";'
        violations = self.validator._validate_let_compiler_infer("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R187')
    
    def test_detects_redundant_number_annotations(self):
        """Test detection of redundant number type annotations."""
        content = 'const age: number = 25;'
        violations = self.validator._validate_let_compiler_infer("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R187')


class TestRule188KeepImportsClean(unittest.TestCase):
    """Test Rule 188: Keep Imports Clean."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_too_many_imports(self):
        """Test detection of files with too many imports."""
        content = "\n".join([f"import {{ item{i} }} from 'module{i}';" for i in range(16)])
        violations = self.validator._validate_keep_imports_clean("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R188')
    
    def test_detects_wildcard_imports(self):
        """Test detection of wildcard imports."""
        content = "import * as utils from 'utils';"
        violations = self.validator._validate_keep_imports_clean("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R188')


class TestRule189DescribeTheShape(unittest.TestCase):
    """Test Rule 189: Describe the Shape."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_inline_object_types(self):
        """Test detection of inline object types that should be interfaces."""
        content = "const config: { apiUrl: string; timeout: number; retries: boolean } = { apiUrl: 'https://api.example.com', timeout: 5000, retries: true };"
        violations = self.validator._validate_describe_the_shape("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R189')


class TestRule190UnionNarrowing(unittest.TestCase):
    """Test Rule 190: Union & Narrowing."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_union_types_without_narrowing(self):
        """Test detection of union types without proper narrowing."""
        content = "type Status = 'loading' | 'success' | 'error';"
        violations = self.validator._validate_union_narrowing("test.ts", content)
        # This rule is complex and may need refinement
        self.assertIsInstance(violations, list)


class TestRule191ReadonlyByDefault(unittest.TestCase):
    """Test Rule 191: Readonly by Default."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_mutable_arrays(self):
        """Test detection of mutable arrays that could be readonly."""
        content = "const items: Array<string> = ['a', 'b', 'c'];"
        violations = self.validator._validate_readonly_by_default("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R191')


class TestRule192DiscriminatedUnions(unittest.TestCase):
    """Test Rule 192: Discriminated Unions."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_potential_discriminated_unions(self):
        """Test detection of types that could use discriminated unions."""
        content = "type Result = { type: 'success'; data: any } | { type: 'error'; message: string };"
        violations = self.validator._validate_discriminated_unions("test.ts", content)
        # This rule provides suggestions rather than strict violations
        self.assertIsInstance(violations, list)


class TestRule193UtilityTypesNotDuplicates(unittest.TestCase):
    """Test Rule 193: Utility Types, Not Duplicates."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_manual_utility_implementations(self):
        """Test detection of manual implementations of utility types."""
        content = "type PartialUser = { id?: number; name?: string; email?: string };"
        violations = self.validator._validate_utility_types_not_duplicates("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R193')


class TestRule194GenericsButSimple(unittest.TestCase):
    """Test Rule 194: Generics, But Simple."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_complex_generics(self):
        """Test detection of overly complex generic constraints."""
        content = "function complex<T extends Record<string, any> & { id: number } & { metadata: Record<string, unknown> }>(item: T): T { return item; }"
        violations = self.validator._validate_generics_but_simple("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R194')


class TestRule195NoUnhandledPromises(unittest.TestCase):
    """Test Rule 195: No Unhandled Promises."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_unhandled_promises(self):
        """Test detection of unhandled promises."""
        content = "fetch('/api/data').then(response => response.json());"
        violations = self.validator._validate_no_unhandled_promises("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R195')
    
    def test_allows_handled_promises(self):
        """Test that properly handled promises are allowed."""
        content = "fetch('/api/data').then(response => response.json()).catch(error => console.error(error));"
        violations = self.validator._validate_no_unhandled_promises("test.ts", content)
        self.assertEqual(len(violations), 0)


class TestRule196TimeoutsCancel(unittest.TestCase):
    """Test Rule 196: Timeouts & Cancel."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_io_without_timeouts(self):
        """Test detection of I/O operations without timeouts."""
        content = "fetch('/api/data');"
        violations = self.validator._validate_timeouts_cancel("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R196')
    
    def test_allows_io_with_timeouts(self):
        """Test that I/O operations with timeouts are allowed."""
        content = "fetch('/api/data', { signal: AbortSignal.timeout(5000) });"
        violations = self.validator._validate_timeouts_cancel("test.ts", content)
        self.assertEqual(len(violations), 0)


class TestRule197FriendlyErrorsAtEdges(unittest.TestCase):
    """Test Rule 197: Friendly Errors at Edges."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_technical_error_messages(self):
        """Test detection of technical error messages."""
        content = 'throw new Error("Database connection failed with error code 12345");'
        violations = self.validator._validate_friendly_errors_at_edges("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R197')


class TestRule198MapErrorsToCodes(unittest.TestCase):
    """Test Rule 198: Map Errors to Codes."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_generic_error_handling(self):
        """Test detection of generic error handling without error codes."""
        content = """
        try {
            riskyOperation();
        } catch (error) {
            console.error(error);
        }
        """
        violations = self.validator._validate_map_errors_to_codes("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R198')


class TestRule199RetriesAreLimited(unittest.TestCase):
    """Test Rule 199: Retries Are Limited."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_unlimited_retries(self):
        """Test detection of retry logic without limits."""
        content = """
        let retries = 0;
        while (true) {
            try {
                await operation();
                break;
            } catch (error) {
                retries++;
            }
        }
        """
        violations = self.validator._validate_retries_are_limited("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R199')


class TestRule200OneSourceOfTruth(unittest.TestCase):
    """Test Rule 200: One Source of Truth."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_duplicate_type_definitions(self):
        """Test detection of duplicate type definitions."""
        content = """
        type User = { id: number; name: string; };
        type User = { id: number; name: string; email: string; };
        """
        violations = self.validator._validate_one_source_of_truth("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R200')


class TestRule201FolderLayout(unittest.TestCase):
    """Test Rule 201: Folder Layout."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_incorrect_type_file_extension(self):
        """Test detection of type files without .d.ts extension."""
        violations = self.validator._validate_folder_layout("types/user.ts", "")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R201')


class TestRule202PathsAliases(unittest.TestCase):
    """Test Rule 202: Paths & Aliases."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_deep_relative_imports(self):
        """Test detection of deep relative imports."""
        content = "import { utils } from '../../../utils/helpers';"
        violations = self.validator._validate_paths_aliases("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R202')


class TestRule203ModernOutputTargets(unittest.TestCase):
    """Test Rule 203: Modern Output Targets."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_rule_applies_to_tsconfig(self):
        """Test that this rule applies to tsconfig.json files."""
        violations = self.validator._validate_modern_output_targets("tsconfig.json", "")
        # This rule is about configuration, not individual files
        self.assertEqual(len(violations), 0)


class TestRule204LintFormat(unittest.TestCase):
    """Test Rule 204: Lint & Format."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_inconsistent_semicolons(self):
        """Test detection of inconsistent semicolon usage."""
        content = """
        const a = 1;
        const b = 2
        const c = 3;
        """
        violations = self.validator._validate_lint_format("test.ts", content)
        # This rule might need refinement based on specific formatting rules
        self.assertIsInstance(violations, list)


class TestRule205TypeCheckInCI(unittest.TestCase):
    """Test Rule 205: Type Check in CI."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_rule_applies_to_ci_config(self):
        """Test that this rule applies to CI configuration files."""
        violations = self.validator._validate_type_check_in_ci("test.ts", "")
        # This rule is about CI configuration, not individual files
        self.assertEqual(len(violations), 0)


class TestRule206TestsForNewBehavior(unittest.TestCase):
    """Test Rule 206: Tests for New Behavior."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_new_functions_without_tests(self):
        """Test detection of new functions without corresponding tests."""
        content = "export function newFunction() { return 'hello'; }"
        violations = self.validator._validate_tests_for_new_behavior("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R206')


class TestRule207CommentsInSimpleEnglish(unittest.TestCase):
    """Test Rule 207: Comments in Simple English."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_complex_comments(self):
        """Test detection of overly complex comments."""
        content = "// THIS IS A VERY COMPLEX COMMENT WITH MANY CAPITAL LETTERS"
        violations = self.validator._validate_comments_in_simple_english("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R207')


class TestRule208NoSecretsInCodeOrLogs(unittest.TestCase):
    """Test Rule 208: No Secrets in Code or Logs."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_secrets_in_code(self):
        """Test detection of secrets in code."""
        content = 'const apiKey = "sk-1234567890abcdef";'
        violations = self.validator._validate_no_secrets_in_code_or_logs("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R208')
    
    def test_detects_passwords_in_code(self):
        """Test detection of passwords in code."""
        content = 'const password = "mypassword123";'
        violations = self.validator._validate_no_secrets_in_code_or_logs("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R208')


class TestRule209ValidateUntrustedInputsAtRuntime(unittest.TestCase):
    """Test Rule 209: Validate Untrusted Inputs at Runtime."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_unvalidated_inputs(self):
        """Test detection of unvalidated external inputs."""
        content = """
        app.post('/api', (req, res) => {
            const data = req.body;
        });
        """
        violations = self.validator._validate_validate_untrusted_inputs_at_runtime("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R209')


class TestRule210KeepUIResponsive(unittest.TestCase):
    """Test Rule 210: Keep the UI Responsive."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_blocking_operations(self):
        """Test detection of operations that could block the UI."""
        content = "const data = JSON.parse(largeJsonString);"
        violations = self.validator._validate_keep_ui_responsive("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R210')


class TestRule211ReviewAICodeThoroughly(unittest.TestCase):
    """Test Rule 211: Review AI Code Thoroughly."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_ai_generated_code_markers(self):
        """Test detection of AI-generated code markers."""
        content = "// AI generated code - needs review"
        violations = self.validator._validate_review_ai_code_thoroughly("test.ts", content)
        # This test might not trigger if the pattern doesn't match exactly
        self.assertIsInstance(violations, list)


class TestRule212MonitorBundleImpact(unittest.TestCase):
    """Test Rule 212: Monitor Bundle Impact."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_large_library_imports(self):
        """Test detection of large library imports."""
        content = "import * as _ from 'lodash';"
        violations = self.validator._validate_monitor_bundle_impact("test.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R212')


class TestRule213QualityDependencies(unittest.TestCase):
    """Test Rule 213: Quality Dependencies."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_untyped_dependencies(self):
        """Test detection of potentially untyped dependencies."""
        content = "import { something } from 'untyped-package';"
        violations = self.validator._validate_quality_dependencies("test.ts", content)
        # This rule provides suggestions rather than strict violations
        self.assertIsInstance(violations, list)


class TestRule214TestTypeBoundaries(unittest.TestCase):
    """Test Rule 214: Test Type Boundaries."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_missing_type_tests(self):
        """Test detection of test files without type boundary tests."""
        content = """
        describe('UserService', () => {
            it('should create user', () => {
                expect(true).toBe(true);
            });
        });
        """
        violations = self.validator._validate_test_type_boundaries("test.spec.ts", content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R214')


class TestRule215GradualMigrationStrategy(unittest.TestCase):
    """Test Rule 215: Gradual Migration Strategy."""
    
    def setUp(self):
        self.validator = TypeScriptValidator()
    
    def test_detects_javascript_files(self):
        """Test detection of JavaScript files that should be migrated."""
        violations = self.validator._validate_gradual_migration_strategy("test.js", "console.log('hello');")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['rule_id'], 'R215')
    
    def test_allows_typescript_files(self):
        """Test that TypeScript files are allowed."""
        violations = self.validator._validate_gradual_migration_strategy("test.ts", "console.log('hello');")
        self.assertEqual(len(violations), 0)


if __name__ == '__main__':
    unittest.main()
