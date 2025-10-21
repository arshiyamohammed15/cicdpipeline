#!/usr/bin/env python3
"""
Unified rule processor for optimized validation.

This module provides a single-pass AST traversal with all rules processed
simultaneously for maximum performance.
"""

import ast
import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

from .models import Violation, Severity


class RuleType(Enum):
    """Types of rule patterns."""
    REGEX = "regex"
    KEYWORD = "keyword"
    AST_PATTERN = "ast_pattern"
    FUNCTION_CALL = "function_call"
    IMPORT_PATTERN = "import_pattern"


@dataclass
class RulePattern:
    """Represents a rule pattern for validation."""
    rule_id: str
    rule_name: str
    rule_number: int
    category: str
    severity: Severity
    pattern_type: RuleType
    pattern: Any  # regex string, keyword list, or AST pattern
    message: str
    fix_suggestion: str
    enabled: bool = True


class UnifiedRuleProcessor:
    """
    Unified rule processor that processes all rules in a single AST pass.
    
    This processor compiles all rule patterns and processes them efficiently
    during a single traversal of the AST.
    """
    
    def __init__(self, config_manager):
        """
        Initialize the unified rule processor.
        
        Args:
            config_manager: Enhanced configuration manager
        """
        self.config_manager = config_manager
        self.compiled_patterns: List[RulePattern] = []
        self._compiled_regexes: Dict[str, re.Pattern] = {}
        self._initialize_patterns()
    
    def _initialize_patterns(self):
        """Initialize and compile all rule patterns."""
        categories = self.config_manager.get_all_categories()
        
        for category in categories:
            try:
                rule_config = self.config_manager.get_rule_config(category)
                pattern_config = self.config_manager.get_pattern_config(category)
                
                rules = rule_config.get("rules", [])
                patterns = pattern_config.get("patterns", {})
                
                for pattern_name, pattern_data in patterns.items():
                    for rule_number in rules:
                        rule_pattern = self._create_rule_pattern(
                            category, rule_number, pattern_name, pattern_data
                        )
                        if rule_pattern:
                            self.compiled_patterns.append(rule_pattern)
            
            except Exception as e:
                print(f"Error initializing patterns for category {category}: {e}")
    
    def _create_rule_pattern(self, category: str, rule_number: int, 
                           pattern_name: str, pattern_data: Dict[str, Any]) -> Optional[RulePattern]:
        """Create a rule pattern from configuration data."""
        try:
            rule_id = f"rule_{rule_number:03d}"
            rule_name = pattern_data.get("message", f"Rule {rule_number}")
            severity = Severity(pattern_data.get("severity", "warning"))
            
            # Determine pattern type and compile pattern
            if "regex" in pattern_data:
                pattern_type = RuleType.REGEX
                pattern = pattern_data["regex"]
                # Compile regex for performance
                if pattern not in self._compiled_regexes:
                    self._compiled_regexes[pattern] = re.compile(pattern)
            
            elif "keywords" in pattern_data:
                pattern_type = RuleType.KEYWORD
                pattern = pattern_data["keywords"]
            
            elif "ast_pattern" in pattern_data:
                pattern_type = RuleType.AST_PATTERN
                pattern = pattern_data["ast_pattern"]
            
            else:
                return None
            
            return RulePattern(
                rule_id=rule_id,
                rule_name=rule_name,
                rule_number=rule_number,
                category=category,
                severity=severity,
                pattern_type=pattern_type,
                pattern=pattern,
                message=pattern_data.get("message", "Rule violation"),
                fix_suggestion=pattern_data.get("fix_suggestion", "Fix the violation")
            )
        
        except Exception as e:
            print(f"Error creating rule pattern for {category}.{pattern_name}: {e}")
            return None
    
    def process_rules(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Process all rules in a single AST pass.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations found
        """
        violations = []
        
        # Process content-based patterns first (regex, keywords)
        violations.extend(self._process_content_patterns(content, file_path))
        
        # Process AST-based patterns
        violations.extend(self._process_ast_patterns(tree, content, file_path))
        
        return violations
    
    def _process_content_patterns(self, content: str, file_path: str) -> List[Violation]:
        """Process regex and keyword patterns on file content."""
        violations = []
        
        for rule_pattern in self.compiled_patterns:
            if not rule_pattern.enabled:
                continue
            
            if rule_pattern.pattern_type == RuleType.REGEX:
                violations.extend(self._process_regex_pattern(rule_pattern, content, file_path))
            
            elif rule_pattern.pattern_type == RuleType.KEYWORD:
                violations.extend(self._process_keyword_pattern(rule_pattern, content, file_path))
        
        return violations
    
    def _process_regex_pattern(self, rule_pattern: RulePattern, content: str, 
                              file_path: str) -> List[Violation]:
        """Process a regex pattern."""
        violations = []
        
        try:
            regex = self._compiled_regexes.get(rule_pattern.pattern)
            if not regex:
                return violations
            
            for match in regex.finditer(content):
                line_number = content[:match.start()].count('\n') + 1
                column_number = match.start() - content.rfind('\n', 0, match.start()) - 1
                
                violation = Violation(
                    rule_id=rule_pattern.rule_id,
                    rule_name=rule_pattern.rule_name,
                    rule_number=rule_pattern.rule_number,
                    severity=rule_pattern.severity,
                    message=rule_pattern.message,
                    file_path=file_path,
                    line_number=line_number,
                    column_number=column_number,
                    code_snippet=match.group(),
                    fix_suggestion=rule_pattern.fix_suggestion,
                    category=rule_pattern.category
                )
                violations.append(violation)
        
        except Exception as e:
            print(f"Error processing regex pattern {rule_pattern.rule_id}: {e}")
        
        return violations
    
    def _process_keyword_pattern(self, rule_pattern: RulePattern, content: str, 
                                file_path: str) -> List[Violation]:
        """Process a keyword pattern."""
        violations = []
        
        try:
            keywords = rule_pattern.pattern
            if not isinstance(keywords, list):
                return violations
            
            for keyword in keywords:
                if keyword in content:
                    # Find first occurrence
                    pos = content.find(keyword)
                    line_number = content[:pos].count('\n') + 1
                    column_number = pos - content.rfind('\n', 0, pos) - 1
                    
                    violation = Violation(
                        rule_id=rule_pattern.rule_id,
                        rule_name=rule_pattern.rule_name,
                        rule_number=rule_pattern.rule_number,
                        severity=rule_pattern.severity,
                        message=rule_pattern.message,
                        file_path=file_path,
                        line_number=line_number,
                        column_number=column_number,
                        code_snippet=keyword,
                        fix_suggestion=rule_pattern.fix_suggestion,
                        category=rule_pattern.category
                    )
                    violations.append(violation)
                    break  # Only report first occurrence
        
        except Exception as e:
            print(f"Error processing keyword pattern {rule_pattern.rule_id}: {e}")
        
        return violations
    
    def _process_ast_patterns(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """Process AST-based patterns."""
        violations = []
        
        # Single pass through AST
        for node in ast.walk(tree):
            for rule_pattern in self.compiled_patterns:
                if not rule_pattern.enabled or rule_pattern.pattern_type != RuleType.AST_PATTERN:
                    continue
                
                try:
                    node_violations = self._check_ast_node(rule_pattern, node, content, file_path)
                    violations.extend(node_violations)
                except Exception as e:
                    print(f"Error checking AST node for rule {rule_pattern.rule_id}: {e}")
        
        return violations
    
    def _check_ast_node(self, rule_pattern: RulePattern, node: ast.AST, 
                       content: str, file_path: str) -> List[Violation]:
        """Check a specific AST node against a rule pattern."""
        violations = []
        
        try:
            pattern = rule_pattern.pattern
            
            # Function length check
            if pattern == "long_functions" and isinstance(node, ast.FunctionDef):
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    line_count = node.end_lineno - node.lineno + 1
                    if line_count > 50:  # Threshold for long functions
                        violation = Violation(
                            rule_id=rule_pattern.rule_id,
                            rule_name=rule_pattern.rule_name,
                            rule_number=rule_pattern.rule_number,
                            severity=rule_pattern.severity,
                            message=f"Function '{node.name}' is too long ({line_count} lines)",
                            file_path=file_path,
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            code_snippet=node.name,
                            fix_suggestion="Break function into smaller, focused functions",
                            category=rule_pattern.category
                        )
                        violations.append(violation)
            
            # Missing docstring check
            elif pattern == "functions_without_docstrings" and isinstance(node, ast.FunctionDef):
                if not ast.get_docstring(node):
                    violation = Violation(
                        rule_id=rule_pattern.rule_id,
                        rule_name=rule_pattern.rule_name,
                        rule_number=rule_pattern.rule_number,
                        severity=rule_pattern.severity,
                        message=f"Function '{node.name}' missing docstring",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=node.name,
                        fix_suggestion="Add docstring explaining function purpose and parameters",
                        category=rule_pattern.category
                    )
                    violations.append(violation)
            
            # Nested loops check
            elif pattern == "nested_for_loops" and isinstance(node, (ast.For, ast.While)):
                if self._has_nested_loops(node):
                    violation = Violation(
                        rule_id=rule_pattern.rule_id,
                        rule_name=rule_pattern.rule_name,
                        rule_number=rule_pattern.rule_number,
                        severity=rule_pattern.severity,
                        message="Nested loops detected - consider optimization",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=type(node).__name__,
                        fix_suggestion="Consider optimization for O(n²) complexity",
                        category=rule_pattern.category
                    )
                    violations.append(violation)
            
            # Risky operations check
            elif pattern == "risky_operations_without_try_catch" and isinstance(node, ast.Call):
                if self._is_risky_operation(node) and not self._has_try_catch(node):
                    violation = Violation(
                        rule_id=rule_pattern.rule_id,
                        rule_name=rule_pattern.rule_name,
                        rule_number=rule_pattern.rule_number,
                        severity=rule_pattern.severity,
                        message="Risky operation without error handling",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=self._get_function_name(node.func),
                        fix_suggestion="Add try-catch blocks around risky operations",
                        category=rule_pattern.category
                    )
                    violations.append(violation)
        
        except Exception as e:
            print(f"Error in AST node check: {e}")
        
        return violations
    
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
        # For now, we'll assume no try-catch for simplicity
        return False
    
    def _get_function_name(self, func_node: ast.AST) -> str:
        """Extract function name from AST node."""
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            return f"{self._get_function_name(func_node.value)}.{func_node.attr}"
        else:
            return str(func_node)
    
    def enable_rule(self, rule_id: str):
        """Enable a specific rule."""
        for pattern in self.compiled_patterns:
            if pattern.rule_id == rule_id:
                pattern.enabled = True
                break
    
    def disable_rule(self, rule_id: str):
        """Disable a specific rule."""
        for pattern in self.compiled_patterns:
            if pattern.rule_id == rule_id:
                pattern.enabled = False
                break
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded rules."""
        stats = {
            "total_patterns": len(self.compiled_patterns),
            "enabled_patterns": sum(1 for p in self.compiled_patterns if p.enabled),
            "disabled_patterns": sum(1 for p in self.compiled_patterns if not p.enabled),
            "patterns_by_type": {},
            "patterns_by_category": {},
            "patterns_by_severity": {}
        }
        
        for pattern in self.compiled_patterns:
            # Count by type
            pattern_type = pattern.pattern_type.value
            stats["patterns_by_type"][pattern_type] = stats["patterns_by_type"].get(pattern_type, 0) + 1
            
            # Count by category
            category = pattern.category
            stats["patterns_by_category"][category] = stats["patterns_by_category"].get(category, 0) + 1
            
            # Count by severity
            severity = pattern.severity.value
            stats["patterns_by_severity"][severity] = stats["patterns_by_severity"].get(severity, 0) + 1
        
        return stats
