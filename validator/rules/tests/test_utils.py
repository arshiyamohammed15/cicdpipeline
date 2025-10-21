"""
Utility functions for validator tests.

Provides helpers for AST generation, violation comparison, and test data creation.
"""

import ast
from typing import List, Dict, Any
from validator.models import Violation, Severity


def create_ast(code: str) -> ast.AST:
    """
    Create AST from code string with error handling.
    
    Args:
        code: Python code as string
        
    Returns:
        AST tree or None if parsing fails
    """
    try:
        return ast.parse(code)
    except SyntaxError:
        return None


def find_violations_by_rule(violations: List[Violation], rule_id: str) -> List[Violation]:
    """
    Filter violations by rule ID.
    
    Args:
        violations: List of violations
        rule_id: Rule ID to filter by
        
    Returns:
        List of matching violations
    """
    return [v for v in violations if v.rule_id == rule_id]


def find_violations_by_severity(violations: List[Violation], 
                                severity: Severity) -> List[Violation]:
    """
    Filter violations by severity.
    
    Args:
        violations: List of violations
        severity: Severity level to filter by
        
    Returns:
        List of matching violations
    """
    return [v for v in violations if v.severity == severity]


def count_violations_by_rule(violations: List[Violation]) -> Dict[str, int]:
    """
    Count violations grouped by rule ID.
    
    Args:
        violations: List of violations
        
    Returns:
        Dictionary mapping rule_id to count
    """
    counts = {}
    for v in violations:
        counts[v.rule_id] = counts.get(v.rule_id, 0) + 1
    return counts


def has_violation_with_message(violations: List[Violation], 
                               message_fragment: str) -> bool:
    """
    Check if any violation contains a message fragment.
    
    Args:
        violations: List of violations
        message_fragment: Text to search for in messages
        
    Returns:
        True if any violation contains the fragment
    """
    return any(message_fragment.lower() in v.message.lower() for v in violations)


def create_test_file_content(imports: List[str] = None,
                            functions: List[str] = None,
                            classes: List[str] = None) -> str:
    """
    Create test file content with specified components.
    
    Args:
        imports: List of import statements
        functions: List of function definitions
        classes: List of class definitions
        
    Returns:
        Complete file content as string
    """
    parts = []
    
    if imports:
        parts.append('\n'.join(imports))
        parts.append('')
    
    if classes:
        parts.extend(classes)
        parts.append('')
    
    if functions:
        parts.extend(functions)
    
    return '\n'.join(parts)


def validate_rule_id_format(rule_id: str) -> bool:
    """
    Validate rule ID format (should be RXXX or rule_XXX).
    
    Args:
        rule_id: Rule ID to validate
        
    Returns:
        True if valid format
    """
    import re
    return bool(re.match(r'^(R\d{3,4}|rule_\d{3})$', rule_id))


def get_line_number(content: str, search_text: str) -> int:
    """
    Get line number where text appears in content.
    
    Args:
        content: Full content
        search_text: Text to search for
        
    Returns:
        Line number (1-indexed) or -1 if not found
    """
    try:
        pos = content.index(search_text)
        return content[:pos].count('\n') + 1
    except ValueError:
        return -1


class ViolationAsserter:
    """Helper class for making assertions about violations."""
    
    def __init__(self, violations: List[Violation]):
        self.violations = violations
    
    def has_rule(self, rule_id: str) -> bool:
        """Check if rule_id exists in violations."""
        return any(v.rule_id == rule_id for v in self.violations)
    
    def has_severity(self, severity: Severity) -> bool:
        """Check if severity exists in violations."""
        return any(v.severity == severity for v in self.violations)
    
    def count(self) -> int:
        """Get total violation count."""
        return len(self.violations)
    
    def count_by_rule(self, rule_id: str) -> int:
        """Get count for specific rule."""
        return len(find_violations_by_rule(self.violations, rule_id))
    
    def get_first(self, rule_id: str = None) -> Violation:
        """Get first violation, optionally filtered by rule_id."""
        if rule_id:
            filtered = find_violations_by_rule(self.violations, rule_id)
            return filtered[0] if filtered else None
        return self.violations[0] if self.violations else None

