#!/usr/bin/env python3
"""
Base validator class for common validation patterns.

This module provides a base class that all rule validators can inherit from,
reducing code duplication and ensuring consistent validation patterns.
"""

import ast
import re
from typing import List, Dict, Any, Optional, Set
from abc import ABC, abstractmethod

from .models import Violation, Severity


class BaseRuleValidator(ABC):
    """
    Base class for all rule validators.
    
    This class provides common functionality and patterns that all
    rule validators can use, reducing code duplication.
    """
    
    def __init__(self, rule_config: Dict[str, Any]):
        """
        Initialize the base validator.
        
        Args:
            rule_config: Configuration for the rules this validator handles
        """
        self.rule_config = rule_config
        self.rules = rule_config.get("rules", [])
        self.category = rule_config.get("category", "unknown")
        self.priority = rule_config.get("priority", "unknown")
        self.description = rule_config.get("description", "")
        
        # Compile patterns for performance
        self._compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, Any]:
        """Compile patterns for better performance."""
        compiled = {}
        
        # This would be overridden by subclasses with specific patterns
        return compiled
    
    @abstractmethod
    def validate_all(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Validate all rules for this category.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations found
        """
        pass
    
    def create_violation(self, rule_number: int, rule_name: str, severity: Severity,
                        message: str, file_path: str, line_number: int,
                        column_number: int, code_snippet: str,
                        fix_suggestion: str = None) -> Violation:
        """
        Create a violation with consistent formatting.
        
        Args:
            rule_number: Rule number
            rule_name: Rule name
            severity: Violation severity
            message: Violation message
            file_path: File path
            line_number: Line number
            column_number: Column number
            code_snippet: Code snippet
            fix_suggestion: Fix suggestion
            
        Returns:
            Violation object
        """
        return Violation(
            rule_id=f"rule_{rule_number:03d}",
            rule_name=rule_name,
            rule_number=rule_number,
            severity=severity,
            message=message,
            file_path=file_path,
            line_number=line_number,
            column_number=column_number,
            code_snippet=code_snippet,
            fix_suggestion=fix_suggestion or "Review and fix the violation",
            category=self.category
        )
    
    def find_regex_violations(self, content: str, file_path: str, 
                             pattern_name: str, pattern_data: Dict[str, Any]) -> List[Violation]:
        """
        Find violations using regex patterns.
        
        Args:
            content: File content
            file_path: File path
            pattern_name: Name of the pattern
            pattern_data: Pattern configuration
            
        Returns:
            List of violations
        """
        violations = []
        
        if "regex" not in pattern_data:
            return violations
        
        try:
            regex = re.compile(pattern_data["regex"])
            rule_number = pattern_data.get("rule_number", self.rules[0] if self.rules else 0)
            
            for match in regex.finditer(content):
                line_number = content[:match.start()].count('\n') + 1
                column_number = match.start() - content.rfind('\n', 0, match.start()) - 1
                
                violation = self.create_violation(
                    rule_number=rule_number,
                    rule_name=pattern_data.get("message", f"{pattern_name} violation"),
                    severity=Severity(pattern_data.get("severity", "warning")),
                    message=pattern_data.get("message", f"{pattern_name} violation detected"),
                    file_path=file_path,
                    line_number=line_number,
                    column_number=column_number,
                    code_snippet=match.group(),
                    fix_suggestion=pattern_data.get("fix_suggestion", f"Fix {pattern_name} violation")
                )
                violations.append(violation)
        
        except Exception as e:
            print(f"Error processing regex pattern {pattern_name}: {e}")
        
        return violations
    
    def find_keyword_violations(self, content: str, file_path: str,
                               pattern_name: str, pattern_data: Dict[str, Any]) -> List[Violation]:
        """
        Find violations using keyword patterns.
        
        Args:
            content: File content
            file_path: File path
            pattern_name: Name of the pattern
            pattern_data: Pattern configuration
            
        Returns:
            List of violations
        """
        violations = []
        
        if "keywords" not in pattern_data:
            return violations
        
        try:
            keywords = pattern_data["keywords"]
            rule_number = pattern_data.get("rule_number", self.rules[0] if self.rules else 0)
            
            for keyword in keywords:
                if keyword in content:
                    # Find first occurrence
                    pos = content.find(keyword)
                    line_number = content[:pos].count('\n') + 1
                    column_number = pos - content.rfind('\n', 0, pos) - 1
                    
                    violation = self.create_violation(
                        rule_number=rule_number,
                        rule_name=pattern_data.get("message", f"{pattern_name} violation"),
                        severity=Severity(pattern_data.get("severity", "warning")),
                        message=pattern_data.get("message", f"Keyword '{keyword}' detected"),
                        file_path=file_path,
                        line_number=line_number,
                        column_number=column_number,
                        code_snippet=keyword,
                        fix_suggestion=pattern_data.get("fix_suggestion", f"Review usage of '{keyword}'")
                    )
                    violations.append(violation)
                    break  # Only report first occurrence
        
        except Exception as e:
            print(f"Error processing keyword pattern {pattern_name}: {e}")
        
        return violations
    
    def find_ast_violations(self, tree: ast.AST, content: str, file_path: str,
                           pattern_name: str, pattern_data: Dict[str, Any]) -> List[Violation]:
        """
        Find violations using AST patterns.
        
        Args:
            tree: AST tree
            content: File content
            file_path: File path
            pattern_name: Name of the pattern
            pattern_data: Pattern configuration
            
        Returns:
            List of violations
        """
        violations = []
        
        if "ast_pattern" not in pattern_data:
            return violations
        
        try:
            ast_pattern = pattern_data["ast_pattern"]
            rule_number = pattern_data.get("rule_number", self.rules[0] if self.rules else 0)
            
            for node in ast.walk(tree):
                if self._matches_ast_pattern(node, ast_pattern):
                    violation = self.create_violation(
                        rule_number=rule_number,
                        rule_name=pattern_data.get("message", f"{pattern_name} violation"),
                        severity=Severity(pattern_data.get("severity", "warning")),
                        message=pattern_data.get("message", f"{pattern_name} violation detected"),
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=self._get_node_snippet(node),
                        fix_suggestion=pattern_data.get("fix_suggestion", f"Fix {pattern_name} violation")
                    )
                    violations.append(violation)
        
        except Exception as e:
            print(f"Error processing AST pattern {pattern_name}: {e}")
        
        return violations
    
    def _matches_ast_pattern(self, node: ast.AST, pattern: str) -> bool:
        """
        Check if an AST node matches a pattern.
        
        Args:
            node: AST node
            pattern: Pattern to match
            
        Returns:
            True if node matches pattern
        """
        if pattern == "long_functions" and isinstance(node, ast.FunctionDef):
            if hasattr(node, 'end_lineno') and node.end_lineno:
                line_count = node.end_lineno - node.lineno + 1
                return line_count > 50  # Threshold for long functions
            return False
        
        elif pattern == "functions_without_docstrings" and isinstance(node, ast.FunctionDef):
            return not ast.get_docstring(node)
        
        elif pattern == "nested_for_loops" and isinstance(node, (ast.For, ast.While)):
            return self._has_nested_loops(node)
        
        elif pattern == "risky_operations_without_try_catch" and isinstance(node, ast.Call):
            return self._is_risky_operation(node) and not self._has_try_catch(node)
        
        return False
    
    def _has_nested_loops(self, node: ast.AST) -> bool:
        """Check if a node contains nested loops."""
        for child in ast.walk(node):
            if child != node and isinstance(child, (ast.For, ast.While)):
                return True
        return False
    
    def _is_risky_operation(self, node: ast.Call) -> bool:
        """Check if a function call is a risky operation."""
        func_name = self._get_function_name(node.func).lower()
        risky_functions = [
            'open', 'file', 'read', 'write', 'requests', 'urllib', 
            'socket', 'http', 'os.system', 'subprocess', 'exec', 'eval'
        ]
        return any(risky in func_name for risky in risky_functions)
    
    def _has_try_catch(self, node: ast.AST) -> bool:
        """Check if a node is within a try-catch block."""
        # This is a simplified check - in practice, you'd need to track the AST context
        return False
    
    def _get_function_name(self, func_node: ast.AST) -> str:
        """Extract function name from AST node."""
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            return f"{self._get_function_name(func_node.value)}.{func_node.attr}"
        else:
            return str(func_node)
    
    def _get_node_snippet(self, node: ast.AST) -> str:
        """Get a code snippet for an AST node."""
        if isinstance(node, ast.FunctionDef):
            return node.name
        elif isinstance(node, ast.ClassDef):
            return node.name
        elif isinstance(node, ast.Call):
            return self._get_function_name(node.func)
        else:
            return type(node).__name__
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get statistics about this validator's rules."""
        return {
            "category": self.category,
            "priority": self.priority,
            "description": self.description,
            "rule_count": len(self.rules),
            "rules": self.rules,
            "pattern_count": len(self._compiled_patterns)
        }
