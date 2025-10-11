"""
Requirements and specification rule validator.

This module implements validation for requirements and specification rules:
- Rule 1: Do Exactly What's Asked
- Rule 2: Only Use Information You're Given
"""

import ast
import re
from typing import List, Dict, Any, Tuple
from ..models import Violation, Severity


class RequirementsValidator:
    """
    Validates requirements and specification rules.
    
    This class focuses on detecting incomplete implementations,
    assumptions, and deviations from specifications.
    """
    
    def __init__(self):
        """Initialize the requirements validator."""
        self.incomplete_patterns = [
            r'#\s*(TODO|FIXME|HACK|XXX|TEMP)',
            r'#\s*(todo|fixme|hack|xxx|temp)',
            r'pass\s*#.*(implement|complete|finish)',
            r'raise\s+NotImplementedError',
            r'raise\s+NotImplemented',
            r'\.\.\.\s*#.*(implement|complete|finish)'
        ]
        
        self.assumption_patterns = [
            r'#\s*(assume|assumption|guess|probably|maybe)',
            r'#\s*(ASSUME|ASSUMPTION|GUESS|PROBABLY|MAYBE)',
            r'#\s*(hardcoded|hard-coded|magic)',
            r'#\s*(HARDCODED|HARD-CODED|MAGIC)'
        ]
        
        self.magic_number_patterns = [
            r'\b\d{2,}\b',  # Numbers with 2+ digits
            r'\b0x[0-9a-fA-F]+\b',  # Hex numbers
            r'\b0b[01]+\b'  # Binary numbers
        ]
        
        self.placeholder_patterns = [
            r'placeholder',
            r'PLACEHOLDER',
            r'temp_',
            r'TEMP_',
            r'dummy',
            r'DUMMY'
        ]
    
    def validate_exact_requirements(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for exact requirements compliance (Rule 1).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of requirements compliance violations
        """
        violations = []
        
        # Check for incomplete implementations
        for pattern in self.incomplete_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_number = content[:match.start()].count('\n') + 1
                column_number = match.start() - content.rfind('\n', 0, match.start()) - 1
                
                violations.append(Violation(
                    rule_number=1,
                    rule_name="Do Exactly What's Asked",
                    severity=Severity.WARNING,
                    message="Incomplete implementation detected - code may not meet exact requirements",
                    file_path=file_path,
                    line_number=line_number,
                    column_number=column_number,
                    code_snippet=match.group(),
                    fix_suggestion="Complete the implementation according to exact specifications"
                ))
        
        # Check for placeholder implementations
        for pattern in self.placeholder_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_number = content[:match.start()].count('\n') + 1
                column_number = match.start() - content.rfind('\n', 0, match.start()) - 1
                
                violations.append(Violation(
                    rule_number=1,
                    rule_name="Do Exactly What's Asked",
                    severity=Severity.WARNING,
                    message="Placeholder implementation detected - may not meet exact requirements",
                    file_path=file_path,
                    line_number=line_number,
                    column_number=column_number,
                    code_snippet=match.group(),
                    fix_suggestion="Replace placeholder with actual implementation"
                ))
        
        # Check for NotImplementedError
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise):
                if isinstance(node.exc, ast.Name):
                    if node.exc.id in ['NotImplementedError', 'NotImplemented']:
                        violations.append(Violation(
                            rule_number=1,
                            rule_name="Do Exactly What's Asked",
                            severity=Severity.ERROR,
                            message="NotImplementedError detected - implementation incomplete",
                            file_path=file_path,
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            code_snippet="NotImplementedError",
                            fix_suggestion="Implement the required functionality"
                        ))
        
        return violations
    
    def validate_given_information_only(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for assumptions and guesswork (Rule 2).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of assumption-related violations
        """
        violations = []
        
        # Check for assumption comments
        for pattern in self.assumption_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_number = content[:match.start()].count('\n') + 1
                column_number = match.start() - content.rfind('\n', 0, match.start()) - 1
                
                violations.append(Violation(
                    rule_number=2,
                    rule_name="Only Use Information You're Given",
                    severity=Severity.WARNING,
                    message="Assumption or guesswork detected - should only use given information",
                    file_path=file_path,
                    line_number=line_number,
                    column_number=column_number,
                    code_snippet=match.group(),
                    fix_suggestion="Remove assumptions and use only provided information"
                ))
        
        # Check for magic numbers without constants
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    # Check if it's a magic number (not 0, 1, -1)
                    if node.value not in [0, 1, -1] and abs(node.value) > 1:
                        # Check if it's defined as a constant nearby
                        if not self._is_defined_as_constant(node, content):
                            violations.append(Violation(
                                rule_number=2,
                                rule_name="Only Use Information You're Given",
                                severity=Severity.WARNING,
                                message=f"Magic number detected: {node.value} - should be defined as a constant",
                                file_path=file_path,
                                line_number=node.lineno,
                                column_number=node.col_offset,
                                code_snippet=str(node.value),
                                fix_suggestion="Define magic numbers as named constants"
                            ))
        
        # Check for hardcoded assumptions in function parameters
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for arg in node.args.args:
                    # Check for default values that might be assumptions
                    if arg.annotation is None and not self._has_docstring(node):
                        violations.append(Violation(
                            rule_number=2,
                            rule_name="Only Use Information You're Given",
                            severity=Severity.INFO,
                            message=f"Function parameter '{arg.arg}' lacks type annotation - may lead to assumptions",
                            file_path=file_path,
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            code_snippet=arg.arg,
                            fix_suggestion="Add type annotations to clarify parameter expectations"
                        ))
        
        return violations
    
    def _is_defined_as_constant(self, node: ast.Constant, content: str) -> bool:
        """Check if a number is defined as a constant nearby."""
        # Look for constant definitions in the same file
        constant_patterns = [
            rf'{node.value}\s*=\s*{node.value}',
            rf'CONSTANT.*{node.value}',
            rf'constant.*{node.value}'
        ]
        
        for pattern in constant_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    def _has_docstring(self, func_node: ast.FunctionDef) -> bool:
        """Check if function has a docstring."""
        return ast.get_docstring(func_node) is not None
    
    def validate_all(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Run all requirements validations.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of all requirements violations
        """
        violations = []
        
        violations.extend(self.validate_exact_requirements(tree, content, file_path))
        violations.extend(self.validate_given_information_only(tree, content, file_path))
        
        return violations
