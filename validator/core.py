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
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

from .models import Violation, ValidationResult, Severity
from .analyzer import CodeAnalyzer
from .reporter import ReportGenerator


class ConstitutionValidator:
    """
    Main validator class that orchestrates rule checking.
    
    This class loads the constitution rules, analyzes code files,
    and generates compliance reports based on the 71 unique rules.
    """
    
    def __init__(self, config_path: str = "rules_config.json"):
        """
        Initialize the validator with configuration.
        
        Args:
            config_path: Path to the rules configuration JSON file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.analyzer = CodeAnalyzer()
        self.reporter = ReportGenerator()
        self.start_time = time.time()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load validation configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def validate_file(self, file_path: str) -> ValidationResult:
        """
        Validate a single Python file against constitution rules.
        
        Args:
            file_path: Path to the Python file to validate
            
        Returns:
            ValidationResult containing all violations found
        """
        start_time = time.time()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise IOError(f"Could not read file {file_path}: {e}")
        
        # Parse the file into AST
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as e:
            # Handle syntax errors as critical violations
            violation = Violation(
                rule_number=14,  # Test Everything
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
        
        # Analyze the code
        violations = []
        
        # Check each rule category
        violations.extend(self._check_basic_work_rules(tree, file_path, content))
        violations.extend(self._check_requirements_rules(tree, file_path, content))
        violations.extend(self._check_privacy_security_rules(tree, file_path, content))
        violations.extend(self._check_performance_rules(tree, file_path, content))
        violations.extend(self._check_architecture_rules(tree, file_path, content))
        violations.extend(self._check_testing_safety_rules(tree, file_path, content))
        violations.extend(self._check_code_quality_rules(tree, file_path, content))
        violations.extend(self._check_system_design_rules(tree, file_path, content))
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
        
        # Calculate metrics
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
        from .rules.basic_work import BasicWorkValidator
        basic_work_validator = BasicWorkValidator()
        violations.extend(basic_work_validator.validate_all(tree, content, file_path))
        return violations
    
    def _check_requirements_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check requirements and specification rules (1, 2)."""
        violations = []
        
        # Import the requirements validator
        from .rules.requirements import RequirementsValidator
        requirements_validator = RequirementsValidator()
        
        # Run all requirements validations
        violations.extend(requirements_validator.validate_all(tree, content, file_path))
        
        return violations
    
    def _check_privacy_security_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check privacy and security rules (3, 11, 12, 27, 36)."""
        violations = []
        
        # Import the privacy validator
        from .rules.privacy import PrivacyValidator
        privacy_validator = PrivacyValidator()
        
        # Run all privacy validations
        violations.extend(privacy_validator.validate_all(tree, content, file_path))
        
        return violations
    
    def _check_performance_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check performance rules (8, 67)."""
        violations = []
        patterns = self.config["validation_patterns"]["performance"]["patterns"]
        
        # Check for wildcard imports
        wildcard_pattern = patterns["large_imports"]["regex"]
        for match in re.finditer(wildcard_pattern, content):
            violations.append(Violation(
                rule_number=8,
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
                    rule_number=67,
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
        
        # Import the architecture validator
        from .rules.architecture import ArchitectureValidator
        architecture_validator = ArchitectureValidator()
        
        # Run all architecture validations
        violations.extend(architecture_validator.validate_all(tree, content, file_path))
        
        return violations
    
    def _check_testing_safety_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check testing and safety rules (7, 14, 59, 69)."""
        violations = []
        patterns = self.config["validation_patterns"]["testing_safety"]["patterns"]
        
        # Check for error handling
        has_try_catch = any(keyword in content for keyword in patterns["error_handling"]["keywords"])
        if not has_try_catch and self._has_risky_operations(content):
            violations.append(Violation(
                rule_number=69,
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
        patterns = self.config["validation_patterns"]["code_quality"]["patterns"]
        
        # Check function length
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 10
                if func_lines > patterns["function_length"]["threshold"]:
                    violations.append(Violation(
                        rule_number=68,
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
                    rule_number=15,
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
        
        # Import the system design validator
        from .rules.system_design import SystemDesignValidator
        system_design_validator = SystemDesignValidator()
        
        # Run all system design validations
        violations.extend(system_design_validator.validate_all(tree, content, file_path))
        
        return violations
    
    def _check_problem_solving_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check problem-solving rules (33, 35, 39)."""
        violations = []
        
        # Import the problem-solving validator
        from .rules.problem_solving import ProblemSolvingValidator
        problem_solving_validator = ProblemSolvingValidator()
        
        # Run all problem-solving validations
        violations.extend(problem_solving_validator.validate_all(tree, content, file_path))
        
        return violations
    
    def _check_platform_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check platform rules (42, 43)."""
        violations = []
        
        # Import the platform validator
        from .rules.platform import PlatformValidator
        platform_validator = PlatformValidator()
        
        # Run all platform validations
        violations.extend(platform_validator.validate_all(tree, content, file_path))
        
        return violations
    
    def _check_teamwork_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check teamwork rules (58)."""
        violations = []
        
        # Import the teamwork validator
        from .rules.teamwork import TeamworkValidator
        teamwork_validator = TeamworkValidator()
        
        # Run all teamwork validations
        violations.extend(teamwork_validator.validate_all(tree, content, file_path))
        
        return violations
    
    def _check_code_review_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check code review rules."""
        violations = []
        
        # Import the code review validator
        from .rules.code_review import CodeReviewValidator
        code_review_validator = CodeReviewValidator()
        
        # Run all code review validations
        violations.extend(code_review_validator.validate(file_path, content))
        
        return violations
    
    def _check_api_contracts_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check API contracts rules."""
        violations = []
        
        # Import the API contracts validator
        from .rules.api_contracts import APIContractsValidator
        api_contracts_validator = APIContractsValidator()
        
        # Run all API contracts validations
        violations.extend(api_contracts_validator.validate(file_path, content))
        
        return violations
    
    def _check_coding_standards_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check coding standards rules."""
        violations = []
        
        # Import the coding standards validator
        from .rules.coding_standards import CodingStandardsValidator
        coding_standards_validator = CodingStandardsValidator()
        
        # Run all coding standards validations
        violations.extend(coding_standards_validator.validate(file_path, content))
        
        return violations
    
    def _check_comments_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check comments rules."""
        violations = []
        
        # Import the comments validator
        from .rules.comments import CommentsValidator
        comments_validator = CommentsValidator()
        
        # Run all comments validations
        violations.extend(comments_validator.validate(file_path, content))
        
        return violations
    
    def _check_folder_standards_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check folder standards rules."""
        violations = []
        
        # Import the folder standards validator
        from .rules.folder_standards import FolderStandardsValidator
        folder_standards_validator = FolderStandardsValidator()
        
        # Run all folder standards validations
        violations.extend(folder_standards_validator.validate(file_path, content))
        
        return violations
    
    def _check_logging_rules(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """Check logging rules."""
        violations = []
        
        # Import the logging validator
        from .rules.logging import LoggingValidator
        logging_validator = LoggingValidator()
        
        # Run all logging validations
        violations.extend(logging_validator.validate(file_path, content))
        
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
            print(f"No Python files found in {directory_path}")
            return results
        
        print(f"Validating {len(python_files)} Python files...")
        
        for file_path in python_files:
            try:
                result = self.validate_file(str(file_path))
                results[str(file_path)] = result
                print(f"[OK] {file_path.name}: {result.compliance_score}% compliance")
            except Exception as e:
                print(f"[ERROR] Error validating {file_path}: {e}")
        
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
