#!/usr/bin/env python3
"""
TypeScript Rules Validator for ZeroUI 2.0

This module validates TypeScript code against Rules 182-215 from the constitution.
It enforces TypeScript coding standards, type safety, and best practices.
"""

import re
import ast
from typing import List, Dict, Any, Optional, Set
from pathlib import Path


class TypeScriptValidator:
    """
    Validator for TypeScript rules (R182-R215).

    Validates TypeScript code against 34 specific rules covering:
    - Type safety and strict mode
    - Null/undefined handling
    - Function clarity and naming
    - Type system usage
    - Async patterns
    - Project structure
    - Code quality
    - Security
    - AI-generated code review
    """

    def __init__(self):
        """Initialize the TypeScript validator."""
        self.rules = {
            'R182': self._validate_no_any_in_committed_code,
            'R183': self._validate_handle_null_undefined,
            'R184': self._validate_small_clear_functions,
            'R185': self._validate_consistent_naming,
            'R186': self._validate_clear_shape_strategy,
            'R187': self._validate_let_compiler_infer,
            'R188': self._validate_keep_imports_clean,
            'R189': self._validate_describe_the_shape,
            'R190': self._validate_union_narrowing,
            'R191': self._validate_readonly_by_default,
            'R192': self._validate_discriminated_unions,
            'R193': self._validate_utility_types_not_duplicates,
            'R194': self._validate_generics_but_simple,
            'R195': self._validate_no_unhandled_promises,
            'R196': self._validate_timeouts_cancel,
            'R197': self._validate_friendly_errors_at_edges,
            'R198': self._validate_map_errors_to_codes,
            'R199': self._validate_retries_are_limited,
            'R200': self._validate_one_source_of_truth,
            'R201': self._validate_folder_layout,
            'R202': self._validate_paths_aliases,
            'R203': self._validate_modern_output_targets,
            'R204': self._validate_lint_format,
            'R205': self._validate_type_check_in_ci,
            'R206': self._validate_tests_for_new_behavior,
            'R207': self._validate_comments_in_simple_english,
            'R208': self._validate_no_secrets_in_code_or_logs,
            'R209': self._validate_validate_untrusted_inputs_at_runtime,
            'R210': self._validate_keep_ui_responsive,
            'R211': self._validate_review_ai_code_thoroughly,
            'R212': self._validate_monitor_bundle_impact,
            'R213': self._validate_quality_dependencies,
            'R214': self._validate_test_type_boundaries,
            'R215': self._validate_gradual_migration_strategy
        }

    def validate_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """
        Validate a TypeScript file against all TypeScript rules.

        Args:
            file_path: Path to the TypeScript file
            content: File content as string

        Returns:
            List of validation violations
        """
        violations = []

        # Only validate TypeScript files
        if not file_path.endswith(('.ts', '.tsx')):
            return violations

        for rule_id, validator_func in self.rules.items():
            try:
                rule_violations = validator_func(file_path, content)
                violations.extend(rule_violations)
            except Exception as e:
                violations.append({
                    'rule_id': rule_id,
                    'severity': 'error',
                    'message': f'Validator error: {str(e)}',
                    'line': 0,
                    'file': file_path
                })

        return violations

    def _validate_no_any_in_committed_code(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """No `any` in committed code - use `unknown` and check it."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Look for `any` type usage
            if re.search(r'\bany\b', line) and not re.search(r'//.*any', line):
                # Allow in comments and type definitions that are being migrated
                if not re.search(r'//.*TODO.*any|//.*FIXME.*any|//.*@ts-ignore', line):
                    violations.append({
                        'rule_id': 'R182',
                        'severity': 'error',
                        'message': 'Use `unknown` instead of `any` and check it before use',
                        'line': i,
                        'file': file_path
                    })

        return violations

    def _validate_handle_null_undefined(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Handle `null`/`undefined` - check optional fields before use."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Look for potential null/undefined access without checks
            code_line = re.sub(r'//.*$', '', line)
            # Trigger on simple property access like user.name while ignoring optional chaining
            if re.search(r'\b\w+\.\w+', code_line) and not re.search(r'\?\.', code_line):
                # Check if there's a null check before this line
                has_null_check = False
                for j in range(max(0, i-5), i):
                    if j < len(lines) and re.search(r'if\s*\(.*\?\.|if\s*\(.*!==\s*null|if\s*\(.*!==\s*undefined|if\s*\(.*&&.*\)', lines[j]):
                        has_null_check = True
                        break

                if not has_null_check and re.search(r'\.\w+', code_line):
                    violations.append({
                        'rule_id': 'R183',
                        'severity': 'warning',
                        'message': 'Check for null/undefined before accessing properties',
                        'line': i,
                        'file': file_path
                    })

        return violations

    def _validate_small_clear_functions(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Small, Clear Functions - keep functions focused and readable."""
        violations = []
        lines = content.split('\n')

        function_start = None
        function_lines = 0

        for i, line in enumerate(lines, 1):
            # Detect function start
            if re.search(r'function\s+\w+|const\s+\w+\s*=\s*\(|export\s+function', line):
                function_start = i
                function_lines = 0

            if function_start:
                function_lines += 1

                # Check for function end
                if re.search(r'^}\s*$|^}\s*;?\s*$', line.strip()):
                    if function_lines > 20:  # More than 20 lines
                        violations.append({
                            'rule_id': 'R184',
                            'severity': 'warning',
                            'message': f'Function is {function_lines} lines long. Consider breaking into smaller functions.',
                            'line': function_start,
                            'file': file_path
                        })
                    function_start = None
                    function_lines = 0

        return violations

    def _validate_consistent_naming(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Consistent Naming - use clear, consistent naming conventions."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for inconsistent naming patterns
            if re.search(r'const\s+[a-z]+\w*[A-Z]', line):  # camelCase with capital
                violations.append({
                    'rule_id': 'R185',
                    'severity': 'warning',
                    'message': 'Use consistent camelCase naming for variables',
                    'line': i,
                    'file': file_path
                })

            # Check for unclear abbreviations
            if re.search(r'\b[a-z]{1,2}[A-Z]', line):  # Very short abbreviations
                violations.append({
                    'rule_id': 'R185',
                    'severity': 'info',
                    'message': 'Avoid unclear abbreviations in variable names',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_clear_shape_strategy(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Clear Shape Strategy - define clear interfaces and types."""
        violations = []
        lines = content.split('\n')

        has_interfaces = False
        has_types = False

        for i, line in enumerate(lines, 1):
            if re.search(r'interface\s+\w+', line):
                has_interfaces = True
            if re.search(r'type\s+\w+\s*=', line):
                has_types = True

        # Check if file has proper type definitions
        if not has_interfaces and not has_types:
            violations.append({
                'rule_id': 'R186',
                'severity': 'info',
                'message': 'Consider defining clear interfaces or types for data structures',
                'line': 1,
                'file': file_path
            })

        return violations

    def _validate_let_compiler_infer(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Let the Compiler Infer - avoid redundant type annotations."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for redundant type annotations
            if re.search(r'const\s+\w+\s*:\s*string\s*=\s*["\']', line):
                violations.append({
                    'rule_id': 'R187',
                    'severity': 'info',
                    'message': 'Let TypeScript infer string types from string literals',
                    'line': i,
                    'file': file_path
                })

            if re.search(r'const\s+\w+\s*:\s*number\s*=\s*\d+', line):
                violations.append({
                    'rule_id': 'R187',
                    'severity': 'info',
                    'message': 'Let TypeScript infer number types from numeric literals',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_keep_imports_clean(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Keep Imports Clean - organize and minimize imports."""
        violations = []
        lines = content.split('\n')

        import_lines = []
        for i, line in enumerate(lines, 1):
            if re.search(r'^\s*import\s+', line):
                import_lines.append(i)

        # Check for too many imports
        if len(import_lines) > 15:
            violations.append({
                'rule_id': 'R188',
                'severity': 'warning',
                'message': f'File has {len(import_lines)} imports. Consider organizing or splitting.',
                'line': import_lines[0],
                'file': file_path
            })

        # Check for wildcard imports
        for i, line in enumerate(lines, 1):
            if re.search(r'import\s+\*\s+as', line):
                violations.append({
                    'rule_id': 'R188',
                    'severity': 'warning',
                    'message': 'Avoid wildcard imports. Import specific functions instead.',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_describe_the_shape(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Describe the Shape - use interfaces for object shapes."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for inline object types that should be interfaces
            if re.search(r':\s*\{[^}]{20,}\}', line):  # Long inline object types
                violations.append({
                    'rule_id': 'R189',
                    'severity': 'info',
                    'message': 'Consider extracting inline object types to interfaces',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_union_narrowing(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Union & Narrowing - narrow union types before use."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Look for union types that might need narrowing
            if re.search(r'\|\s*string|\|\s*number|\|\s*boolean', line):
                # Check if there's proper type narrowing in the surrounding code
                has_narrowing = False
                for j in range(max(0, i-3), min(len(lines), i+3)):
                    if j < len(lines) and re.search(r'typeof\s+\w+|instanceof\s+\w+|in\s+\w+', lines[j]):
                        has_narrowing = True
                        break

                if not has_narrowing:
                    violations.append({
                        'rule_id': 'R190',
                        'severity': 'warning',
                        'message': 'Use type narrowing (typeof, instanceof, in) with union types',
                        'line': i,
                        'file': file_path
                    })

        return violations

    def _validate_readonly_by_default(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Readonly by Default - make data immutable when possible."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for mutable arrays/objects that could be readonly
            if re.search(r'const\s+\w+\s*:\s*Array<|const\s+\w+\s*:\s*\[\]', line):
                violations.append({
                    'rule_id': 'R191',
                    'severity': 'info',
                    'message': 'Consider using readonly arrays for immutable data',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_discriminated_unions(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Discriminated Unions - use discriminated unions for complex states."""
        violations = []
        lines = content.split('\n')

        # This is a complex rule that would need more sophisticated analysis
        # For now, provide a basic check
        for i, line in enumerate(lines, 1):
            if re.search(r'type\s+\w+\s*=\s*\{[^}]*type[^}]*\}', line):
                violations.append({
                    'rule_id': 'R192',
                    'severity': 'info',
                    'message': 'Consider using discriminated unions for complex state types',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_utility_types_not_duplicates(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Utility Types, Not Duplicates - use built-in utility types."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for manual implementations of utility types
            if re.search(r'type\s+\w+\s*=\s*\{[^}]*\?\s*:', line):
                violations.append({
                    'rule_id': 'R193',
                    'severity': 'info',
                    'message': 'Consider using built-in utility types like Partial<T>',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_generics_but_simple(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Generics, But Simple - keep generics simple and readable."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for overly complex generic constraints
            # Heuristics: long generic args, multiple constraints, or nested shapes
            if (re.search(r'<[^>]{20,}>', line) or
                re.search(r'<[^>]*(?:&|,[^,<>]+,[^,<>]+,)[^>]*>', line) or
                re.search(r'<[^>]*[\{\[][^{\]]{8,}[\}\]][^>]*>', line)):
                violations.append({
                    'rule_id': 'R194',
                    'severity': 'warning',
                    'message': 'Keep generic type parameters simple and readable',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_no_unhandled_promises(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """No Unhandled Promises - handle all promises properly."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Look for unhandled promises
            if re.search(r'\.then\(|\.catch\(|await\s+', line):
                # Check if promise is properly handled
                has_handling = re.search(r'\.catch\(|try\s*\{', line)
                if not has_handling:
                    violations.append({
                        'rule_id': 'R195',
                        'severity': 'error',
                        'message': 'Handle promise rejections with.catch() or try/catch',
                        'line': i,
                        'file': file_path
                    })

        return violations

    def _validate_timeouts_cancel(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Timeouts & Cancel - add timeouts to I/O operations."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Look for I/O operations without timeouts
            code_line = re.sub(r'//.*$', '', line)
            if re.search(r'fetch\(|axios\.|request\(', code_line) and not re.search(r'AbortController|AbortSignal|signal\s*:|AbortSignal\.timeout|timeout\s*\(', code_line):
                violations.append({
                    'rule_id': 'R196',
                    'severity': 'warning',
                    'message': 'Add timeouts to I/O operations to prevent hanging',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_friendly_errors_at_edges(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Friendly Errors at Edges - provide user-friendly error messages."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Look for technical error messages that should be user-friendly
            if re.search(r'throw\s+new\s+Error\([^)]{20,}\)', line):
                violations.append({
                    'rule_id': 'R197',
                    'severity': 'info',
                    'message': 'Provide user-friendly error messages at application boundaries',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_map_errors_to_codes(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Map Errors to Codes - use canonical error codes."""
        violations = []
        lines = content.split('\n')
        in_catch = False
        brace_depth = 0
        catch_start_line = 0
        block_lines: List[str] = []

        for i, raw_line in enumerate(lines, 1):
            line = re.sub(r'//.*$', '', raw_line)
            if not in_catch and re.search(r'\bcatch\s*\(', line):
                in_catch = True
                catch_start_line = i
                block_lines = [line]
                brace_depth = line.count('{') - line.count('}')
                continue
            if in_catch:
                block_lines.append(line)
                brace_depth += line.count('{') - line.count('}')
                if brace_depth <= 0:
                    block_text = "\n".join(block_lines)
                    # Flag generic console logging inside catch as missing code mapping
                    if re.search(r'console\.(error|log)\(', block_text) and not re.search(r'(error\.?code|\.code\s*=|map.*Error|ERROR_[A-Z_]+)', block_text):
                        violations.append({
                            'rule_id': 'R198',
                            'severity': 'warning',
                            'message': 'Map errors to canonical error codes for better debugging',
                            'line': catch_start_line,
                            'file': file_path
                        })
                    in_catch = False
                    brace_depth = 0
                    block_lines = []

        return violations

    def _validate_retries_are_limited(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Retries Are Limited - limit retry attempts with backoff."""
        violations = []
        lines = content.split('\n')
        for i, raw_line in enumerate(lines, 1):
            line = re.sub(r'//.*$', '', raw_line)
            # Detect obvious infinite/retry loops
            if re.search(r'while\s*\(\s*true\s*\)', line) or re.search(r'for\s*\(\s*;\s*;\s*\)', line):
                window = "\n".join(lines[max(0, i-5):min(len(lines), i+15)])
                if not re.search(r'maxRetries|maxAttempts|retryCount\s*<|attempts?\s*<|\bbackoff\b', window):
                    violations.append({
                        'rule_id': 'R199',
                        'severity': 'warning',
                        'message': 'Limit retry attempts and use exponential backoff',
                        'line': i,
                        'file': file_path
                    })

        return violations

    def _validate_one_source_of_truth(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """One Source of Truth - avoid duplicate type definitions."""
        violations = []
        lines = content.split('\n')

        # This would need more sophisticated analysis to detect duplicates
        # For now, provide a basic check
        type_definitions = []
        for i, line in enumerate(lines, 1):
            if re.search(r'type\s+(\w+)\s*=', line):
                type_name = re.search(r'type\s+(\w+)\s*=', line).group(1)
                if type_name in type_definitions:
                    violations.append({
                        'rule_id': 'R200',
                        'severity': 'warning',
                        'message': f'Duplicate type definition: {type_name}',
                        'line': i,
                        'file': file_path
                    })
                type_definitions.append(type_name)

        return violations

    def _validate_folder_layout(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Folder Layout - organize files in logical folder structure."""
        # This rule is more about project structure than file content
        violations = []

        # Check if file is in appropriate folder
        if 'types' in file_path and not file_path.endswith('.d.ts'):
            violations.append({
                'rule_id': 'R201',
                'severity': 'info',
                'message': 'Type definition files should have.d.ts extension',
                'line': 1,
                'file': file_path
            })

        return violations

    def _validate_paths_aliases(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Paths & Aliases - use path aliases for clean imports."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Look for relative imports that could use aliases
            if re.search(r'from\s+["\']\.\./\.\./\.\./', line):
                violations.append({
                    'rule_id': 'R202',
                    'severity': 'info',
                    'message': 'Consider using path aliases instead of deep relative imports',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_modern_output_targets(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Modern Output Targets - use modern compilation targets."""
        # This rule is about tsconfig.json, not individual files
        violations = []
        return violations

    def _validate_lint_format(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Lint & Format - ensure consistent code style."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for inconsistent formatting
            if re.search(r';\s*$', line) and i < len(lines) - 1:
                next_line = lines[i] if i < len(lines) else ""
                if not re.search(r';\s*$', next_line) and next_line.strip():
                    violations.append({
                        'rule_id': 'R204',
                        'severity': 'info',
                        'message': 'Maintain consistent semicolon usage',
                        'line': i,
                        'file': file_path
                    })

        return violations

    def _validate_type_check_in_ci(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Type Check in CI - ensure type checking in continuous integration."""
        # This rule is about CI configuration, not individual files
        violations = []
        return violations

    def _validate_tests_for_new_behavior(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Tests for New Behavior - write tests for new functionality."""
        violations = []

        # Check if this is a real test file (ignore only proper spec files or test directories)
        normalized_path = file_path.replace('\\', '/').lower()
        if re.search(r'\.spec\.[tj]sx?$', normalized_path) or re.search(r'/(tests?|__tests__)/', normalized_path):
            return violations

        # Look for new functions without corresponding tests
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if (re.search(r'export\s+function\s+\w+\s*\(', line) or
                re.search(r'export\s+default\s+function\s+\w*\s*\(', line) or
                re.search(r'export\s+(const|let|var)\s+\w+\s*=\s*\([^)]*\)\s*=>', line)):
                violations.append({
                    'rule_id': 'R206',
                    'severity': 'info',
                    'message': 'Ensure new functions have corresponding tests',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_comments_in_simple_english(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Comments in Simple English - write clear, simple comments."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for overly complex comments
            if re.search(r'//.*[A-Z]{5,}', line):  # Comments with many capital letters
                violations.append({
                    'rule_id': 'R207',
                    'severity': 'info',
                    'message': 'Write comments in simple, clear English',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_no_secrets_in_code_or_logs(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """No Secrets in Code or Logs - never commit secrets."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Look for potential secrets
            if re.search(r'password\s*=\s*["\'][^"\']+["\']|api[_-]?key\s*=\s*["\'][^"\']+["\']|secret\s*=\s*["\'][^"\']+["\']', line, re.IGNORECASE):
                violations.append({
                    'rule_id': 'R208',
                    'severity': 'error',
                    'message': 'Never commit secrets, passwords, or API keys to code',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_validate_untrusted_inputs_at_runtime(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Validate Untrusted Inputs at Runtime - validate external data."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Look for external data usage without validation
            if re.search(r'req\.body|req\.query|req\.params', line) and not re.search(r'validate|schema|zod', line):
                violations.append({
                    'rule_id': 'R209',
                    'severity': 'warning',
                    'message': 'Validate untrusted inputs at runtime',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_keep_ui_responsive(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Keep the UI Responsive - avoid blocking operations."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Look for synchronous operations that could block UI
            if re.search(r'JSON\.parse\(|JSON\.stringify\(|\.forEach\(', line) and 'async' not in line:
                violations.append({
                    'rule_id': 'R210',
                    'severity': 'info',
                    'message': 'Consider using async operations for large data processing',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_review_ai_code_thoroughly(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Review AI Code Thoroughly - always review AI-generated code."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Look for AI-generated code markers
            if re.search(r'//.*AI.*generated|//.*GPT|//.*Copilot', line, re.IGNORECASE):
                violations.append({
                    'rule_id': 'R211',
                    'severity': 'warning',
                    'message': 'AI-generated code must be thoroughly reviewed for type safety',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_monitor_bundle_impact(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Monitor Bundle Impact - watch for bundle size increases."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Look for large imports that could impact bundle size
            if re.search(r'import\s+.*\*.*from\s+["\']lodash["\']|import\s+.*\*.*from\s+["\']moment["\']', line):
                violations.append({
                    'rule_id': 'R212',
                    'severity': 'warning',
                    'message': 'Large library imports can significantly impact bundle size',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_quality_dependencies(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Quality Dependencies - use well-typed dependencies."""
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Look for untyped dependencies
            if re.search(r'import.*from\s+["\'][^"\']*["\']', line) and not re.search(r'@types/', line):
                # This is a basic check - would need package.json analysis for full validation
                violations.append({
                    'rule_id': 'R213',
                    'severity': 'info',
                    'message': 'Ensure dependencies have proper TypeScript definitions',
                    'line': i,
                    'file': file_path
                })

        return violations

    def _validate_test_type_boundaries(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Test Type Boundaries - test complex type interactions."""
        violations = []

        # Check if this is a test file
        if 'test' in file_path or 'spec' in file_path:
            lines = content.split('\n')
            has_type_tests = False

            for line in lines:
                if re.search(r'\btype\b.*\btest\b|\binterface\b.*\btest\b|expect\s*<.*>|expectType|satisfies\s', line):
                    has_type_tests = True
                    break

            if not has_type_tests:
                violations.append({
                    'rule_id': 'R214',
                    'severity': 'info',
                    'message': 'Consider adding type boundary tests for complex types',
                    'line': 1,
                    'file': file_path
                })

        return violations

    def _validate_gradual_migration_strategy(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Gradual Migration Strategy - migrate JavaScript to TypeScript gradually."""
        violations = []

        # Check for JavaScript files that should be migrated
        if file_path.endswith('.js') and not file_path.endswith('.d.ts'):
            violations.append({
                'rule_id': 'R215',
                'severity': 'info',
                'message': 'Consider migrating JavaScript files to TypeScript gradually',
                'line': 1,
                'file': file_path
            })

        return violations
