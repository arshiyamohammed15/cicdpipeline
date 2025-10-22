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
                rule_id="rule_19",
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
                rule_id="rule_19",
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
                rule_id="rule_21",
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
                rule_id="rule_21",
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
        if tree is None:
            # If no AST, fallback: detect obvious network usage without offline hints
            if any(k in content.lower() for k in ['requests', 'http', 'socket']) and not any(h in content.lower() for h in ['offline', 'cache', 'fallback', 'local']):
                violations.append(Violation(
                    rule_id="rule_28",
                    rule_number=28,
                    rule_name="Work Without Internet",
                    severity=Severity.WARNING,
                    message="Network dependencies detected without offline fallback",
                    file_path=file_path,
                    line_number=1,
                    column_number=0,
                    code_snippet="Network usage",
                    fix_suggestion="Add offline capability and local caching"
                ))
            return violations
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func).lower()
                
                # Check for external data transmission
                network_context_keywords = ['http', 'https', 'api.', 'cloud', 'aws', 'gcp', 'azure', 'requests.']
                verb_indicators = ['send', 'post', 'upload']
                verb_with_context = any(v in func_name for v in verb_indicators) and any(ctx in func_name for ctx in network_context_keywords)
                # Avoid false positives for local pattern sharing helpers
                if any(keyword in func_name for keyword in self.cloud_keywords) or (verb_with_context and 'anonymous' not in func_name and 'pattern' not in func_name):
                    violations.append(Violation(
                rule_id="rule_23",
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
        if tree is None:
            return violations
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                has_try_catch = True
                break
        
        if not has_try_catch and self._has_risky_operations(tree):
            violations.append(Violation(
                rule_id="rule_30",
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
                            for child in ast.walk(tree):
                                if isinstance(child, ast.Call):
                                    func_name = self._get_function_name(child.func).lower()
                                    # For sensitive data, any external-sounding verb is enough
                                    if any(verb in func_name for verb in ['send', 'post', 'upload', 'push', 'publish']):
                                        violations.append(Violation(
                rule_id="rule_23",
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
        if tree is not None:
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if class requires configuration in __init__
                    has_config_requirement = False
                    has_default_values = False
                    for child in node.body:
                        if isinstance(child, ast.FunctionDef) and child.name == '__init__':
                            # Compute which args have defaults
                            positional = [a.arg for a in child.args.args if a.arg != 'self']
                            defaults_count = len(child.args.defaults)
                            defaulted = set(positional[-defaults_count:]) if defaults_count else set()
                            has_default_values = len(defaulted) > 0
                            has_config_requirement = any(name not in defaulted for name in positional)
                    if has_config_requirement and not has_default_values:
                        violations.append(Violation(
                rule_id="rule_24",
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
                rule_id="rule_24",
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
        
        # Check for offline fallback patterns (ignore comments and inline trailing comments)
        cleaned_lines = []
        for line in content.splitlines():
            # remove inline comments after '#'
            no_inline = line.split('#', 1)[0]
            if not no_inline.strip().startswith('#'):
                cleaned_lines.append(no_inline)
        code_only = '\n'.join(cleaned_lines)
        offline_patterns = [
            'offline', 'cache', 'local', 'fallback', 'backup', 'sync'
        ]
        for pattern in offline_patterns:
            if re.search(pattern, code_only, re.IGNORECASE):
                has_offline_fallback = True
                break
        
        # Determine whether network calls occur inside functions without try/except
        uses_network_calls = False
        function_has_network_calls = False
        # Scan entire tree for any network call
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                call_name = self._get_function_name(n.func).lower()
                if any(lib in call_name for lib in ['requests.', 'urllib', 'http.', 'socket.']):
                    uses_network_calls = True
                    break
        # Specifically check calls inside functions
        for func in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            for inner in ast.walk(func):
                if isinstance(inner, ast.Call):
                    inner_name = self._get_function_name(inner.func).lower()
                    if any(lib in inner_name for lib in ['requests.', 'urllib', 'http.', 'socket.']):
                        function_has_network_calls = True
                        break
            if function_has_network_calls:
                break

        # WARNING when network calls occur inside a function and there is no offline fallback
        if has_network_imports and not has_offline_fallback and function_has_network_calls:
            violations.append(Violation(
                rule_id="rule_28",
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
        
        if has_network_imports and uses_network_calls and not has_caching:
            violations.append(Violation(
                rule_id="rule_28",
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
