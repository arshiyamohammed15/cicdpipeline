"""
Performance rule validator.

This module implements validation for performance rules:
- Rule 8: Make Things Fast + Respect People's Time
- Rule 67: Respect People's Time (merged with Rule 8)
"""

import ast
import re
from typing import List, Dict, Any, Tuple
from ..models import Violation, Severity


class PerformanceValidator:
    """
    Validates performance-related rules.
    
    This class focuses on detecting performance issues like inefficient
    loops, blocking operations, and other time-consuming patterns.
    """
    
    def __init__(self):
        """Initialize the performance validator."""
        self.blocking_operations = [
            'time.sleep', 'input', 'raw_input', 'getpass.getpass',
            'os.system', 'subprocess.call', 'subprocess.run'
        ]
        
        self.inefficient_patterns = [
            r'for\s+\w+\s+in\s+range\s*\(\s*len\s*\(',
            r'\.append\s*\(\s*\[\s*\]\s*\)',  # List of lists
            r'\.join\s*\(\s*\[\s*str\s*\('  # String concatenation in loops
        ]
        
        self.import_performance_issues = [
            'import *', 'from * import *'
        ]
    
    def validate_startup_time(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for startup time issues.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of startup time violations
        """
        violations = []
        
        # Check for wildcard imports
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == '*':
                    violations.append(Violation(
                rule_id="rule_8",
                rule_number=8,
                        rule_name="Make Things Fast",
                        severity=Severity.WARNING,
                        message="Wildcard import detected - can impact startup time",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet="from * import *",
                        fix_suggestion="Use specific imports instead of wildcard imports"
                    ))
        
        return violations
    
    def validate_blocking_operations(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for blocking operations.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of blocking operation violations
        """
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                
                for blocking_op in self.blocking_operations:
                    if blocking_op in func_name:
                        violations.append(Violation(
                rule_id="rule_67",
                rule_number=67,
                            rule_name="Respect People's Time",
                            severity=Severity.WARNING,
                            message=f"Blocking operation detected: {func_name}",
                            file_path=file_path,
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            code_snippet=func_name,
                            fix_suggestion="Consider async alternatives for better performance"
                        ))
        
        return violations
    
    def validate_loop_efficiency(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for inefficient loop patterns.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of loop efficiency violations
        """
        violations = []
        
        # Check for nested loops
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Check if this loop contains another loop
                for child in ast.walk(node):
                    if child != node and isinstance(child, (ast.For, ast.While)):
                        violations.append(Violation(
                rule_id="rule_8",
                rule_number=8,
                            rule_name="Make Things Fast",
                            severity=Severity.WARNING,
                            message="Nested loops detected - consider optimization for O(n²) complexity",
                            file_path=file_path,
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            code_snippet=f"{type(node).__name__} contains {type(child).__name__}",
                            fix_suggestion="Consider using list comprehensions, built-in functions, or vectorized operations"
                        ))
        
        return violations
    
    def validate_memory_usage(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for memory usage issues.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of memory usage violations
        """
        violations = []
        
        # Check for large data structures
        for node in ast.walk(tree):
            if isinstance(node, ast.List):
                # Check for list comprehensions that might create large lists
                if isinstance(node, ast.ListComp):
                    violations.append(Violation(
                rule_id="rule_8",
                rule_number=8,
                        rule_name="Make Things Fast",
                        severity=Severity.INFO,
                        message="List comprehension detected - ensure it doesn't create excessive memory usage",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet="List comprehension",
                        fix_suggestion="Consider generator expressions for large datasets"
                    ))
        
        return violations
    
    def validate_response_time(self, content: str, file_path: str) -> List[Violation]:
        """
        Check for response time issues.
        
        Args:
            content: File content to analyze
            file_path: Path to the file
            
        Returns:
            List of response time violations
        """
        violations = []
        
        # Check for inefficient string operations
        inefficient_patterns = [
            r'\+.*\+.*\+',  # Multiple string concatenations
            r'\.join\s*\(\s*\[\s*str\s*\('  # String conversion in join
        ]
        
        for pattern in inefficient_patterns:
            for match in re.finditer(pattern, content):
                line_number = content[:match.start()].count('\n') + 1
                column_number = match.start() - content.rfind('\n', 0, match.start()) - 1
                
                violations.append(Violation(
                rule_id="rule_67",
                rule_number=67,
                    rule_name="Respect People's Time",
                    severity=Severity.WARNING,
                    message="Inefficient string operation detected",
                    file_path=file_path,
                    line_number=line_number,
                    column_number=column_number,
                    code_snippet=match.group(),
                    fix_suggestion="Use f-strings or .join() for better performance"
                ))
        
        return violations
    
    def validate_algorithm_complexity(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for algorithm complexity issues.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of complexity violations
        """
        violations = []
        
        # Check for O(n²) patterns
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Look for nested operations that could be O(n²)
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        func_name = self._get_function_name(child.func)
                        if func_name in ['list.index', 'list.remove', 'list.insert']:
                            violations.append(Violation(
                rule_id="rule_8",
                rule_number=8,
                                rule_name="Make Things Fast",
                                severity=Severity.WARNING,
                                message=f"O(n²) operation detected: {func_name} in loop",
                                file_path=file_path,
                                line_number=node.lineno,
                                column_number=node.col_offset,
                                code_snippet=func_name,
                                fix_suggestion="Consider using sets or dictionaries for O(1) lookups"
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
    
    def validate_all(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Run all performance validations.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of all performance violations
        """
        violations = []
        
        violations.extend(self.validate_startup_time(tree, file_path))
        violations.extend(self.validate_blocking_operations(tree, file_path))
        violations.extend(self.validate_loop_efficiency(tree, file_path))
        violations.extend(self.validate_memory_usage(tree, file_path))
        violations.extend(self.validate_response_time(content, file_path))
        violations.extend(self.validate_algorithm_complexity(tree, file_path))
        
        return violations
