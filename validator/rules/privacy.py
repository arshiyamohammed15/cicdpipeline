"""
Privacy and security rule validator.

This module implements validation for privacy and security rules:
- Rule 3: Protect People's Privacy
- Rule 12: Keep AI Safe + Risk Modules - Safety First
- Rule 27: Be Smart About Data
- Rule 36: Be Extra Careful with Private Data
"""

import re
import ast
from typing import List, Dict, Any, Tuple
from ..models import Violation, Severity


class PrivacyValidator:
    """
    Validates privacy and security rules.
    
    This class focuses on detecting hardcoded credentials, personal data,
    and other privacy violations in code.
    """
    
    def __init__(self):
        """Initialize the privacy validator."""
        self.credential_patterns = [
            r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']',
            r'(?i)(api_key|apikey|api-key)\s*=\s*["\'][^"\']+["\']',
            r'(?i)(secret|token|auth)\s*=\s*["\'][^"\']+["\']',
            r'(?i)(private_key|privatekey)\s*=\s*["\'][^"\']+["\']',
            r'(?i)(access_token|access_token)\s*=\s*["\'][^"\']+["\']'
        ]
        
        self.personal_data_patterns = [
            r'(?i)(ssn|social_security)\s*=\s*["\'][^"\']+["\']',
            r'(?i)(credit_card|cc_number)\s*=\s*["\'][^"\']+["\']',
            r'(?i)(phone|telephone)\s*=\s*["\'][^"\']+["\']',
            r'(?i)(email|e-mail)\s*=\s*["\'][^"\']+["\']',
            r'(?i)(address|street)\s*=\s*["\'][^"\']+["\']'
        ]
        
        self.encryption_keywords = [
            'encrypt', 'decrypt', 'hash', 'salt', 'cipher',
            'aes', 'rsa', 'ssl', 'tls', 'https'
        ]
        
        self.unsafe_keywords = [
            'plaintext', 'unencrypted', 'raw_data', 'clear_text'
        ]
    
    def validate_credentials(self, content: str, file_path: str) -> List[Violation]:
        """
        Check for hardcoded credentials.
        
        Args:
            content: File content to analyze
            file_path: Path to the file
            
        Returns:
            List of credential-related violations
        """
        violations = []
        
        for pattern in self.credential_patterns:
            for match in re.finditer(pattern, content):
                line_number = content[:match.start()].count('\n') + 1
                column_number = match.start() - content.rfind('\n', 0, match.start()) - 1
                
                violations.append(Violation(
                    rule_number=3,
                    rule_name="Protect People's Privacy",
                    severity=Severity.ERROR,
                    message="Hardcoded credentials detected - use environment variables or secure config",
                    file_path=file_path,
                    line_number=line_number,
                    column_number=column_number,
                    code_snippet=match.group(),
                    fix_suggestion="Use environment variables, secure configuration management, or encrypted storage"
                ))
        
        return violations
    
    def validate_personal_data(self, content: str, file_path: str) -> List[Violation]:
        """
        Check for personal data handling.
        
        Args:
            content: File content to analyze
            file_path: Path to the file
            
        Returns:
            List of personal data violations
        """
        violations = []
        
        for pattern in self.personal_data_patterns:
            for match in re.finditer(pattern, content):
                line_number = content[:match.start()].count('\n') + 1
                column_number = match.start() - content.rfind('\n', 0, match.start()) - 1
                
                violations.append(Violation(
                    rule_number=36,
                    rule_name="Be Extra Careful with Private Data",
                    severity=Severity.ERROR,
                    message="Personal data detected - ensure proper data classification and encryption",
                    file_path=file_path,
                    line_number=line_number,
                    column_number=column_number,
                    code_snippet=match.group(),
                    fix_suggestion="Implement proper data classification, encryption, and access controls"
                ))
        
        return violations
    
    def validate_data_encryption(self, content: str, file_path: str) -> List[Violation]:
        """
        Check for proper data encryption practices.
        
        Args:
            content: File content to analyze
            file_path: Path to the file
            
        Returns:
            List of encryption-related violations
        """
        violations = []
        
        # Check for unsafe data handling
        for keyword in self.unsafe_keywords:
            if keyword in content.lower():
                line_number = content.lower().find(keyword) + 1
                violations.append(Violation(
                    rule_number=27,
                    rule_name="Be Smart About Data",
                    severity=Severity.WARNING,
                    message=f"Unsafe data handling detected: {keyword}",
                    file_path=file_path,
                    line_number=line_number,
                    column_number=0,
                    code_snippet=keyword,
                    fix_suggestion="Consider encryption for sensitive data handling"
                ))
        
        return violations
    
    def validate_ai_safety(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for AI safety violations.
        
        Args:
            tree: AST tree of the code
            file_path: Path to the file
            
        Returns:
            List of AI safety violations
        """
        violations = []
        
        # Check for dangerous AI operations
        dangerous_operations = [
            'exec', 'eval', 'compile', 'input', 'raw_input',
            'os.system', 'subprocess', 'shell'
        ]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func).lower()
                
                for dangerous_op in dangerous_operations:
                    if dangerous_op in func_name:
                        violations.append(Violation(
                            rule_number=12,
                            rule_name="Keep AI Safe + Risk Modules - Safety First",
                            severity=Severity.ERROR,
                            message=f"Dangerous operation detected: {func_name}",
                            file_path=file_path,
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            code_snippet=func_name,
                            fix_suggestion="Use sandboxed environment or safer alternatives"
                        ))
        
        return violations
    
    def validate_data_sharing(self, content: str, file_path: str) -> List[Violation]:
        """
        Check for inappropriate data sharing patterns.
        
        Args:
            content: File content to analyze
            file_path: Path to the file
            
        Returns:
            List of data sharing violations
        """
        violations = []
        
        # Check for external API calls that might leak data
        external_patterns = [
            r'requests\.post\s*\(',
            r'urllib\.request\.urlopen\s*\(',
            r'http\.client\.HTTPSConnection\s*\('
        ]
        
        for pattern in external_patterns:
            for match in re.finditer(pattern, content):
                line_number = content[:match.start()].count('\n') + 1
                column_number = match.start() - content.rfind('\n', 0, match.start()) - 1
                
                violations.append(Violation(
                    rule_number=27,
                    rule_name="Be Smart About Data",
                    severity=Severity.WARNING,
                    message="External API call detected - ensure no sensitive data is shared",
                    file_path=file_path,
                    line_number=line_number,
                    column_number=column_number,
                    code_snippet=match.group(),
                    fix_suggestion="Verify data classification and ensure only anonymous patterns are shared"
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
    
    def validate_data_quality(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for data quality validation (Rule 11).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of data quality violations
        """
        violations = []
        
        # Check for input validation
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has input validation
                has_validation = False
                has_input_params = len(node.args.args) > 0
                
                if has_input_params:
                    # Look for validation patterns in function body
                    for child in ast.walk(node):
                        if isinstance(child, ast.If):
                            # Check for validation conditions
                            if self._has_validation_condition(child):
                                has_validation = True
                                break
                    
                    if not has_validation:
                        violations.append(Violation(
                            rule_number=11,
                            rule_name="Check Your Data",
                            severity=Severity.WARNING,
                            message=f"Function '{node.name}' with parameters lacks input validation",
                            file_path=file_path,
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            code_snippet=node.name,
                            fix_suggestion="Add input validation and sanitization"
                        ))
        
        # Check for data sanitization
        sanitization_keywords = ['strip', 'lower', 'upper', 'replace', 'encode', 'decode']
        has_sanitization = any(keyword in content.lower() for keyword in sanitization_keywords)
        
        if not has_sanitization and self._has_user_input(content):
            violations.append(Violation(
                rule_number=11,
                rule_name="Check Your Data",
                severity=Severity.INFO,
                message="User input detected without data sanitization",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Missing sanitization",
                fix_suggestion="Add data sanitization for user inputs"
            ))
        
        return violations
    
    def _has_validation_condition(self, if_node: ast.If) -> bool:
        """Check if an if statement contains validation logic."""
        validation_patterns = [
            'isinstance', 'len', 'isdigit', 'isalpha', 'strip', 'lower', 'upper',
            'isnull', 'isempty', 'valid', 'check', 'verify'
        ]
        
        for node in ast.walk(if_node):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func).lower()
                if any(pattern in func_name for pattern in validation_patterns):
                    return True
        return False
    
    def _has_user_input(self, content: str) -> bool:
        """Check if code contains user input operations."""
        input_keywords = ['input', 'raw_input', 'getpass', 'stdin', 'argv']
        return any(keyword in content.lower() for keyword in input_keywords)
    
    def validate_all(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Run all privacy and security validations.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of all privacy/security violations
        """
        violations = []
        
        violations.extend(self.validate_credentials(content, file_path))
        violations.extend(self.validate_personal_data(content, file_path))
        violations.extend(self.validate_data_encryption(content, file_path))
        violations.extend(self.validate_ai_safety(tree, file_path))
        violations.extend(self.validate_data_sharing(content, file_path))
        violations.extend(self.validate_data_quality(tree, content, file_path))
        
        return violations
