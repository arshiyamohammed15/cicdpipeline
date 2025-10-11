"""
Architecture rule validator.

This module implements validation for architecture rules:
- Rule 19: Keep Different Parts Separate
- Rule 21: Use the Hybrid System Design
- Rule 23: Process Data Locally First
"""

import ast
import re
from typing import List, Dict, Any, Tuple
from pathlib import Path
from ..models import Violation, Severity


class ArchitectureValidator:
    """
    Validates architecture-related rules.
    
    This class focuses on detecting architectural violations like
    mixed concerns, improper data flow, and system design issues.
    """
    
    def __init__(self):
        """Initialize the architecture validator."""
        self.ui_keywords = ['ui', 'view', 'template', 'gui', 'interface', 'frontend', 'widget']
        self.business_logic_keywords = [
            'business', 'service', 'model', 'repository', 'dao', 'controller',
            'logic', 'algorithm', 'calculation', 'processing'
        ]
        self.data_keywords = [
            'database', 'sql', 'query', 'api', 'request', 'response',
            'data', 'storage', 'persistence'
        ]
        self.cloud_keywords = [
            'cloud', 'aws', 'azure', 'gcp', 'remote', 'external', 'api',
            'http', 'https', 'rest', 'graphql'
        ]
    
    def validate_separation_of_concerns(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for separation of concerns violations.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of separation of concerns violations
        """
        violations = []
        file_name = Path(file_path).name.lower()
        
        # Check if this is a UI file
        is_ui_file = any(keyword in file_name for keyword in self.ui_keywords)
        
        if is_ui_file:
            # Look for business logic in UI files
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = self._get_function_name(node.func).lower()
                    
                    for keyword in self.business_logic_keywords:
                        if keyword in func_name:
                            violations.append(Violation(
                                rule_number=19,
                                rule_name="Keep Different Parts Separate",
                                severity=Severity.ERROR,
                                message=f"Business logic detected in UI file: {func_name}",
                                file_path=file_path,
                                line_number=node.lineno,
                                column_number=node.col_offset,
                                code_snippet=func_name,
                                fix_suggestion="Move business logic to separate service/controller layer"
                            ))
        
        # Check for data access in UI files
        if is_ui_file:
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = self._get_function_name(node.func).lower()
                    
                    for keyword in self.data_keywords:
                        if keyword in func_name:
                            violations.append(Violation(
                                rule_number=19,
                                rule_name="Keep Different Parts Separate",
                                severity=Severity.ERROR,
                                message=f"Data access detected in UI file: {func_name}",
                                file_path=file_path,
                                line_number=node.lineno,
                                column_number=node.col_offset,
                                code_snippet=func_name,
                                fix_suggestion="Use data access layer or repository pattern"
                            ))
        
        return violations
    
    def validate_hybrid_system_design(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for hybrid system design compliance.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of hybrid system design violations
        """
        violations = []
        
        # Check for proper module separation
        file_name = Path(file_path).name.lower()
        
        # IDE Extension should only show information
        if 'extension' in file_name or 'ide' in file_name:
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = self._get_function_name(node.func).lower()
                    
                    # IDE Extension shouldn't process data
                    if any(keyword in func_name for keyword in ['process', 'analyze', 'compute']):
                        violations.append(Violation(
                            rule_number=21,
                            rule_name="Use the Hybrid System Design",
                            severity=Severity.ERROR,
                            message="IDE Extension should only display information, not process data",
                            file_path=file_path,
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            code_snippet=func_name,
                            fix_suggestion="Move data processing to Edge Agent"
                        ))
        
        # Edge Agent should process data locally
        if 'agent' in file_name or 'edge' in file_name:
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = self._get_function_name(node.func).lower()
                    
                    # Edge Agent shouldn't send data to cloud
                    if any(keyword in func_name for keyword in ['upload', 'send', 'post', 'put']):
                        violations.append(Violation(
                            rule_number=21,
                            rule_name="Use the Hybrid System Design",
                            severity=Severity.WARNING,
                            message="Edge Agent should process data locally, not send to cloud",
                            file_path=file_path,
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            code_snippet=func_name,
                            fix_suggestion="Ensure data processing happens locally in Edge Agent"
                        ))
        
        return violations
    
    def validate_local_data_processing(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for local data processing compliance.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of local data processing violations
        """
        violations = []
        
        # Check for source code leaving the company
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func).lower()
                
                # Check for external data transmission
                if any(keyword in func_name for keyword in self.cloud_keywords):
                    violations.append(Violation(
                        rule_number=23,
                        rule_name="Process Data Locally First",
                        severity=Severity.ERROR,
                        message="Source code or sensitive data should not leave the company",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=func_name,
                        fix_suggestion="Process data locally and only send anonymous patterns to cloud"
                    ))
        
        return violations
    
    def validate_module_consistency(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for module consistency.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of module consistency violations
        """
        violations = []
        
        # Check for consistent error handling
        has_try_catch = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                has_try_catch = True
                break
        
        if not has_try_catch and self._has_risky_operations(tree):
            violations.append(Violation(
                rule_number=30,
                rule_name="Make All Modules Feel Like One Product",
                severity=Severity.WARNING,
                message="Inconsistent error handling - all modules should handle errors the same way",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Missing error handling",
                fix_suggestion="Implement consistent error handling across all modules"
            ))
        
        return violations
    
    def validate_data_flow(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for proper data flow patterns.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of data flow violations
        """
        violations = []
        
        # Check for proper data classification
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.lower()
                        
                        # Check for sensitive data variables
                        if any(keyword in var_name for keyword in ['password', 'secret', 'private', 'personal']):
                            # Check if it's being sent externally
                            for child in ast.walk(node):
                                if isinstance(child, ast.Call):
                                    func_name = self._get_function_name(child.func).lower()
                                    if any(keyword in func_name for keyword in ['send', 'post', 'upload']):
                                        violations.append(Violation(
                                            rule_number=23,
                                            rule_name="Process Data Locally First",
                                            severity=Severity.ERROR,
                                            message="Sensitive data being sent externally",
                                            file_path=file_path,
                                            line_number=node.lineno,
                                            column_number=node.col_offset,
                                            code_snippet=var_name,
                                            fix_suggestion="Keep sensitive data local, only send anonymous patterns"
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
        risky_keywords = [
            'open', 'file', 'requests', 'urllib', 'subprocess',
            'os.system', 'eval', 'exec', 'input'
        ]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func).lower()
                if any(keyword in func_name for keyword in risky_keywords):
                    return True
        
        return False
    
    def validate_zero_configuration(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for zero-configuration patterns (Rule 24).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of configuration-related violations
        """
        violations = []
        
        # Check for mandatory configuration before use
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if class requires configuration in __init__
                has_config_requirement = False
                has_default_values = False
                
                for child in node.body:
                    if isinstance(child, ast.FunctionDef) and child.name == '__init__':
                        for arg in child.args.args:
                            if arg.arg != 'self':
                                # Check for default values
                                if arg in child.args.defaults:
                                    has_default_values = True
                                else:
                                    has_config_requirement = True
                
                if has_config_requirement and not has_default_values:
                    violations.append(Violation(
                        rule_number=24,
                        rule_name="Don't Make People Configure Before Using",
                        severity=Severity.WARNING,
                        message=f"Class '{node.name}' requires configuration before use",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=node.name,
                        fix_suggestion="Provide default values or make configuration optional"
                    ))
        
        # Check for configuration files that are required
        config_patterns = [
            r'config\.json',
            r'config\.yaml',
            r'config\.ini',
            r'\.env',
            r'settings\.py'
        ]
        
        for pattern in config_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # Check if it's required vs optional
                if 'required' in content.lower() or 'must' in content.lower():
                    violations.append(Violation(
                        rule_number=24,
                        rule_name="Don't Make People Configure Before Using",
                        severity=Severity.INFO,
                        message="Configuration file appears to be required before use",
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet=pattern,
                        fix_suggestion="Make configuration optional with sensible defaults"
                    ))
        
        return violations
    
    def validate_offline_capability(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for offline capability (Rule 28).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of offline capability violations
        """
        violations = []
        
        # Check for network dependencies without offline fallback
        network_imports = [
            'requests', 'urllib', 'http', 'socket', 'ftplib', 'smtplib',
            'poplib', 'imaplib', 'telnetlib', 'xmlrpc'
        ]
        
        has_network_imports = False
        has_offline_fallback = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(network_lib in alias.name for network_lib in network_imports):
                        has_network_imports = True
                        break
            elif isinstance(node, ast.ImportFrom):
                if node.module and any(network_lib in node.module for network_lib in network_imports):
                    has_network_imports = True
                    break
        
        # Check for offline fallback patterns
        offline_patterns = [
            'offline', 'cache', 'local', 'fallback', 'backup', 'sync'
        ]
        
        for pattern in offline_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                has_offline_fallback = True
                break
        
        if has_network_imports and not has_offline_fallback:
            violations.append(Violation(
                rule_number=28,
                rule_name="Work Without Internet",
                severity=Severity.WARNING,
                message="Network dependencies detected without offline fallback",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Network imports",
                fix_suggestion="Add offline capability and local caching"
            ))
        
        # Check for local caching mechanisms
        cache_patterns = [
            r'cache',
            r'local_storage',
            r'sqlite',
            r'pickle',
            r'json\.dump',
            r'json\.load'
        ]
        
        has_caching = any(re.search(pattern, content, re.IGNORECASE) for pattern in cache_patterns)
        
        if has_network_imports and not has_caching:
            violations.append(Violation(
                rule_number=28,
                rule_name="Work Without Internet",
                severity=Severity.INFO,
                message="Network operations without local caching detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Missing caching",
                fix_suggestion="Implement local caching for offline operation"
            ))
        
        return violations
    
    def validate_all(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Run all architecture validations.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of all architecture violations
        """
        violations = []
        
        violations.extend(self.validate_separation_of_concerns(tree, file_path))
        violations.extend(self.validate_hybrid_system_design(tree, file_path))
        violations.extend(self.validate_local_data_processing(tree, file_path))
        violations.extend(self.validate_module_consistency(tree, file_path))
        violations.extend(self.validate_data_flow(tree, file_path))
        violations.extend(self.validate_zero_configuration(tree, content, file_path))
        violations.extend(self.validate_offline_capability(tree, content, file_path))
        
        return violations
