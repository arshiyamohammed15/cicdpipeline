"""
Testing and safety rule validator.

This module implements validation for testing and safety rules:
- Rule 7: Never Break Things During Updates
- Rule 14: Test Everything + Handle Edge Cases Gracefully
- Rule 59: Build Safety Into Everything
"""

import ast
import re
from typing import List, Dict, Any, Tuple
from pathlib import Path
from ..models import Violation, Severity


class TestingValidator:
    """
    Validates testing and safety rules.
    
    This class focuses on detecting missing tests, unsafe operations,
    and lack of proper error handling and rollback mechanisms.
    """
    
    def __init__(self):
        """Initialize the testing validator."""
        self.risky_operations = [
            'open', 'file', 'requests', 'urllib', 'subprocess',
            'os.system', 'eval', 'exec', 'input', 'raw_input',
            'sql', 'query', 'execute', 'commit', 'rollback'
        ]
        
        self.safety_keywords = [
            'try', 'except', 'finally', 'rollback', 'undo', 'revert',
            'backup', 'restore', 'checkpoint', 'savepoint'
        ]
        
        self.test_keywords = [
            'test', 'spec', 'check', 'assert', 'verify', 'validate'
        ]
    
    def validate_test_coverage(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for test coverage.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of test coverage violations
        """
        violations = []
        
        # Check if this is a test file
        file_name = Path(file_path).name.lower()
        is_test_file = any(keyword in file_name for keyword in self.test_keywords)
        
        if not is_test_file:
            # Check if there are corresponding test files
            # This is a simplified check - in a real implementation,
            # you'd check for actual test files in the project
            has_test_functions = False
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if any(keyword in node.name.lower() for keyword in self.test_keywords):
                        has_test_functions = True
                        break
            
            if not has_test_functions:
                violations.append(Violation(
                rule_id="rule_14",
                rule_number=14,
                    rule_name="Test Everything",
                    severity=Severity.WARNING,
                    message="No test functions found in file",
                    file_path=file_path,
                    line_number=1,
                    column_number=0,
                    code_snippet="Missing tests",
                    fix_suggestion="Add test functions or create corresponding test file"
                ))
        
        return violations
    
    def validate_error_handling(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for proper error handling.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of error handling violations
        """
        violations = []
        
        # Check for try-catch blocks
        has_try_catch = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                has_try_catch = True
                break
        
        # Check for risky operations without error handling
        if not has_try_catch and self._has_risky_operations(tree):
            violations.append(Violation(
                rule_id="rule_14",
                rule_number=14,
                rule_name="Handle Edge Cases Gracefully",
                severity=Severity.WARNING,
                message="Risky operations without error handling detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Missing error handling",
                fix_suggestion="Add try-catch blocks around risky operations"
            ))
        
        return violations
    
    def validate_rollback_mechanisms(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for rollback mechanisms.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of rollback mechanism violations
        """
        violations = []
        
        # Check for rollback/undo mechanisms
        has_rollback = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func).lower()
                if any(keyword in func_name for keyword in ['rollback', 'undo', 'revert']):
                    has_rollback = True
                    break
        
        # Check for database operations without rollback
        has_db_operations = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func).lower()
                if any(keyword in func_name for keyword in ['commit', 'execute', 'insert', 'update', 'delete']):
                    has_db_operations = True
                    break
        
        if has_db_operations and not has_rollback:
            violations.append(Violation(
                rule_id="rule_7",
                rule_number=7,
                rule_name="Never Break Things During Updates",
                severity=Severity.WARNING,
                message="Database operations without rollback mechanism",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Missing rollback",
                fix_suggestion="Implement rollback mechanisms for safe updates"
            ))
        
        return violations
    
    def validate_safety_measures(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for safety measures.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of safety measure violations
        """
        violations = []
        
        # Check for dangerous operations
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func).lower()
                
                if any(keyword in func_name for keyword in ['delete', 'remove', 'drop', 'truncate']):
                    # Check if there's a confirmation or safety check
                    has_safety_check = False
                    
                    # Look for confirmation patterns in the same function
                    for child in ast.walk(node):
                        if isinstance(child, ast.If):
                            # Check if there's a confirmation check
                            if self._has_confirmation_check(child):
                                has_safety_check = True
                                break
                    
                    if not has_safety_check:
                        violations.append(Violation(
                rule_id="rule_59",
                rule_number=59,
                            rule_name="Build Safety Into Everything",
                            severity=Severity.WARNING,
                            message=f"Dangerous operation without safety check: {func_name}",
                            file_path=file_path,
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            code_snippet=func_name,
                            fix_suggestion="Add confirmation checks or safety measures for dangerous operations"
                        ))
        
        return violations
    
    def validate_backup_mechanisms(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for backup mechanisms.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of backup mechanism violations
        """
        violations = []
        
        # Check for file operations without backup
        has_file_operations = False
        has_backup = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func).lower()
                
                if any(keyword in func_name for keyword in ['write', 'save', 'create', 'modify']):
                    has_file_operations = True
                
                if any(keyword in func_name for keyword in ['backup', 'copy', 'duplicate']):
                    has_backup = True
        
        if has_file_operations and not has_backup:
            violations.append(Violation(
                rule_id="rule_59",
                rule_number=59,
                rule_name="Build Safety Into Everything",
                severity=Severity.INFO,
                message="File operations without backup mechanism",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Missing backup",
                fix_suggestion="Consider implementing backup mechanisms for file operations"
            ))
        
        return violations
    
    def validate_input_validation(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for input validation.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of input validation violations
        """
        violations = []
        
        # Check for input operations without validation
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func).lower()
                
                if any(keyword in func_name for keyword in ['input', 'raw_input', 'getpass']):
                    # Check if there's input validation
                    has_validation = False
                    
                    # Look for validation patterns
                    for child in ast.walk(node):
                        if isinstance(child, ast.If):
                            if self._has_validation_check(child):
                                has_validation = True
                                break
                    
                    if not has_validation:
                        violations.append(Violation(
                rule_id="rule_14",
                rule_number=14,
                            rule_name="Handle Edge Cases Gracefully",
                            severity=Severity.WARNING,
                            message="Input operation without validation",
                            file_path=file_path,
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            code_snippet=func_name,
                            fix_suggestion="Add input validation and sanitization"
                        ))
        
        return violations
    
    def _get_function_name(self, func_node: ast.AST) -> str:
        """Extract function name from AST node."""
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            return f"{self._get_function_name(func_node.value)}.{func_node.attr}"
        else:
            return str(func_node)
    
    def _has_risky_operations(self, tree: ast.AST) -> bool:
        """Check if code contains risky operations."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func).lower()
                if any(keyword in func_name for keyword in self.risky_operations):
                    return True
        return False
    
    def _has_confirmation_check(self, if_node: ast.If) -> bool:
        """Check if an if statement contains a confirmation check."""
        # Look for confirmation patterns
        confirmation_patterns = ['confirm', 'yes', 'y', 'ok', 'proceed']
        
        for node in ast.walk(if_node):
            if isinstance(node, ast.Compare):
                # Check if the comparison involves confirmation
                for child in ast.walk(node):
                    if isinstance(child, ast.Str):
                        if any(pattern in child.s.lower() for pattern in confirmation_patterns):
                            return True
        return False
    
    def _has_validation_check(self, if_node: ast.If) -> bool:
        """Check if an if statement contains input validation."""
        # Look for validation patterns
        validation_patterns = ['len', 'isinstance', 'isdigit', 'isalpha', 'strip', 'lower', 'upper']
        
        for node in ast.walk(if_node):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func).lower()
                if any(pattern in func_name for pattern in validation_patterns):
                    return True
        return False
    
    def validate_all(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Run all testing and safety validations.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of all testing/safety violations
        """
        violations = []
        
        violations.extend(self.validate_test_coverage(tree, file_path))
        violations.extend(self.validate_error_handling(tree, file_path))
        violations.extend(self.validate_rollback_mechanisms(tree, file_path))
        violations.extend(self.validate_safety_measures(tree, file_path))
        violations.extend(self.validate_backup_mechanisms(tree, file_path))
        violations.extend(self.validate_input_validation(tree, file_path))
        
        return violations
