"""
Coding Standards Constitution Validator

Validates compliance with the ZeroUI 2.0 Coding Standards Constitution.
Covers Python/TypeScript standards, formatting, naming, and best practices.
"""

import re
import ast
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..models import Violation, Severity


class CodingStandardsValidator:
    """Validates coding standards and best practices."""
    
    def __init__(self):
        self.rules = {
            'R027': self._validate_python_standards,
            'R028': self._validate_typescript_standards,
            'R029': self._validate_code_formatting,
            'R030': self._validate_naming_conventions,
            'R031': self._validate_function_length,
            'R032': self._validate_complexity,
            'R033': self._validate_dependencies,
            'R034': self._validate_imports,
            'R035': self._validate_type_hints,
            'R036': self._validate_error_handling,
            'R037': self._validate_resource_management,
            'R038': self._validate_security_practices,
            'R039': self._validate_authentication_security,
            'R040': self._validate_data_protection,
            'R041': self._validate_input_validation,
            'R042': self._validate_output_sanitization,
            'R045': self._validate_performance_standards,
            'R087': self._validate_async_handlers,
            'R088': self._validate_packaging_policy
        }
    
    def validate(self, file_path: str, content: str) -> List[Violation]:
        """Validate coding standards compliance for a file."""
        violations = []
        
        # Check file type and apply appropriate standards
        if file_path.endswith('.py'):
            violations.extend(self._validate_python_standards(content, file_path))
        elif file_path.endswith(('.ts', '.js')):
            violations.extend(self._validate_typescript_standards(content, file_path))
        
        # Apply common standards
        violations.extend(self._validate_code_formatting(content, file_path))
        violations.extend(self._validate_naming_conventions(content, file_path))
        violations.extend(self._validate_function_length(content, file_path))
        violations.extend(self._validate_complexity(content, file_path))
        violations.extend(self._validate_imports(content, file_path))
        violations.extend(self._validate_error_handling(content, file_path))
        violations.extend(self._validate_security_practices(content, file_path))
        violations.extend(self._validate_performance_standards(content, file_path))
        
        return violations
    
    def _validate_python_standards(self, content: str, file_path: str) -> List[Violation]:
        """Validate Python coding standards."""
        violations = []
        
        # Check for ruff, black, mypy usage
        if 'import' in content and 'ruff' not in content.lower():
            violations.append(Violation(
                rule_id='R027',
                file_path=file_path,
                line_number=1,
                message='ruff + black (line-length 100) + mypy --strict; Python 3.11+',
                severity=Severity.ERROR,
                category='code_quality'
            ))
        
        # Check for type hints
        violations.extend(self._validate_type_hints(content, file_path))
        
        # Check for proper error handling
        violations.extend(self._validate_error_handling(content, file_path))
        
        # Check for resource management
        violations.extend(self._validate_resource_management(content, file_path))
        
        return violations
    
    def _validate_typescript_standards(self, content: str, file_path: str) -> List[Violation]:
        """Validate TypeScript coding standards."""
        violations = []
        
        # Check for eslint, prettier usage
        if 'function' in content and 'eslint' not in content.lower():
            violations.append(Violation(
                rule_id='R028',
                file_path=file_path,
                line_number=1,
                message='eslint + prettier; tsconfig strict: true, exactOptionalPropertyTypes',
                severity=Severity.ERROR,
                category='code_quality'
            ))
        
        # Check for 'any' usage
        if 'any' in content:
            violations.append(Violation(
                rule_id='R028',
                file_path=file_path,
                line_number=1,
                message='No \'any\' in TypeScript - use proper types',
                severity=Severity.WARNING,
                category='code_quality'
            ))
        
        return violations
    
    def _validate_code_formatting(self, content: str, file_path: str) -> List[Violation]:
        """Validate code formatting standards."""
        violations = []
        
        # Check for consistent formatting
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            # Check for trailing whitespace
            if line.rstrip() != line:
                violations.append(Violation(
                    rule_id='R029',
                    file_path=file_path,
                    line_number=line_num,
                    message='Trailing whitespace detected - use automated formatting',
                    severity=Severity.WARNING,
                    category='code_quality'
                ))
            
            # Check for inconsistent indentation
            if line.startswith(' ') and line.startswith('\t'):
                violations.append(Violation(
                    rule_id='R029',
                    file_path=file_path,
                    line_number=line_num,
                    message='Mixed tabs and spaces - use consistent formatting',
                    severity=Severity.WARNING,
                    category='code_quality'
                ))
        
        return violations
    
    def _validate_naming_conventions(self, content: str, file_path: str) -> List[Violation]:
        """Validate naming conventions."""
        violations = []
        
        if file_path.endswith('.py'):
            violations.extend(self._validate_python_naming(content, file_path))
        elif file_path.endswith(('.ts', '.js')):
            violations.extend(self._validate_typescript_naming(content, file_path))
        
        return violations
    
    def _validate_python_naming(self, content: str, file_path: str) -> List[Violation]:
        """Validate Python naming conventions."""
        violations = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Function names should be snake_case
                    if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                        violations.append(Violation(
                            rule_id='R030',
                            file_path=file_path,
                            line_number=node.lineno,
                            message=f'Function name \'{node.name}\' should be snake_case',
                            severity=Severity.WARNING,
                            category='code_quality'
                        ))
                
                elif isinstance(node, ast.ClassDef):
                    # Class names should be PascalCase
                    if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                        violations.append(Violation(
                            rule_id='R030',
                            file_path=file_path,
                            line_number=node.lineno,
                            message=f'Class name \'{node.name}\' should be PascalCase',
                            severity=Severity.WARNING,
                            category='code_quality'
                        ))
                
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    # Variable names should be snake_case
                    if not re.match(r'^[a-z_][a-z0-9_]*$', node.id):
                        violations.append(Violation(
                            rule_id='R030',
                            file_path=file_path,
                            line_number=node.lineno,
                            message=f'Variable name \'{node.id}\' should be snake_case',
                            severity=Severity.WARNING,
                            category='code_quality'
                        ))
        
        except SyntaxError:
            # Skip files with syntax errors
            pass
        
        return violations
    
    def _validate_typescript_naming(self, content: str, file_path: str) -> List[Violation]:
        """Validate TypeScript naming conventions."""
        violations = []
        
        # Check for camelCase function names
        function_pattern = r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        for match in re.finditer(function_pattern, content):
            func_name = match.group(1)
            if not re.match(r'^[a-z][a-zA-Z0-9]*$', func_name):
                violations.append(Violation(
                    rule_id='R030',
                    file_path=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                    message=f'Function name \'{func_name}\' should be camelCase',
                    severity=Severity.WARNING,
                    category='code_quality'
                ))
        
        # Check for PascalCase class names
        class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            if not re.match(r'^[A-Z][a-zA-Z0-9]*$', class_name):
                violations.append(Violation(
                    rule_id='R030',
                    file_path=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                    message=f'Class name \'{class_name}\' should be PascalCase',
                    severity=Severity.WARNING,
                    category='code_quality'
                ))
        
        return violations
    
    def _validate_function_length(self, content: str, file_path: str) -> List[Violation]:
        """Validate function length."""
        violations = []
        
        if file_path.endswith('.py'):
            violations.extend(self._validate_python_function_length(content, file_path))
        elif file_path.endswith(('.ts', '.js')):
            violations.extend(self._validate_typescript_function_length(content, file_path))
        
        return violations
    
    def _validate_python_function_length(self, content: str, file_path: str) -> List[Violation]:
        """Validate Python function length."""
        violations = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Count lines in function
                    func_lines = node.end_lineno - node.lineno + 1
                    if func_lines > 50:
                        violations.append(Violation(
                            rule_id='R031',
                            file_path=file_path,
                            line_number=node.lineno,
                            message=f'Function \'{node.name}\' is {func_lines} lines long (recommended: ≤50)',
                            severity=Severity.WARNING,
                            category='code_quality'
                        ))
        
        except SyntaxError:
            # Skip files with syntax errors
            pass
        
        return violations
    
    def _validate_typescript_function_length(self, content: str, file_path: str) -> List[Violation]:
        """Validate TypeScript function length."""
        violations = []
        
        # Simple line count for functions (this could be more sophisticated)
        lines = content.split('\n')
        in_function = False
        function_start = 0
        brace_count = 0
        
        for line_num, line in enumerate(lines, 1):
            if re.search(r'function\s+\w+', line) or re.search(r'\w+\s*\([^)]*\)\s*{', line):
                in_function = True
                function_start = line_num
                brace_count = line.count('{') - line.count('}')
            elif in_function:
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0:
                    # Function ended
                    func_length = line_num - function_start + 1
                    if func_length > 50:
                        violations.append(Violation(
                            rule_id='R031',
                            file_path=file_path,
                            line_number=function_start,
                            message=f'Function is {func_length} lines long (recommended: ≤50)',
                            severity=Severity.WARNING,
                            category='code_quality'
                        ))
                    in_function = False
        
        return violations
    
    def _validate_complexity(self, content: str, file_path: str) -> List[Violation]:
        """Validate cyclomatic complexity."""
        violations = []
        
        # Simple complexity check - count control flow statements
        complexity_indicators = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'case', 'switch']
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            complexity_count = sum(1 for indicator in complexity_indicators if indicator in line)
            if complexity_count > 3:
                violations.append(Violation(
                    rule_id='R032',
                    file_path=file_path,
                    line_number=line_num,
                    message=f'High complexity detected - consider using early returns',
                    severity=Severity.WARNING,
                    category='code_quality'
                ))
        
        return violations
    
    def _validate_dependencies(self, content: str, file_path: str) -> List[Violation]:
        """Validate dependency management."""
        violations = []
        
        if self._is_dependency_file(file_path):
            # Check for license information
            if 'license' not in content.lower():
                violations.append(Violation(
                    rule_id='R033',
                    file_path=file_path,
                    line_number=1,
                    message='Review new dependencies for license, size, security; block known CVEs',
                    severity=Severity.ERROR,
                    category='security'
                ))
        
        return violations
    
    def _validate_imports(self, content: str, file_path: str) -> List[Violation]:
        """Validate import organization."""
        violations = []
        
        # Check for wildcard imports
        if re.search(r'import\s+\*', content):
            violations.append(Violation(
                rule_id='R034',
                file_path=file_path,
                line_number=1,
                message='Avoid wildcard imports - use specific imports',
                severity=Severity.WARNING,
                category='code_quality'
            ))
        
        # Check import organization (simplified)
        lines = content.split('\n')
        import_lines = [line for line in lines if line.strip().startswith('import')]
        
        if len(import_lines) > 1:
            # Check if imports are grouped properly
            stdlib_imports = []
            third_party_imports = []
            local_imports = []
            
            for line in import_lines:
                if any(stdlib in line for stdlib in ['os', 'sys', 'json', 're', 'pathlib']):
                    stdlib_imports.append(line)
                elif '.' in line and not line.startswith('from .'):
                    third_party_imports.append(line)
                else:
                    local_imports.append(line)
            
            # Check order
            if third_party_imports and stdlib_imports:
                if import_lines.index(third_party_imports[0]) < import_lines.index(stdlib_imports[0]):
                    violations.append(Violation(
                        rule_id='R034',
                        file_path=file_path,
                        line_number=1,
                        message='Organize imports: stdlib, third-party, local',
                        severity=Severity.WARNING,
                        category='code_quality'
                    ))
        
        return violations
    
    def _validate_type_hints(self, content: str, file_path: str) -> List[Violation]:
        """Validate type hints usage."""
        violations = []
        
        if file_path.endswith('.py'):
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check if function has type hints
                        if not node.returns and not any(arg.annotation for arg in node.args.args):
                            violations.append(Violation(
                                rule_id='R035',
                                file_path=file_path,
                                line_number=node.lineno,
                                message=f'Function \'{node.name}\' should have type hints',
                                severity=Severity.WARNING,
                                category='code_quality'
                            ))
            except SyntaxError:
                pass
        
        return violations
    
    def _validate_error_handling(self, content: str, file_path: str) -> List[Violation]:
        """Validate error handling."""
        violations = []
        
        # Check for risky operations without error handling
        risky_operations = ['open(', 'requests.', 'urllib.', 'subprocess.', 'os.system']
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for operation in risky_operations:
                if operation in line and 'try:' not in content:
                    violations.append(Violation(
                        rule_id='R036',
                        file_path=file_path,
                        line_number=line_num,
                        message='Proper error handling with try-catch blocks and meaningful messages',
                        severity=Severity.ERROR,
                        category='code_quality'
                    ))
                    break
        
        return violations
    
    def _validate_resource_management(self, content: str, file_path: str) -> List[Violation]:
        """Validate resource management."""
        violations = []
        
        if file_path.endswith('.py'):
            # Check for file operations without context managers
            if 'open(' in content and 'with ' not in content:
                violations.append(Violation(
                    rule_id='R037',
                    file_path=file_path,
                    line_number=1,
                    message='Use context managers (with statement) for file operations',
                    severity=Severity.WARNING,
                    category='code_quality'
                ))
        
        return violations
    
    def _validate_security_practices(self, content: str, file_path: str) -> List[Violation]:
        """Validate security practices."""
        violations = []
        
        # Check for hardcoded secrets
        secret_patterns = [
            r'(?i)(password|secret|key|token)\s*=\s*["\'][^"\']+["\']',
            r'(?i)(password|secret|key|token)\s*:\s*["\'][^"\']+["\']',
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in secret_patterns:
                if re.search(pattern, line):
                    violations.append(Violation(
                        rule_id='R038',
                        file_path=file_path,
                        line_number=line_num,
                        message='No secrets in code; use environment variables and secure storage',
                        severity=Severity.ERROR,
                        category='security'
                    ))
        
        return violations
    
    def _validate_authentication_security(self, content: str, file_path: str) -> List[Violation]:
        """Validate authentication security."""
        violations = []
        
        if 'auth' in content.lower() and 'password' in content.lower():
            if 'hash' not in content.lower() and 'bcrypt' not in content.lower():
                violations.append(Violation(
                    rule_id='R039',
                    file_path=file_path,
                    line_number=1,
                    message='Secure authentication implementation with proper validation',
                    severity=Severity.ERROR,
                    category='security'
                ))
        
        return violations
    
    def _validate_data_protection(self, content: str, file_path: str) -> List[Violation]:
        """Validate data protection."""
        violations = []
        
        if 'data' in content.lower() and 'encrypt' not in content.lower():
            violations.append(Violation(
                rule_id='R040',
                file_path=file_path,
                line_number=1,
                message='Protect sensitive data with encryption and access controls',
                severity=Severity.ERROR,
                category='security'
            ))
        
        return violations
    
    def _validate_input_validation(self, content: str, file_path: str) -> List[Violation]:
        """Validate input validation."""
        violations = []
        
        if 'input' in content.lower() and 'validate' not in content.lower():
            violations.append(Violation(
                rule_id='R041',
                file_path=file_path,
                line_number=1,
                message='Validate and sanitize all user inputs',
                severity=Severity.ERROR,
                category='security'
            ))
        
        return violations
    
    def _validate_output_sanitization(self, content: str, file_path: str) -> List[Violation]:
        """Validate output sanitization."""
        violations = []
        
        if 'output' in content.lower() and 'sanitize' not in content.lower():
            violations.append(Violation(
                rule_id='R042',
                file_path=file_path,
                line_number=1,
                message='Sanitize outputs to prevent injection attacks',
                severity=Severity.ERROR,
                category='security'
            ))
        
        return violations
    
    def _validate_performance_standards(self, content: str, file_path: str) -> List[Violation]:
        """Validate performance standards."""
        violations = []
        
        # Check for performance-related keywords
        performance_keywords = ['SLO', 'timeout', 'retry', 'backpressure', 'performance']
        has_performance = any(keyword in content.lower() for keyword in performance_keywords)
        
        if not has_performance and 'api' in content.lower():
            violations.append(Violation(
                rule_id='R045',
                file_path=file_path,
                line_number=1,
                message='Publish per-route SLOs; add timeouts, retries, backpressure',
                severity=Severity.WARNING,
                category='code_quality'
            ))
        
        return violations
    
    def _validate_async_handlers(self, content: str, file_path: str) -> List[Violation]:
        """Validate async handler usage."""
        violations = []
        
        if 'handler' in content.lower() and 'async' not in content.lower():
            violations.append(Violation(
                rule_id='R087',
                file_path=file_path,
                line_number=1,
                message='Async only for handlers; avoid blocking calls; httpx for async tests',
                severity=Severity.WARNING,
                category='code_quality'
            ))
        
        return violations
    
    def _validate_packaging_policy(self, content: str, file_path: str) -> List[Violation]:
        """Validate packaging policy."""
        violations = []
        
        if self._is_dependency_file(file_path):
            if 'pip-tools' not in content.lower() and 'lock' not in content.lower():
                violations.append(Violation(
                    rule_id='R088',
                    file_path=file_path,
                    line_number=1,
                    message='pip-tools lock with hashes; no unpinned deps',
                    severity=Severity.ERROR,
                    category='code_quality'
                ))
        
        return violations
    
    def _is_dependency_file(self, file_path: str) -> bool:
        """Check if file is a dependency management file."""
        dependency_files = ['requirements.txt', 'package.json', 'Pipfile', 'poetry.lock', 'yarn.lock']
        return any(file_path.endswith(f) for f in dependency_files)
