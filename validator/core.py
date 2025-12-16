"""
Core validation engine for ZEROUI 2.0 Constitution rules.

This module provides the main validation logic that orchestrates
rule checking across different categories and generates compliance reports.
"""

import ast
import json
import re
import os
import time
from typing import Dict, List, Tuple, Any, Optional, Union
from pathlib import Path

from .models import Violation, ValidationResult, Severity
from .analyzer import CodeAnalyzer
from .reporter import ReportGenerator
from .factories import get_validator_factory

# Import enhanced configuration manager
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.enhanced_config_manager import EnhancedConfigManager


class ConstitutionValidator:
    """
    Main validator class that orchestrates rule checking.

    This class loads the constitution rules, analyzes code files,
    and generates compliance reports. The total rule count is validated
    against the single source of truth during CI.
    
    Uses dependency injection for better testability and maintainability.
    """

    def __init__(
        self,
        config_path: str = "config/constitution_rules.json",
        analyzer: Optional[CodeAnalyzer] = None,
        reporter: Optional[ReportGenerator] = None,
        config_manager: Optional[EnhancedConfigManager] = None,
        validator_factory = None
    ):
        """
        Initialize the validator with configuration and dependencies.

        Args:
            config_path: Path to the rules configuration JSON file
            analyzer: Optional CodeAnalyzer instance (injected dependency)
            reporter: Optional ReportGenerator instance (injected dependency)
            config_manager: Optional EnhancedConfigManager instance (injected dependency)
            validator_factory: Optional ValidatorFactory instance (injected dependency)
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # Dependency injection - use provided instances or create defaults
        self.analyzer = analyzer or CodeAnalyzer()
        self.reporter = reporter or ReportGenerator()
        self.config_manager = config_manager or EnhancedConfigManager()
        self.validator_factory = validator_factory or get_validator_factory()
        
        self.start_time = time.time()

    def _normalize_rule_ids(self, violations: List[Violation]) -> List[Violation]:
        """Ensure every violation has a rule_id; derive from rule_number if missing."""
        normalized = []
        for v in violations:
            if not getattr(v, "rule_id", None):
                try:
                    rn = int(getattr(v, "rule_number", 0))
                    setattr(v, "rule_id", f"rule_{rn:03d}" if rn > 0 else "rule_unknown")
                except Exception as e:
                    self._logger.warning(f"Failed to generate rule_id for violation: {e}", exc_info=True)
                    setattr(v, "rule_id", "rule_unknown")
            normalized.append(v)
        return normalized

    def get_rule_configuration_status(self) -> Dict[str, Any]:
        """Get current rule configuration status"""
        return self.config_manager.validate_configuration()

    def is_rule_enabled(self, rule_id: str, file_path: str = None) -> bool:
        """Check if a specific rule is enabled for a file"""
        # For now, assume all rules are enabled
        # This can be enhanced with file-specific rule overrides
        return True

    def _load_config(self) -> Dict[str, Any]:
        """Load validation configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")

    def validate_file(self, file_path: str, prompt: str = None) -> ValidationResult:
        """
        Validate a single Python file against constitution rules.

        Args:
            file_path: Path to the Python file to validate
            prompt: Optional prompt for pre-implementation validation

        Returns:
            ValidationResult containing all violations found
        """
        start_time = time.time()

        # Pre-implementation validation if prompt provided
        pre_validation_result = self._validate_pre_implementation(prompt, file_path, start_time)
        if pre_validation_result:
            return pre_validation_result

        # Read and parse file
        content, tree = self._read_and_parse_file(file_path, start_time)
        if isinstance(content, ValidationResult):
            return content

        # Analyze the code
        violations = self._check_all_rule_categories(tree, file_path, content)

        # Calculate metrics and return result
        return self._build_validation_result(file_path, violations, start_time)

    def _validate_pre_implementation(self, prompt: Optional[str], file_path: str, 
                                     start_time: float) -> Optional[ValidationResult]:
        """Perform pre-implementation validation if prompt is provided."""
        if not prompt:
            return None

        try:
            from .pre_implementation_hooks import PreImplementationHookManager
            hook_manager = PreImplementationHookManager()

            file_type = "typescript" if file_path.endswith(('.ts', '.tsx')) else "python"
            pre_result = hook_manager.validate_before_generation(prompt, file_type=file_type)

            if not pre_result['valid']:
                return ValidationResult(
                    file_path=file_path,
                    total_violations=len(pre_result['violations']),
                    violations_by_severity={Severity.ERROR: len(pre_result['violations'])},
                    violations=pre_result['violations'],
                    processing_time=time.time() - start_time,
                    compliance_score=0.0,
                    metadata={'pre_validation_failed': True, 'recommendations': pre_result['recommendations']}
                )
        except Exception as e:
            self._logger.warning(f"Warning: Pre-implementation validation failed: {e}", exc_info=True)
        return None

    def _read_and_parse_file(self, file_path: str, start_time: float) -> Union[tuple[str, ast.AST], ValidationResult]:
        """Read file content and parse into AST, handling errors."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise IOError(f"Could not read file {file_path}: {e}")

        # Parse the file into AST
        try:
            tree = ast.parse(content, filename=file_path)
            return content, tree
        except SyntaxError as e:
            violation = Violation(
                rule_id="syntax_error",
                rule_name="Syntax Error",
                severity=Severity.ERROR,
                message=f"Syntax error in file: {e.msg}",
                file_path=file_path,
                line_number=e.lineno or 0,
                column_number=e.offset or 0,
                code_snippet=content.split('\n')[e.lineno - 1] if e.lineno else "",
                fix_suggestion="Fix syntax errors before validation"
            )
            return ValidationResult(
                file_path=file_path,
                total_violations=1,
                violations_by_severity={Severity.ERROR: 1, Severity.WARNING: 0, Severity.INFO: 0},
                violations=[violation],
                processing_time=time.time() - start_time,
                compliance_score=0.0
            )

    def _check_all_rule_categories(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check all rule categories and return violations."""
        violations = []

        # Check each rule category (only if rules are enabled) and normalize rule_id
        violations.extend(self._normalize_rule_ids(self._check_basic_work_rules(tree, file_path, content)))
        violations.extend(self._normalize_rule_ids(self._check_requirements_rules(tree, file_path, content)))
        violations.extend(self._normalize_rule_ids(self._check_privacy_security_rules(tree, file_path, content)))
        violations.extend(self._normalize_rule_ids(self._check_performance_rules(tree, file_path, content)))
        violations.extend(self._normalize_rule_ids(self._check_architecture_rules(tree, file_path, content)))
        violations.extend(self._normalize_rule_ids(self._check_testing_safety_rules(tree, file_path, content)))
        violations.extend(self._normalize_rule_ids(self._check_code_quality_rules(tree, file_path, content)))
        violations.extend(self._normalize_rule_ids(self._check_system_design_rules(tree, file_path, content)))
        violations.extend(self._check_problem_solving_rules(tree, file_path, content))
        violations.extend(self._check_platform_rules(tree, file_path, content))
        violations.extend(self._check_teamwork_rules(tree, file_path, content))

        # Check new constitution categories
        violations.extend(self._check_code_review_rules(tree, file_path, content))
        violations.extend(self._check_api_contracts_rules(tree, file_path, content))
        violations.extend(self._check_coding_standards_rules(tree, file_path, content))
        violations.extend(self._check_comments_rules(tree, file_path, content))
        violations.extend(self._check_folder_standards_rules(tree, file_path, content))
        violations.extend(self._check_logging_rules(tree, file_path, content))
        violations.extend(self._check_exception_handling_rules(tree, file_path, content))
        violations.extend(self._check_typescript_rules(tree, file_path, content))
        violations.extend(self._check_storage_governance_rules(tree, file_path, content))

        return violations

    def _build_validation_result(self, file_path: str, violations: List[Violation], 
                                 start_time: float) -> ValidationResult:
        """Build and return ValidationResult from violations."""
        violations_by_severity = self._count_violations_by_severity(violations)
        total_violations = len(violations)
        compliance_score = self._calculate_compliance_score(violations, total_violations)
        processing_time = time.time() - start_time

        return ValidationResult(
            file_path=file_path,
            total_violations=total_violations,
            violations_by_severity=violations_by_severity,
            violations=violations,
            processing_time=processing_time,
            compliance_score=compliance_score
        )

    def _check_basic_work_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check basic work rules (4, 5, 10)."""
        violations = []
        validator = self.validator_factory.create('basic_work')
        if validator:
            violations.extend(validator.validate_all(tree, content, file_path))
        return violations

    def _check_requirements_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check requirements and specification rules (1, 2)."""
        violations = []
        validator = self.validator_factory.create('requirements')
        if validator:
            violations.extend(validator.validate_all(tree, content, file_path))
        return violations

    def _check_privacy_security_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check privacy and security rules (3, 11, 12, 27, 36)."""
        violations = []
        validator = self.validator_factory.create('privacy')
        if validator:
            violations.extend(validator.validate_all(tree, content, file_path))
        return violations

    def _check_performance_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check performance rules (8, 67)."""
        violations = []

        # Check if validation_patterns exists in config
        if "validation_patterns" not in self.config:
            return violations

        if "performance" not in self.config["validation_patterns"]:
            return violations

        patterns = self.config["validation_patterns"]["performance"]["patterns"]

        # Check for wildcard imports
        wildcard_pattern = patterns["large_imports"]["regex"]
        for match in re.finditer(wildcard_pattern, content):
            violations.append(Violation(
                rule_name="Make Things Fast",
                severity=Severity.WARNING,
                message=patterns["large_imports"]["message"],
                file_path=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                code_snippet=match.group(),
                fix_suggestion="Use specific imports instead of wildcard imports"
            ))

        # Check for blocking operations
        for keyword in patterns["blocking_operations"]["keywords"]:
            if keyword in content:
                line_num = content.find(keyword)
                violations.append(Violation(
                    rule_name="Respect People's Time",
                    severity=Severity.WARNING,
                    message=patterns["blocking_operations"]["message"],
                    file_path=file_path,
                    line_number=content[:line_num].count('\n') + 1,
                    column_number=line_num - content.rfind('\n', 0, line_num) - 1,
                    code_snippet=keyword,
                    fix_suggestion="Consider async alternatives for better performance"
                ))

        return violations

    def _check_architecture_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check architecture rules (19, 21, 23, 24, 28)."""
        violations = []
        validator = self.validator_factory.create('architecture')
        if validator:
            violations.extend(validator.validate_all(tree, content, file_path))
        return violations

    def _check_testing_safety_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check testing and safety rules (7, 14, 59, 69)."""
        violations = []

        # Check if validation_patterns exists in config
        if "validation_patterns" not in self.config:
            return violations

        if "testing_safety" not in self.config["validation_patterns"]:
            return violations

        patterns = self.config["validation_patterns"]["testing_safety"]["patterns"]

        # Check for error handling
        has_try_catch = any(keyword in content for keyword in patterns["error_handling"]["keywords"])
        if not has_try_catch and self._has_risky_operations(content):
            violations.append(Violation(
                rule_name="Handle Edge Cases Gracefully",
                severity=Severity.WARNING,
                message=patterns["missing_error_handling"]["message"],
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Risky operations without error handling",
                fix_suggestion="Add try-catch blocks around risky operations"
            ))

        # Check for test files
        if file_path.endswith('.py') and not any(test_indicator in file_path.lower()
                                               for test_indicator in ['test', 'spec', 'check']):
            # This is a basic check - in a real implementation, you'd check for corresponding test files
            pass

        return violations

    def _check_code_quality_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check code quality rules (15, 18, 68)."""
        violations = []

        # Check if validation_patterns exists in config
        if "validation_patterns" not in self.config:
            return violations

        if "code_quality" not in self.config["validation_patterns"]:
            return violations

        patterns = self.config["validation_patterns"]["code_quality"]["patterns"]

        # Check function length
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 10
                if func_lines > patterns["function_length"]["threshold"]:
                    violations.append(Violation(
                        rule_name="Write Clean, Readable Code",
                        severity=Severity.WARNING,
                        message=patterns["function_length"]["message"],
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=node.name,
                        fix_suggestion="Break function into smaller, focused functions"
                    ))

        # Check for missing docstrings
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not ast.get_docstring(node):
                violations.append(Violation(
                    rule_name="Write Good Instructions",
                    severity=Severity.WARNING,
                    message=patterns["missing_docstring"]["message"],
                    file_path=file_path,
                    line_number=node.lineno,
                    column_number=node.col_offset,
                    code_snippet=node.name,
                    fix_suggestion="Add docstring explaining function purpose and parameters"
                ))

        return violations

    def _has_risky_operations(self, content: str) -> bool:
        """Check if code contains risky operations that need error handling."""
        risky_keywords = [
            "open(", "file(", "requests.", "urllib", "subprocess",
            "os.system", "eval(", "exec(", "input(", "raw_input"
        ]
        return any(keyword in content for keyword in risky_keywords)

    def _check_system_design_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check system design rules (22, 25, 29, 30)."""
        violations = []
        validator = self.validator_factory.create('system_design')
        if validator:
            violations.extend(validator.validate_all(tree, content, file_path))
        return violations

    def _check_problem_solving_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check problem-solving rules (33, 35, 39)."""
        violations = []
        validator = self.validator_factory.create('problem_solving')
        if validator:
            violations.extend(validator.validate_all(tree, content, file_path))
        return violations

    def _check_platform_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check platform rules (42, 43)."""
        violations = []
        validator = self.validator_factory.create('platform')
        if validator:
            violations.extend(validator.validate_all(tree, content, file_path))
        return violations

    def _check_teamwork_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check teamwork rules (58)."""
        violations = []
        validator = self.validator_factory.create('teamwork')
        teamwork_validator = TeamworkValidator()

        # Run all teamwork validations
        violations.extend(teamwork_validator.validate_all(tree, content, file_path))

        return violations

    def _check_code_review_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check code review rules."""
        violations = []
        validator = self.validator_factory.create('code_review')
        if validator:
            # Some validators use validate() instead of validate_all()
            if hasattr(validator, 'validate'):
                violations.extend(validator.validate(file_path, content))
            else:
                violations.extend(validator.validate_all(tree, content, file_path))
        return violations

    def _check_api_contracts_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check API contracts rules."""
        violations = []
        validator = self.validator_factory.create('api_contracts')
        if validator:
            if hasattr(validator, 'validate'):
                violations.extend(validator.validate(file_path, content))
            else:
                violations.extend(validator.validate_all(tree, content, file_path))
        return violations

    def _check_coding_standards_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check coding standards rules."""
        violations = []
        validator = self.validator_factory.create('coding_standards')
        if validator:
            if hasattr(validator, 'validate'):
                violations.extend(validator.validate(file_path, content))
            else:
                violations.extend(validator.validate_all(tree, content, file_path))
        return violations

    def _check_comments_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check comments rules."""
        violations = []
        validator = self.validator_factory.create('comments')
        if validator:
            if hasattr(validator, 'validate'):
                violations.extend(validator.validate(file_path, content))
            else:
                violations.extend(validator.validate_all(tree, content, file_path))
        return violations

    def _check_folder_standards_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check folder standards rules."""
        violations = []
        validator = self.validator_factory.create('folder_standards')
        if validator:
            if hasattr(validator, 'validate'):
                violations.extend(validator.validate(file_path, content))
            else:
                violations.extend(validator.validate_all(tree, content, file_path))
        return violations

    def _check_logging_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check logging rules."""
        violations = []
        validator = self.validator_factory.create('logging')
        if validator:
            if hasattr(validator, 'validate'):
                violations.extend(validator.validate(file_path, content))
            else:
                violations.extend(validator.validate_all(tree, content, file_path))
        return violations

    def _check_exception_handling_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check exception handling rules (150-181)."""
        violations = []
        validator = self.validator_factory.create('exception_handling')
        exception_validator = ExceptionHandlingValidator()

        # Run all exception handling validations
        violations.extend(exception_validator.validate(file_path, content))

        return violations

    def _check_typescript_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check TypeScript rules (182-215)."""
        violations = []
        validator = self.validator_factory.create('typescript')
        if validator:
            # TypeScript validator has a different interface
            if hasattr(validator, 'validate_file'):
                typescript_violations = validator.validate_file(file_path, content)
                # Convert to Violation objects
                for violation in typescript_violations:
                    violations.append(Violation(
                        rule_id=violation.get('rule_id', 'typescript_rule'),
                        severity=Severity.ERROR if violation.get('severity') == 'error' else
                                Severity.WARNING if violation.get('severity') == 'warning' else Severity.INFO,
                        message=violation.get('message', 'TypeScript violation'),
                        line_number=violation.get('line', 0),
                        file_path=violation.get('file', file_path),
                        column_number=0,
                        code_snippet="",
                        fix_suggestion=""
                    ))
            elif hasattr(validator, 'validate'):
                violations.extend(validator.validate(file_path, content))
            else:
                violations.extend(validator.validate_all(tree, content, file_path))
        return violations

    def _check_storage_governance_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check storage governance rules (216-228)."""
        violations = []
        validator = self.validator_factory.create('storage_governance')
        if validator:
            if hasattr(validator, 'validate'):
                violations.extend(validator.validate(file_path, content))
            else:
                violations.extend(validator.validate_all(tree, content, file_path))
        return violations

    def _count_violations_by_severity(self, violations: List[Violation]) -> Dict[Severity, int]:
        """Count violations by severity level."""
        counts = {Severity.ERROR: 0, Severity.WARNING: 0, Severity.INFO: 0}
        for violation in violations:
            counts[violation.severity] += 1
        return counts

    def _calculate_compliance_score(self, violations: List[Violation], total_violations: int) -> float:
        """Calculate compliance score based on violations."""
        if total_violations == 0:
            return 100.0

        # Weight violations by severity
        error_weight = 3
        warning_weight = 2
        info_weight = 1

        weighted_violations = 0
        for violation in violations:
            if violation.severity == Severity.ERROR:
                weighted_violations += error_weight
            elif violation.severity == Severity.WARNING:
                weighted_violations += warning_weight
            else:
                weighted_violations += info_weight

        # Calculate score (higher is better)
        max_possible_violations = total_violations * error_weight
        score = max(0, 100 - (weighted_violations / max_possible_violations * 100))
        return round(score, 2)

    def validate_directory(self, directory_path: str, recursive: bool = True) -> Dict[str, ValidationResult]:
        """
        Validate all Python files in a directory.

        Args:
            directory_path: Path to directory to validate
            recursive: Whether to search subdirectories recursively

        Returns:
            Dictionary mapping file paths to validation results
        """
        results = {}
        directory = Path(directory_path)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        # Find Python files
        pattern = "**/*.py" if recursive else "*.py"
        python_files = list(directory.glob(pattern))

        if not python_files:
            self._logger.warning(f"No Python files found in {directory_path}")
            return results

        self._logger.info(f"Validating {len(python_files)} Python files...")

        for file_path in python_files:
            try:
                result = self.validate_file(str(file_path))
                results[str(file_path)] = result
                self._logger.info(f"[OK] {file_path.name}: {result.compliance_score}% compliance")
            except Exception as e:
                self._logger.error(f"[ERROR] Error validating {file_path}: {e}", exc_info=True)

        return results

    def generate_report(self, results: Dict[str, ValidationResult],
                       output_format: str = "console") -> str:
        """
        Generate a validation report.

        Args:
            results: Dictionary of validation results
            output_format: Format of the report ("console", "json", "html", "markdown")

        Returns:
            Generated report as string
        """
        return self.reporter.generate_report(results, output_format, self.config)
