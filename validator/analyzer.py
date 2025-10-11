"""
Code analyzer for AST-based code analysis.

This module provides advanced code analysis capabilities using Python's
Abstract Syntax Tree (AST) to detect complex patterns and violations
of the ZEROUI 2.0 Constitution rules.
"""

import ast
import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ComplexityLevel(Enum):
    """Code complexity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FunctionMetrics:
    """Metrics for a function."""
    name: str
    line_count: int
    complexity: int
    parameters: int
    has_docstring: bool
    has_type_hints: bool
    nested_depth: int


@dataclass
class ClassMetrics:
    """Metrics for a class."""
    name: str
    line_count: int
    methods: int
    attributes: int
    has_docstring: bool
    inheritance_depth: int


class CodeAnalyzer:
    """
    Advanced code analyzer using AST parsing.
    
    This class provides sophisticated analysis of Python code to detect
    violations of constitution rules that require deep code understanding.
    """
    
    def __init__(self):
        """Initialize the code analyzer."""
        self.risky_operations = {
            'file_operations': ['open', 'file', 'read', 'write'],
            'network_operations': ['requests', 'urllib', 'socket', 'http'],
            'system_operations': ['os.system', 'subprocess', 'exec', 'eval'],
            'user_input': ['input', 'raw_input'],
            'database_operations': ['sql', 'query', 'execute', 'commit']
        }
    
    def analyze_function_complexity(self, tree: ast.AST) -> List[FunctionMetrics]:
        """
        Analyze function complexity and metrics.
        
        Args:
            tree: AST tree of the code
            
        Returns:
            List of function metrics
        """
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics = self._calculate_function_metrics(node)
                functions.append(metrics)
        
        return functions
    
    def _calculate_function_metrics(self, func_node: ast.FunctionDef) -> FunctionMetrics:
        """Calculate detailed metrics for a function."""
        line_count = self._count_function_lines(func_node)
        complexity = self._calculate_cyclomatic_complexity(func_node)
        parameters = len(func_node.args.args)
        has_docstring = ast.get_docstring(func_node) is not None
        has_type_hints = self._has_type_hints(func_node)
        nested_depth = self._calculate_nested_depth(func_node)
        
        return FunctionMetrics(
            name=func_node.name,
            line_count=line_count,
            complexity=complexity,
            parameters=parameters,
            has_docstring=has_docstring,
            has_type_hints=has_type_hints,
            nested_depth=nested_depth
        )
    
    def _count_function_lines(self, func_node: ast.FunctionDef) -> int:
        """Count lines in a function."""
        if hasattr(func_node, 'end_lineno') and func_node.end_lineno:
            return func_node.end_lineno - func_node.lineno + 1
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
    
    def _has_type_hints(self, func_node: ast.FunctionDef) -> bool:
        """Check if function has type hints."""
        # Check return type annotation
        if func_node.returns:
            return True
        
        # Check parameter type annotations
        for arg in func_node.args.args:
            if arg.annotation:
                return True
        
        return False
    
    def _calculate_nested_depth(self, func_node: ast.FunctionDef) -> int:
        """Calculate maximum nesting depth in a function."""
        max_depth = 0
        current_depth = 0
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, 
                               ast.Try, ast.With, ast.AsyncWith)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                # End of block
                current_depth -= 1
        
        return max_depth
    
    def detect_nested_loops(self, tree: ast.AST) -> List[Tuple[int, int, str]]:
        """
        Detect nested loops that could cause performance issues.
        
        Args:
            tree: AST tree of the code
            
        Returns:
            List of tuples (line_number, column, description)
        """
        nested_loops = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Check if this loop contains another loop
                for child in ast.walk(node):
                    if child != node and isinstance(child, (ast.For, ast.While)):
                        nested_loops.append((
                            node.lineno,
                            node.col_offset,
                            f"Nested loop detected: {type(node).__name__} contains {type(child).__name__}"
                        ))
        
        return nested_loops
    
    def detect_risky_operations(self, tree: ast.AST) -> List[Tuple[int, int, str, str]]:
        """
        Detect risky operations that need error handling.
        
        Args:
            tree: AST tree of the code
            
        Returns:
            List of tuples (line_number, column, operation, category)
        """
        risky_ops = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                
                for category, operations in self.risky_operations.items():
                    if any(op in func_name for op in operations):
                        risky_ops.append((
                            node.lineno,
                            node.col_offset,
                            func_name,
                            category
                        ))
        
        return risky_ops
    
    def _get_function_name(self, func_node: ast.AST) -> str:
        """Extract function name from AST node."""
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            return f"{self._get_function_name(func_node.value)}.{func_node.attr}"
        else:
            return str(func_node)
    
    def detect_mixed_concerns(self, tree: ast.AST, file_path: str) -> List[Tuple[int, int, str]]:
        """
        Detect mixed concerns (business logic in UI, etc.).
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file being analyzed
            
        Returns:
            List of tuples (line_number, column, description)
        """
        mixed_concerns = []
        file_name = file_path.lower()
        
        # Check if this is a UI file
        is_ui_file = any(keyword in file_name for keyword in 
                        ['ui', 'view', 'template', 'gui', 'interface', 'frontend'])
        
        if is_ui_file:
            # Look for business logic patterns
            business_logic_patterns = [
                'database', 'sql', 'query', 'api', 'business', 'service',
                'model', 'repository', 'dao'
            ]
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = self._get_function_name(node.func).lower()
                    for pattern in business_logic_patterns:
                        if pattern in func_name:
                            mixed_concerns.append((
                                node.lineno,
                                node.col_offset,
                                f"Business logic in UI file: {func_name}"
                            ))
        
        return mixed_concerns
    
    def detect_hardcoded_values(self, tree: ast.AST) -> List[Tuple[int, int, str, str]]:
        """
        Detect hardcoded values that should be configurable.
        
        Args:
            tree: AST tree of the code
            
        Returns:
            List of tuples (line_number, column, value, type)
        """
        hardcoded = []
        
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
                                hardcoded.append((
                                    node.lineno,
                                    node.col_offset,
                                    value,
                                    "configuration"
                                ))
        
        return hardcoded
    
    def analyze_imports(self, tree: ast.AST) -> Dict[str, Any]:
        """
        Analyze import statements for potential issues.
        
        Args:
            tree: AST tree of the code
            
        Returns:
            Dictionary with import analysis results
        """
        imports = {
            'wildcard_imports': [],
            'unused_imports': [],
            'standard_library': [],
            'third_party': [],
            'local_imports': []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == '*':
                        imports['wildcard_imports'].append(node.lineno)
                    else:
                        if '.' in alias.name:
                            imports['third_party'].append(alias.name)
                        else:
                            imports['standard_library'].append(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module == '*':
                    imports['wildcard_imports'].append(node.lineno)
                else:
                    if node.level > 0:  # Relative import
                        imports['local_imports'].append(node.module)
                    elif '.' in node.module:
                        imports['third_party'].append(node.module)
                    else:
                        imports['standard_library'].append(node.module)
        
        return imports
    
    def detect_security_issues(self, tree: ast.AST) -> List[Tuple[int, int, str, str]]:
        """
        Detect potential security issues in code.
        
        Args:
            tree: AST tree of the code
            
        Returns:
            List of tuples (line_number, column, issue, severity)
        """
        security_issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func).lower()
                
                # Check for dangerous functions
                dangerous_functions = {
                    'eval': 'critical',
                    'exec': 'critical',
                    'compile': 'high',
                    'input': 'medium',
                    'raw_input': 'medium'
                }
                
                for dangerous_func, severity in dangerous_functions.items():
                    if dangerous_func in func_name:
                        security_issues.append((
                            node.lineno,
                            node.col_offset,
                            f"Dangerous function: {func_name}",
                            severity
                        ))
        
        return security_issues
    
    def get_code_metrics(self, tree: ast.AST) -> Dict[str, Any]:
        """
        Get comprehensive code metrics.
        
        Args:
            tree: AST tree of the code
            
        Returns:
            Dictionary with various code metrics
        """
        metrics = {
            'total_lines': 0,
            'functions': 0,
            'classes': 0,
            'imports': 0,
            'comments': 0,
            'complexity': 0,
            'nested_depth': 0
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics['functions'] += 1
                metrics['complexity'] += self._calculate_cyclomatic_complexity(node)
                metrics['nested_depth'] = max(metrics['nested_depth'], 
                                            self._calculate_nested_depth(node))
            elif isinstance(node, ast.ClassDef):
                metrics['classes'] += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                metrics['imports'] += 1
        
        return metrics
