"""
Comments Constitution Validator

Validates compliance with the ZeroUI 2.0 Comments Constitution.
Covers documentation standards, simple English, and comment quality.
"""

import re
import ast
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..models import Violation, Severity


class CommentsValidator:
    """Validates comment and documentation standards."""
    
    def __init__(self):
        self.rules = {
            'R008': self._validate_simple_english_comments,
            'R046': self._validate_function_documentation,
            'R047': self._validate_class_documentation,
            'R048': self._validate_module_documentation,
            'R049': self._validate_api_documentation,
            'R050': self._validate_error_documentation,
            'R051': self._validate_configuration_documentation,
            'R052': self._validate_security_documentation,
            'R053': self._validate_readme_requirements,
            'R089': self._validate_todo_policy
        }
        
        # Banned words for simple English
        self.banned_words = [
            'utilize', 'leverage', 'aforementioned', 'herein', 'thusly',
            'performant', 'instantiate', 'facilitate', 'implement', 'execute',
            'utilize', 'leverage', 'aforementioned', 'herein', 'thusly'
        ]
    
    def validate(self, file_path: str, content: str) -> List[Violation]:
        """Validate comment and documentation compliance for a file."""
        violations = []
        
        # Check for simple English in comments
        violations.extend(self._validate_simple_english_comments(content, file_path))
        
        # Check for proper documentation
        violations.extend(self._validate_function_documentation(content, file_path))
        violations.extend(self._validate_class_documentation(content, file_path))
        violations.extend(self._validate_module_documentation(content, file_path))
        violations.extend(self._validate_api_documentation(content, file_path))
        violations.extend(self._validate_error_documentation(content, file_path))
        violations.extend(self._validate_configuration_documentation(content, file_path))
        violations.extend(self._validate_security_documentation(content, file_path))
        
        # Check for TODO policy
        violations.extend(self._validate_todo_policy(content, file_path))
        
        # Check for README requirements
        violations.extend(self._validate_readme_requirements(content, file_path))
        
        return violations
    
    def _validate_simple_english_comments(self, content: str, file_path: str) -> List[Violation]:
        """Validate simple English in comments."""
        violations = []
        
        # Extract comments from content
        comments = self._extract_comments(content, file_path)
        
        for comment in comments:
            # Check for banned words
            for banned_word in self.banned_words:
                if banned_word.lower() in comment['text'].lower():
                    violations.append(Violation(
                        rule_id='R008',
                        rule_name=f'Banned word "{banned_word}" in comment - use simple English',
                        severity=Severity.WARNING,
                        message=f'Banned word "{banned_word}" in comment - use simple English',
                        file_path=file_path,
                        line_number=comment['line'],
                        column_number=0,
                        code_snippet="",
                        category='documentation'
                    
                    ))
            
            # Check sentence length (max 15 words)
            sentences = re.split(r'[.!?]+', comment['text'])
            for sentence in sentences:
                words = sentence.strip().split()
                if len(words) > 15:
                    violations.append(Violation(
                        rule_id='R008',
                        file_path=file_path,
                        line_number=comment['line'],
                        message=f'Sentence too long ({len(words)} words, max 15) - use simple English',
                        severity=Severity.WARNING,
                        category='documentation'
                    ))
            
            # Check grade level (simplified - count complex words)
            complex_words = self._count_complex_words(comment['text'])
            if complex_words > 2:  # Simplified grade level check
                violations.append(Violation(
                        rule_id='R008',
                        rule_name='Comment too complex - use grade 8 level English',
                        severity=Severity.WARNING,
                        message='Comment too complex - use grade 8 level English',
                        file_path=file_path,
                        line_number=comment['line'],
                        column_number=0,
                        code_snippet="",
                        category='documentation'
                
                    ))
        
        return violations
    
    def _validate_function_documentation(self, content: str, file_path: str) -> List[Violation]:
        """Validate function documentation."""
        violations = []
        
        if file_path.endswith('.py'):
            violations.extend(self._validate_python_function_docs(content, file_path))
        elif file_path.endswith(('.ts', '.js')):
            violations.extend(self._validate_typescript_function_docs(content, file_path))
        
        return violations
    
    def _validate_python_function_docs(self, content: str, file_path: str) -> List[Violation]:
        """Validate Python function documentation."""
        violations = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if function is public (not starting with _)
                    if not node.name.startswith('_'):
                        # Check for docstring
                        if not ast.get_docstring(node):
                            violations.append(Violation(
                        rule_id='R046',
                        rule_name=f'Public function \'{node.name}\' must have docstring with WHAT + WHY + Steps',
                        severity=Severity.WARNING,
                        message=f'Public function \'{node.name}\' must have docstring with WHAT + WHY + Steps',
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=0,
                        code_snippet="",
                        category='documentation'
                            
                    ))
                        else:
                            # Check docstring quality
                            docstring = ast.get_docstring(node)
                            if not self._is_quality_docstring(docstring):
                                violations.append(Violation(
                        rule_id='R046',
                        rule_name=f'Function \'{node.name}\' docstring should include WHAT + WHY + Steps',
                        severity=Severity.WARNING,
                        message=f'Function \'{node.name}\' docstring should include WHAT + WHY + Steps',
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=0,
                        code_snippet="",
                        category='documentation'
                                
                    ))
        except SyntaxError:
            # Skip files with syntax errors
            pass
        
        return violations
    
    def _validate_typescript_function_docs(self, content: str, file_path: str) -> List[Violation]:
        """Validate TypeScript function documentation."""
        violations = []
        
        # Look for public functions without JSDoc comments
        function_pattern = r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        for match in re.finditer(function_pattern, content):
            func_name = match.group(1)
            if not func_name.startswith('_'):
                # Check for JSDoc comment before function
                func_start = match.start()
                before_func = content[:func_start]
                if '/**' not in before_func or '*/' not in before_func:
                    violations.append(Violation(
                        rule_id='R046',
                        rule_name=f'Public function \'{func_name}\' must have JSDoc documentation',
                        severity=Severity.WARNING,
                        message=f'Public function \'{func_name}\' must have JSDoc documentation',
                        file_path=file_path,
                        line_number=content[:func_start].count('\n') + 1,
                        column_number=0,
                        code_snippet="",
                        category='documentation'
                    
                    ))
        
        return violations
    
    def _validate_class_documentation(self, content: str, file_path: str) -> List[Violation]:
        """Validate class documentation."""
        violations = []
        
        if file_path.endswith('.py'):
            violations.extend(self._validate_python_class_docs(content, file_path))
        elif file_path.endswith(('.ts', '.js')):
            violations.extend(self._validate_typescript_class_docs(content, file_path))
        
        return violations
    
    def _validate_python_class_docs(self, content: str, file_path: str) -> List[Violation]:
        """Validate Python class documentation."""
        violations = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if class is public (not starting with _)
                    if not node.name.startswith('_'):
                        # Check for docstring
                        if not ast.get_docstring(node):
                            violations.append(Violation(
                        rule_id='R047',
                        rule_name=f'Public class \'{node.name}\' must have docstring explaining purpose and usage',
                        severity=Severity.WARNING,
                        message=f'Public class \'{node.name}\' must have docstring explaining purpose and usage',
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=0,
                        code_snippet="",
                        category='documentation'
                            
                    ))
        except SyntaxError:
            # Skip files with syntax errors
            pass
        
        return violations
    
    def _validate_typescript_class_docs(self, content: str, file_path: str) -> List[Violation]:
        """Validate TypeScript class documentation."""
        violations = []
        
        # Look for public classes without JSDoc comments
        class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            if not class_name.startswith('_'):
                # Check for JSDoc comment before class
                class_start = match.start()
                before_class = content[:class_start]
                if '/**' not in before_class or '*/' not in before_class:
                    violations.append(Violation(
                        rule_id='R047',
                        rule_name=f'Public class \'{class_name}\' must have JSDoc documentation',
                        severity=Severity.WARNING,
                        message=f'Public class \'{class_name}\' must have JSDoc documentation',
                        file_path=file_path,
                        line_number=content[:class_start].count('\n') + 1,
                        column_number=0,
                        code_snippet="",
                        category='documentation'
                    
                    ))
        
        return violations
    
    def _validate_module_documentation(self, content: str, file_path: str) -> List[Violation]:
        """Validate module documentation."""
        violations = []
        
        if file_path.endswith('.py'):
            # Check for module docstring at the top
            lines = content.split('\n')
            has_module_docstring = False
            
            for i, line in enumerate(lines[:10]):  # Check first 10 lines
                if line.strip().startswith('"""') or line.strip().startswith("'''"):
                    has_module_docstring = True
                    break
            
            if not has_module_docstring:
                violations.append(Violation(
                        rule_id='R048',
                        rule_name='Module must have docstring explaining purpose and exports',
                        severity=Severity.WARNING,
                        message='Module must have docstring explaining purpose and exports',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='documentation'
                
                    ))
        
        return violations
    
    def _validate_api_documentation(self, content: str, file_path: str) -> List[Violation]:
        """Validate API documentation."""
        violations = []
        
        # Check for API endpoints without documentation
        api_patterns = [
            r'@app\.route\s*\([^)]+\)',
            r'@router\.(get|post|put|delete|patch)\s*\([^)]+\)',
            r'router\.(get|post|put|delete|patch)\s*\([^)]+\)'
        ]
        
        for pattern in api_patterns:
            for match in re.finditer(pattern, content):
                # Check for documentation before the endpoint
                endpoint_start = match.start()
                before_endpoint = content[:endpoint_start]
                if '"""' not in before_endpoint and "'''" not in before_endpoint:
                    violations.append(Violation(
                        rule_id='R049',
                        rule_name='API endpoints must have comprehensive documentation',
                        severity=Severity.WARNING,
                        message='API endpoints must have comprehensive documentation',
                        file_path=file_path,
                        line_number=content[:endpoint_start].count('\n') + 1,
                        column_number=0,
                        code_snippet="",
                        category='documentation'
                    
                    ))
        
        return violations
    
    def _validate_error_documentation(self, content: str, file_path: str) -> List[Violation]:
        """Validate error handling documentation."""
        violations = []
        
        # Check for error handling without documentation
        error_patterns = ['raise', 'except', 'throw', 'error', 'exception']
        
        for pattern in error_patterns:
            if pattern in content.lower():
                # Check if error handling is documented
                if 'docstring' not in content.lower() and 'comment' not in content.lower():
                    violations.append(Violation(
                        rule_id='R050',
                        rule_name='Error handling must be documented with possible exceptions',
                        severity=Severity.WARNING,
                        message='Error handling must be documented with possible exceptions',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='documentation'
                    
                    ))
                break
        
        return violations
    
    def _validate_configuration_documentation(self, content: str, file_path: str) -> List[Violation]:
        """Validate configuration documentation."""
        violations = []
        
        # Check for configuration without documentation
        config_keywords = ['config', 'setting', 'parameter', 'option', 'env', 'environment']
        
        has_config = any(keyword in content.lower() for keyword in config_keywords)
        if has_config:
            # Check if configuration is documented
            if 'docstring' not in content.lower() and 'comment' not in content.lower():
                violations.append(Violation(
                        rule_id='R051',
                        rule_name='Configuration options must be documented with defaults and ranges',
                        severity=Severity.WARNING,
                        message='Configuration options must be documented with defaults and ranges',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='documentation'
                
                    ))
        
        return violations
    
    def _validate_security_documentation(self, content: str, file_path: str) -> List[Violation]:
        """Validate security documentation."""
        violations = []
        
        # Check for security-related code without documentation
        security_keywords = ['security', 'auth', 'encrypt', 'hash', 'token', 'password']
        
        has_security = any(keyword in content.lower() for keyword in security_keywords)
        if has_security:
            # Check if security is documented
            if 'docstring' not in content.lower() and 'comment' not in content.lower():
                violations.append(Violation(
                        rule_id='R052',
                        rule_name='Security-related code must be documented with threat model',
                        severity=Severity.WARNING,
                        message='Security-related code must be documented with threat model',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='documentation'
                
                    ))
        
        return violations
    
    def _validate_readme_requirements(self, content: str, file_path: str) -> List[Violation]:
        """Validate README requirements."""
        violations = []
        
        # Check if this is a README file
        if 'README' in file_path.upper():
            # Check for required sections
            required_sections = ['setup', 'usage', 'installation', 'getting started']
            has_required_sections = any(section in content.lower() for section in required_sections)
            
            if not has_required_sections:
                violations.append(Violation(
                        rule_id='R053',
                        rule_name='Projects must have comprehensive README with setup and usage',
                        severity=Severity.WARNING,
                        message='Projects must have comprehensive README with setup and usage',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='documentation'
                
                    ))
        
        return violations
    
    def _validate_todo_policy(self, content: str, file_path: str) -> List[Violation]:
        """Validate TODO policy compliance."""
        violations = []
        
        # Check for TODO comments
        todo_pattern = r'TODO\s*[:(]?\s*([^\\n]*)'
        for match in re.finditer(todo_pattern, content, re.IGNORECASE):
            todo_text = match.group(1).strip()
            line_number = content[:match.start()].count('\n') + 1
            
            # Check if TODO follows the required format: TODO(owner): description [ticket] [date]
            if not re.match(r'\([^)]+\):', todo_text):
                violations.append(Violation(
                        rule_id='R089',
                        rule_name='TODO(owner): description [ticket] [date] format required',
                        severity=Severity.WARNING,
                        message='TODO(owner): description [ticket] [date] format required',
                        file_path=file_path,
                        line_number=line_number,
                        column_number=0,
                        code_snippet="",
                        category='documentation'
                
                    ))
        
        return violations
    
    def _extract_comments(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract comments from content."""
        comments = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Python comments
            if file_path.endswith('.py'):
                if line.strip().startswith('#'):
                    comment_text = line.strip()[1:].strip()
                    if comment_text:
                        comments.append({
                            'line': line_num,
                            'text': comment_text,
                            'type': 'line'
                        })
            
            # JavaScript/TypeScript comments
            elif file_path.endswith(('.js', '.ts')):
                if line.strip().startswith('//'):
                    comment_text = line.strip()[2:].strip()
                    if comment_text:
                        comments.append({
                            'line': line_num,
                            'text': comment_text,
                            'type': 'line'
                        })
        
        return comments
    
    def _count_complex_words(self, text: str) -> int:
        """Count complex words in text (simplified)."""
        # Simple heuristic: words with more than 3 syllables or technical terms
        complex_words = [
            'implementation', 'configuration', 'initialization', 'authentication',
            'authorization', 'encryption', 'decryption', 'optimization',
            'initialization', 'configuration', 'authentication', 'authorization'
        ]
        
        words = text.lower().split()
        complex_count = sum(1 for word in words if word in complex_words)
        
        # Also count words with more than 3 syllables (simplified)
        for word in words:
            if len(word) > 8 and word not in complex_words:
                complex_count += 1
        
        return complex_count
    
    def _is_quality_docstring(self, docstring: str) -> bool:
        """Check if docstring is of good quality."""
        if not docstring:
            return False
        
        # Check for WHAT (description)
        has_what = len(docstring.strip()) > 10
        
        # Check for WHY (purpose/reason)
        why_keywords = ['because', 'to', 'for', 'purpose', 'reason', 'why']
        has_why = any(keyword in docstring.lower() for keyword in why_keywords)
        
        # Check for Steps (if applicable)
        has_steps = 'step' in docstring.lower() or 'process' in docstring.lower()
        
        return has_what and (has_why or has_steps)
