#!/usr/bin/env python3
"""
Privacy & Security Rules Validator

Validates code against privacy and security principles:
- Protect people's privacy
- Check your data
- Keep AI safe
- Be smart about data
- Be extra careful with private data
"""

import ast
import re
from typing import List
from..models import Violation, Severity
from..base_validator import BaseRuleValidator


class PrivacyValidator(BaseRuleValidator):
    """Validator for privacy and security rules."""

    def __init__(self, rule_config: dict = None):
        if rule_config is None:
            rule_config = {
                "category": "privacy_security",
                "priority": "critical",
                "description": "Privacy and security principles",
                "rules": [3, 11, 12, 27, 36]
            }
        super().__init__(rule_config)

    def validate_protect_privacy(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for privacy violations.

        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file

        Returns:
            List of violations
        """
        violations = []

        # Check for hardcoded credentials
        credential_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'\b[A-Za-z0-9_-]*key\s*=\s*["\'][^"\']+["\']'
        ]

        for pattern in credential_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_number = content[:match.start()].count('\n') + 1
                violations.append(self.create_violation(
                    rule_name="Protect people's privacy",
                    severity=Severity.ERROR,
                    message="Hardcoded credentials/API key detected - security risk",
                    file_path=file_path,
                    line_number=line_number,
                    column_number=0,
                    code_snippet=match.group(),
                    fix_suggestion="Use environment variables or secure configuration"
                ))

        # Check for personal data patterns
        personal_data_patterns = [
            r'ssn\s*=\s*["\'][^"\']+["\']',
            r'social_security\s*=\s*["\'][^"\']+["\']',
            r'credit_card\s*=\s*["\'][^"\']+["\']',
            r'phone\s*=\s*["\'][^"\']+["\']',
            r'email\s*=\s*["\'][^"\']+["\']'
        ]

        for pattern in personal_data_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_number = content[:match.start()].count('\n') + 1
                violations.append(self.create_violation(
                    rule_name="Protect people's privacy",
                    severity=Severity.ERROR,
                    message="Personal data detected - ensure proper data classification",
                    file_path=file_path,
                    line_number=line_number,
                    column_number=0,
                    code_snippet=match.group(),
                    fix_suggestion="Implement proper data classification and encryption"
                ))

        return violations

    def validate_check_data(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for data validation.

        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file

        Returns:
            List of violations
        """
        violations = []

        # Check for input validation
        input_patterns = ['input(', 'raw_input(', 'sys.stdin']
        has_input = any(pattern in content for pattern in input_patterns)

        if has_input:
            # Check for validation
            validation_patterns = ['validate', 'check', 'verify', 'sanitize', 'strip']
            has_validation = any(pattern in content.lower() for pattern in validation_patterns)

            if not has_validation:
                violations.append(self.create_violation(
                    rule_name="Check your data",
                    severity=Severity.WARNING,
                    message="Input detected without validation",
                    file_path=file_path,
                    line_number=1,
                    column_number=0,
                    code_snippet="Input validation",
                    fix_suggestion="Add input validation and sanitization"
                ))

        return violations

    def validate_keep_ai_safe(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for AI safety.

        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file

        Returns:
            List of violations
        """
        violations = []

        # Check for AI-related code
        ai_patterns = ['ai.', 'artificial_intelligence', 'machine_learning', 'ml.', 'neural_network']
        has_ai = any(pattern in content.lower() for pattern in ai_patterns)

        if has_ai:
            # Check for safety measures
            safety_patterns = ['safety', 'guard', 'constraint', 'limit', 'bound']
            has_safety = any(pattern in content.lower() for pattern in safety_patterns)

            if not has_safety:
                violations.append(self.create_violation(
                    rule_name="Keep AI safe",
                    severity=Severity.WARNING,
                    message="AI code detected without safety measures",
                    file_path=file_path,
                    line_number=1,
                    column_number=0,
                    code_snippet="AI safety",
                    fix_suggestion="Implement AI safety measures and constraints"
                ))

        return violations

    def validate_smart_data_handling(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for smart data handling.

        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file

        Returns:
            List of violations
        """
        violations = []

        # Check for data processing patterns
        data_patterns = ['data', 'database', 'db.', 'sql', 'query']
        has_data = any(pattern in content.lower() for pattern in data_patterns)

        if has_data:
            # Check for optimization
            optimization_patterns = ['index', 'cache', 'optimize', 'efficient', 'batch']
            has_optimization = any(pattern in content.lower() for pattern in optimization_patterns)

            if not has_optimization:
                violations.append(self.create_violation(
                    rule_name="Be smart about data",
                    severity=Severity.INFO,
                    message="Data operations detected without optimization",
                    file_path=file_path,
                    line_number=1,
                    column_number=0,
                    code_snippet="Data optimization",
                    fix_suggestion="Consider data optimization techniques"
                ))

        return violations

    def validate_extra_careful_private_data(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for extra care with private data.

        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file

        Returns:
            List of violations
        """
        violations = []

        # Check for private data handling
        private_patterns = ['private', 'confidential', 'sensitive', 'personal']
        has_private = any(pattern in content.lower() for pattern in private_patterns)

        if has_private:
            # Check for encryption
            encryption_patterns = ['encrypt', 'hash', 'secure', 'cipher', 'crypto']
            has_encryption = any(pattern in content.lower() for pattern in encryption_patterns)

            if not has_encryption:
                violations.append(self.create_violation(
                    rule_name="Be extra careful with private data",
                    severity=Severity.WARNING,
                    message="Private data detected without encryption",
                    file_path=file_path,
                    line_number=1,
                    column_number=0,
                    code_snippet="Private data encryption",
                    fix_suggestion="Implement encryption for private data"
                ))

        return violations

    def validate_all(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Validate all privacy and security rules.

        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file

        Returns:
            List of all violations found
        """
        violations = []

        violations.extend(self.validate_protect_privacy(tree, content, file_path))
        violations.extend(self.validate_check_data(tree, content, file_path))
        violations.extend(self.validate_keep_ai_safe(tree, content, file_path))
        violations.extend(self.validate_smart_data_handling(tree, content, file_path))
        violations.extend(self.validate_extra_careful_private_data(tree, content, file_path))

        return violations
