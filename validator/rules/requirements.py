#!/usr/bin/env python3
"""
Requirements Rules Validator

Validates code against requirements principles:
- Rule 1: Do exactly what's asked
- Rule 2: Only use information you're given
"""

import ast
import re
from typing import List
from ..models import Violation, Severity
from ..base_validator import BaseRuleValidator


class RequirementsValidator(BaseRuleValidator):
    """Validator for requirements rules."""
    
    def __init__(self, rule_config: dict = None):
        if rule_config is None:
            rule_config = {
                "category": "requirements",
                "priority": "critical",
                "description": "Requirements and specifications",
                "rules": [1, 2]
            }
        super().__init__(rule_config)
    
    def validate_do_exactly_what_asked(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for incomplete implementations (Rule 1).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations
        """
        violations = []
        
        # Check for TODO comments
        todo_pattern = r'#\s*TODO|#\s*FIXME|#\s*XXX'
        for match in re.finditer(todo_pattern, content, re.IGNORECASE):
            line_number = content[:match.start()].count('\n') + 1
            violations.append(self.create_violation(
                rule_number=1,
                rule_name="Do exactly what's asked",
                severity=Severity.WARNING,
                message="Incomplete implementation detected - TODO/FIXME comment found",
                file_path=file_path,
                line_number=line_number,
                column_number=0,
                code_snippet=match.group(),
                fix_suggestion="Complete the implementation as requested"
            ))
        
        # Check for incomplete functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function only has pass
                if (len(node.body) == 1 and 
                    isinstance(node.body[0], ast.Pass)):
                    violations.append(self.create_violation(
                        rule_number=1,
                        rule_name="Do exactly what's asked",
                        severity=Severity.WARNING,
                        message=f"Function '{node.name}' is incomplete (only contains 'pass')",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=node.name,
                        fix_suggestion="Implement the function as requested"
                    ))
        
        return violations
    
    def validate_only_use_given_information(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for assumptions and magic values (Rule 2).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations
        """
        violations = []
        
        # Check for magic numbers
        magic_number_pattern = r'=\s*\d{3,}'  # Numbers with 3+ digits
        for match in re.finditer(magic_number_pattern, content):
            line_number = content[:match.start()].count('\n') + 1
            violations.append(self.create_violation(
                rule_number=2,
                rule_name="Only use information you're given",
                severity=Severity.WARNING,
                message="Magic number detected - use named constants",
                file_path=file_path,
                line_number=line_number,
                column_number=0,
                code_snippet=match.group(),
                fix_suggestion="Replace magic numbers with named constants"
            ))
        
        # Check for assumptions in comments
        assumption_patterns = [
            r'assume|assumption|probably|likely|might|could',
            r'guess|estimate|approximate'
        ]
        
        for pattern in assumption_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_number = content[:match.start()].count('\n') + 1
                violations.append(self.create_violation(
                    rule_number=2,
                    rule_name="Only use information you're given",
                    severity=Severity.INFO,
                    message="Assumption detected in code or comments",
                    file_path=file_path,
                    line_number=line_number,
                    column_number=0,
                    code_snippet=match.group(),
                    fix_suggestion="Use only information explicitly provided"
                ))
        
        return violations
    
    def validate_all(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Validate all requirements rules.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of all violations found
        """
        violations = []
        
        violations.extend(self.validate_do_exactly_what_asked(tree, content, file_path))
        violations.extend(self.validate_only_use_given_information(tree, content, file_path))
        
        return violations