"""
Code quality rule validator.

This module implements validation for code quality rules:
- Rule 15: Write Good Instructions
- Rule 18: Make Things Repeatable
- Rule 68: Write Clean, Readable Code
"""

import ast
import re
from typing import List, Dict, Any, Tuple
from ..models import Violation, Severity


class QualityValidator:
    """
    Validates code quality rules.
    
    This class focuses on detecting code quality issues like
    poor documentation, non-reproducible code, and readability problems.
    """
    
    def __init__(self):
        """Initialize the quality validator."""
        self.function_length_threshold = 50
        self.class_length_threshold = 200
        self.parameter_threshold = 5
        self.complexity_threshold = 10
        
        self.naming_patterns = {
            'function': r'^[a-z_][a-z0-9_]*$',
            'class': r'^[A-Z][a-zA-Z0-9]*$',
            'constant': r'^[A-Z_][A-Z0-9_]*$',
            'variable': r'^[a-z_][a-z0-9_]*$'
        }
        
        self.documentation_keywords = ['"""', "'''", '# TODO', '# FIXME', '# NOTE', '# HACK']
    
    def validate_function_length(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for function length violations.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of function length violations
        """
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                line_count = self._count_function_lines(node)
                
                if line_count > self.function_length_threshold:
                    violations.append(Violation(
                rule_id="rule_68",
                rule_number=68,
                        rule_name="Write Clean, Readable Code",
                        severity=Severity.WARNING,
                        message=f"Function exceeds recommended length ({line_count} > {self.function_length_threshold} lines)",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=node.name,
                        fix_suggestion="Break function into smaller, focused functions"
                    ))
        
        return violations
    
    def validate_class_length(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for class length violations.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of class length violations
        """
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                line_count = self._count_class_lines(node)
                
                if line_count > self.class_length_threshold:
                    violations.append(Violation(
                rule_id="rule_68",
                rule_number=68,
                        rule_name="Write Clean, Readable Code",
                        severity=Severity.WARNING,
                        message=f"Class exceeds recommended length ({line_count} > {self.class_length_threshold} lines)",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=node.name,
                        fix_suggestion="Consider breaking class into smaller, focused classes"
                    ))
        
        return violations
    
    def validate_parameter_count(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for excessive parameter count.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of parameter count violations
        """
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                parameter_count = len(node.args.args)
                
                if parameter_count > self.parameter_threshold:
                    violations.append(Violation(
                rule_id="rule_68",
                rule_number=68,
                        rule_name="Write Clean, Readable Code",
                        severity=Severity.WARNING,
                        message=f"Function has too many parameters ({parameter_count} > {self.parameter_threshold})",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=node.name,
                        fix_suggestion="Consider using a configuration object or data class for parameters"
                    ))
        
        return violations
    
    def validate_cyclomatic_complexity(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for cyclomatic complexity violations.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of complexity violations
        """
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)
                
                if complexity > self.complexity_threshold:
                    violations.append(Violation(
                rule_id="rule_68",
                rule_number=68,
                        rule_name="Write Clean, Readable Code",
                        severity=Severity.WARNING,
                        message=f"Function has high cyclomatic complexity ({complexity} > {self.complexity_threshold})",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=node.name,
                        fix_suggestion="Simplify function logic or break into smaller functions"
                    ))
        
        return violations
    
    def validate_naming_conventions(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for naming convention violations.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of naming convention violations
        """
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(self.naming_patterns['function'], node.name):
                    violations.append(Violation(
                rule_id="rule_68",
                rule_number=68,
                        rule_name="Write Clean, Readable Code",
                        severity=Severity.WARNING,
                        message=f"Function name doesn't follow convention: {node.name}",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=node.name,
                        fix_suggestion="Use snake_case for function names"
                    ))
            
            elif isinstance(node, ast.ClassDef):
                if not re.match(self.naming_patterns['class'], node.name):
                    violations.append(Violation(
                rule_id="rule_68",
                rule_number=68,
                        rule_name="Write Clean, Readable Code",
                        severity=Severity.WARNING,
                        message=f"Class name doesn't follow convention: {node.name}",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=node.name,
                        fix_suggestion="Use PascalCase for class names"
                    ))
            
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if not re.match(self.naming_patterns['variable'], target.id):
                            violations.append(Violation(
                rule_id="rule_68",
                rule_number=68,
                                rule_name="Write Clean, Readable Code",
                                severity=Severity.WARNING,
                                message=f"Variable name doesn't follow convention: {target.id}",
                                file_path=file_path,
                                line_number=node.lineno,
                                column_number=node.col_offset,
                                code_snippet=target.id,
                                fix_suggestion="Use snake_case for variable names"
                            ))
        
        return violations
    
    def validate_documentation(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for documentation completeness.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of documentation violations
        """
        violations = []
        
        # Check for module docstring
        if not ast.get_docstring(tree):
            violations.append(Violation(
                rule_id="rule_15",
                rule_number=15,
                rule_name="Write Good Instructions",
                severity=Severity.INFO,
                message="Module missing docstring",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Missing module docstring",
                fix_suggestion="Add module docstring explaining the purpose and usage"
            ))
        
        # Check for function docstrings
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not ast.get_docstring(node):
                    violations.append(Violation(
                rule_id="rule_15",
                rule_number=15,
                        rule_name="Write Good Instructions",
                        severity=Severity.WARNING,
                        message=f"Function missing docstring: {node.name}",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=node.name,
                        fix_suggestion="Add docstring explaining function purpose and parameters"
                    ))
        
        # Check for class docstrings
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    violations.append(Violation(
                rule_id="rule_15",
                rule_number=15,
                        rule_name="Write Good Instructions",
                        severity=Severity.WARNING,
                        message=f"Class missing docstring: {node.name}",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=node.name,
                        fix_suggestion="Add docstring explaining class purpose and usage"
                    ))
        
        return violations
    
    def validate_reproducibility(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for code reproducibility issues.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of reproducibility violations
        """
        violations = []
        
        # Check for hardcoded values that should be configurable
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.lower()
                        
                        # Check for configuration-related variables
                        if any(keyword in var_name for keyword in 
                              ['url', 'host', 'port', 'timeout', 'limit', 'threshold']):
                            if isinstance(node.value, (ast.Str, ast.Constant)):
                                value = node.value.s if hasattr(node.value, 's') else str(node.value.value)
                                violations.append(Violation(
                rule_id="rule_18",
                rule_number=18,
                                    rule_name="Make Things Repeatable",
                                    severity=Severity.WARNING,
                                    message=f"Hardcoded configuration value: {var_name} = {value}",
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    column_number=node.col_offset,
                                    code_snippet=f"{var_name} = {value}",
                                    fix_suggestion="Use configuration files or environment variables"
                                ))
        
        return violations
    
    def validate_code_organization(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for code organization issues.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of organization violations
        """
        violations = []
        
        # Check for proper import organization
        imports = []
        other_statements = []
        
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(node)
            else:
                other_statements.append(node)
        
        # Check if imports are at the top
        if other_statements and imports:
            first_other_line = other_statements[0].lineno
            last_import_line = imports[-1].lineno
            
            if first_other_line < last_import_line:
                violations.append(Violation(
                rule_id="rule_68",
                rule_number=68,
                    rule_name="Write Clean, Readable Code",
                    severity=Severity.INFO,
                    message="Imports should be at the top of the file",
                    file_path=file_path,
                    line_number=first_other_line,
                    column_number=0,
                    code_snippet="Import organization",
                    fix_suggestion="Move all imports to the top of the file"
                ))
        
        return violations
    
    def _count_function_lines(self, func_node: ast.FunctionDef) -> int:
        """Count lines in a function."""
        if hasattr(func_node, 'end_lineno') and func_node.end_lineno:
            return func_node.end_lineno - func_node.lineno + 1
        return 1
    
    def _count_class_lines(self, class_node: ast.ClassDef) -> int:
        """Count lines in a class."""
        if hasattr(class_node, 'end_lineno') and class_node.end_lineno:
            return class_node.end_lineno - class_node.lineno + 1
        return 1
    
    def _calculate_cyclomatic_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def validate_all(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Run all code quality validations.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of all code quality violations
        """
        violations = []
        
        violations.extend(self.validate_function_length(tree, file_path))
        violations.extend(self.validate_class_length(tree, file_path))
        violations.extend(self.validate_parameter_count(tree, file_path))
        violations.extend(self.validate_cyclomatic_complexity(tree, file_path))
        violations.extend(self.validate_naming_conventions(tree, file_path))
        violations.extend(self.validate_documentation(tree, file_path))
        violations.extend(self.validate_reproducibility(tree, file_path))
        violations.extend(self.validate_code_organization(tree, file_path))
        
        return violations
