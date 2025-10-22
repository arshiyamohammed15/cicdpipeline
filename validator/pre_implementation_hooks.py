"""
Pre-Implementation Hooks for ALL 280 Constitution Rules

This module provides comprehensive validation of prompts before AI code generation,
ensuring ALL 280 Constitution rules are enforced at the source rather than after generation.
"""

import re
import ast
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from validator.models import Violation, Severity


class ComprehensivePreImplementationValidator:
    """
    Validates ALL 280 Constitution rules before AI code generation.
    
    This prevents violations at the source rather than detecting them after generation.
    """
    
    def __init__(self):
        """Initialize the comprehensive validator."""
        self.rule_categories = {
            'basic_work': (1, 75),
            'code_review': (76, 99),
            'security_privacy': (100, 131),
            'logging': (132, 149),
            'error_handling': (150, 180),
            'typescript': (181, 215),
            'storage_governance': (216, 228),
            'gsmd': (232, 252),
            'simple_readability': (253, 280)
        }
        
        # Initialize rule validators
        self._init_rule_validators()
    
    def _init_rule_validators(self):
        """Initialize all rule category validators."""
        self.validators = {
            'basic_work': self._validate_basic_work_rules,
            'code_review': self._validate_code_review_rules,
            'security_privacy': self._validate_security_privacy_rules,
            'logging': self._validate_logging_rules,
            'error_handling': self._validate_error_handling_rules,
            'typescript': self._validate_typescript_rules,
            'storage_governance': self._validate_storage_governance_rules,
            'gsmd': self._validate_gsmd_rules,
            'simple_readability': self._validate_simple_readability_rules
        }
    
    def validate_prompt(self, prompt: str, file_type: str = None, task_type: str = None) -> List[Violation]:
        """
        Validate prompt against ALL 280 Constitution rules.
        
        Args:
            prompt: The prompt to validate
            file_type: Type of file being generated (python, typescript, etc.)
            task_type: Type of task (api, storage, logging, etc.)
            
        Returns:
            List of violations found in the prompt
        """
        violations = []
        
        # Always validate basic work rules (1-75)
        violations.extend(self._validate_basic_work_rules(prompt))
        
        # Always validate code review rules (76-99)
        violations.extend(self._validate_code_review_rules(prompt))
        
        # Always validate security/privacy rules (100-131)
        violations.extend(self._validate_security_privacy_rules(prompt))
        
        # Always validate logging rules (132-149)
        violations.extend(self._validate_logging_rules(prompt))
        
        # Always validate error handling rules (150-180)
        violations.extend(self._validate_error_handling_rules(prompt))
        
        # Context-specific validations
        if file_type and file_type.lower() in ['typescript', 'ts']:
            violations.extend(self._validate_typescript_rules(prompt))
        
        if task_type and 'storage' in task_type.lower():
            violations.extend(self._validate_storage_governance_rules(prompt))
        
        if task_type and 'policy' in task_type.lower():
            violations.extend(self._validate_gsmd_rules(prompt))
        
        # Always validate simple readability rules (253-280)
        violations.extend(self._validate_simple_readability_rules(prompt))
        
        return violations
    
    def _validate_basic_work_rules(self, prompt: str) -> List[Violation]:
        """Validate Basic Work Rules (1-75)."""
        violations = []
        
        # Rule 1: Do exactly what's asked
        if self._detects_additions_beyond_request(prompt):
            violations.append(Violation(
                rule_id='R001',
                severity=Severity.ERROR,
                message="Prompt requests additions beyond what's asked (Rule 1 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        # Rule 2: Only use information you're given
        if self._detects_guessing_or_assumptions(prompt):
            violations.append(Violation(
                rule_id='R002',
                severity=Severity.ERROR,
                message="Prompt may involve guessing or assumptions (Rule 2 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        # Rule 3: Protect people's privacy
        if self._detects_privacy_violations(prompt):
            violations.append(Violation(
                rule_id='R003',
                severity=Severity.ERROR,
                message="Prompt may expose sensitive information (Rule 3 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        # Rule 4: Use settings files, not hardcoded numbers
        if self._detects_hardcoded_values(prompt):
            violations.append(Violation(
                rule_id='R004',
                severity=Severity.ERROR,
                message="Prompt may use hardcoded values instead of settings (Rule 4 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        # Rule 6: Never break things during updates
        if self._detects_breaking_changes(prompt):
            violations.append(Violation(
                rule_id='R006',
                severity=Severity.ERROR,
                message="Prompt may cause breaking changes (Rule 6 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        return violations
    
    def _validate_code_review_rules(self, prompt: str) -> List[Violation]:
        """Validate Code Review Rules (76-99)."""
        violations = []
        
        # Rule 83: Automation (CI/Pre-commit)
        if self._detects_manual_processes(prompt):
            violations.append(Violation(
                rule_id='R083',
                severity=Severity.ERROR,
                message="Prompt requests manual processes instead of automation (Rule 83 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        # Rule 86: Python quality gates
        if 'python' in prompt.lower() and not self._detects_quality_gates(prompt):
            violations.append(Violation(
                rule_id='R086',
                severity=Severity.ERROR,
                message="Python code must include quality gates (lint, type, test) (Rule 86 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        # Rule 87: TypeScript quality gates
        if 'typescript' in prompt.lower() and not self._detects_typescript_quality_gates(prompt):
            violations.append(Violation(
                rule_id='R087',
                severity=Severity.ERROR,
                message="TypeScript code must include quality gates (Rule 87 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        return violations
    
    def _validate_security_privacy_rules(self, prompt: str) -> List[Violation]:
        """Validate Security & Privacy Rules (100-131)."""
        violations = []
        
        # Rule 90: Security & secrets
        if self._detects_secrets_in_code(prompt):
            violations.append(Violation(
                rule_id='R090',
                severity=Severity.ERROR,
                message="Prompt may expose secrets in code (Rule 90 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        # Rule 100: Security & privacy
        if self._detects_privacy_risks(prompt):
            violations.append(Violation(
                rule_id='R100',
                severity=Severity.ERROR,
                message="Prompt may create privacy risks (Rule 100 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        return violations
    
    def _validate_logging_rules(self, prompt: str) -> List[Violation]:
        """Validate Logging Rules (132-149)."""
        violations = []
        
        # Rule 132: Log format & transport
        if 'log' in prompt.lower() and not self._detects_structured_logging(prompt):
            violations.append(Violation(
                rule_id='R132',
                severity=Severity.ERROR,
                message="Logging must be structured JSON (Rule 132 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        # Rule 133: Required fields
        if 'log' in prompt.lower() and not self._detects_required_log_fields(prompt):
            violations.append(Violation(
                rule_id='R133',
                severity=Severity.ERROR,
                message="Logs must include required fields (Rule 133 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        return violations
    
    def _validate_error_handling_rules(self, prompt: str) -> List[Violation]:
        """Validate Error Handling Rules (150-180)."""
        violations = []
        
        # Rule 150: Prevent first
        if self._detects_reactive_error_handling(prompt):
            violations.append(Violation(
                rule_id='R150',
                severity=Severity.ERROR,
                message="Error handling should be preventive, not reactive (Rule 150 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        # Rule 155: No silent catches
        if self._detects_silent_error_handling(prompt):
            violations.append(Violation(
                rule_id='R155',
                severity=Severity.ERROR,
                message="No silent error handling allowed (Rule 155 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        return violations
    
    def _validate_typescript_rules(self, prompt: str) -> List[Violation]:
        """Validate TypeScript Rules (181-215)."""
        violations = []
        
        # Rule 181: Strict mode always
        if 'typescript' in prompt.lower() and not self._detects_strict_mode(prompt):
            violations.append(Violation(
                rule_id='R181',
                severity=Severity.ERROR,
                message="TypeScript must use strict mode (Rule 181 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        # Rule 182: No 'any' in committed code
        if self._detects_any_type_usage(prompt):
            violations.append(Violation(
                rule_id='R182',
                severity=Severity.ERROR,
                message="No 'any' type allowed in TypeScript (Rule 182 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        return violations
    
    def _validate_storage_governance_rules(self, prompt: str) -> List[Violation]:
        """Validate Storage Governance Rules (216-228)."""
        violations = []
        
        # Rule 216: Kebab-case naming
        if 'storage' in prompt.lower() and self._detects_non_kebab_case(prompt):
            violations.append(Violation(
                rule_id='R216',
                severity=Severity.ERROR,
                message="Storage paths must use kebab-case (Rule 216 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        # Rule 217: No source code/PII in stores
        if self._detects_code_or_pii_in_storage(prompt):
            violations.append(Violation(
                rule_id='R217',
                severity=Severity.ERROR,
                message="No source code or PII in storage (Rule 217 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        return violations
    
    def _validate_gsmd_rules(self, prompt: str) -> List[Violation]:
        """Validate GSMD Rules (232-252)."""
        violations = []
        
        # Rule 232: GSMD source of truth paths
        if 'policy' in prompt.lower() and not self._detects_gsmd_paths(prompt):
            violations.append(Violation(
                rule_id='R232',
                severity=Severity.ERROR,
                message="GSMD must use correct source of truth paths (Rule 232 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        return violations
    
    def _validate_simple_readability_rules(self, prompt: str) -> List[Violation]:
        """Validate Simple Code Readability Rules (253-280)."""
        violations = []
        
        # Rule 253: Plain English variable names
        if self._detects_abbreviations(prompt):
            violations.append(Violation(
                rule_id='R253',
                severity=Severity.ERROR,
                message="Variable names must be plain English (Rule 253 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        # Rule 270: NO advanced programming concepts
        if self._detects_advanced_concepts(prompt):
            violations.append(Violation(
                rule_id='R270',
                severity=Severity.ERROR,
                message="Advanced programming concepts are banned (Rule 270 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        # Rule 271: NO complex data structures
        if self._detects_complex_data_structures(prompt):
            violations.append(Violation(
                rule_id='R271',
                severity=Severity.ERROR,
                message="Complex data structures are banned (Rule 271 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        # Rule 272: NO advanced string manipulation
        if self._detects_advanced_string_manipulation(prompt):
            violations.append(Violation(
                rule_id='R272',
                severity=Severity.ERROR,
                message="Advanced string manipulation is banned (Rule 272 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        # Rule 280: ENFORCE Simple Level
        if self._detects_complex_code(prompt):
            violations.append(Violation(
                rule_id='R280',
                severity=Severity.ERROR,
                message="Code must be understandable by an 8th grader (Rule 280 violation)",
                file_path="prompt",
                line_number=1
            ))
        
        return violations
    
    # Detection helper methods
    def _detects_additions_beyond_request(self, prompt: str) -> bool:
        """Detect if prompt requests additions beyond what's asked."""
        addition_indicators = [
            "also add", "also include", "also create", "bonus", "extra",
            "additionally", "furthermore", "moreover", "plus"
        ]
        return any(indicator in prompt.lower() for indicator in addition_indicators)
    
    def _detects_guessing_or_assumptions(self, prompt: str) -> bool:
        """Detect if prompt involves guessing or assumptions."""
        assumption_indicators = [
            "assume", "guess", "probably", "likely", "maybe", "perhaps",
            "I think", "probably should", "might be"
        ]
        return any(indicator in prompt.lower() for indicator in assumption_indicators)
    
    def _detects_privacy_violations(self, prompt: str) -> bool:
        """Detect potential privacy violations."""
        privacy_risks = [
            "password", "secret", "private", "personal", "sensitive",
            "ssn", "social security", "credit card", "bank account"
        ]
        return any(risk in prompt.lower() for risk in privacy_risks)
    
    def _detects_hardcoded_values(self, prompt: str) -> bool:
        """Detect hardcoded values instead of settings."""
        # Look for numbers that might be hardcoded
        numbers = re.findall(r'\b\d+\b', prompt)
        return len(numbers) > 3 and "config" not in prompt.lower() and "setting" not in prompt.lower()
    
    def _detects_breaking_changes(self, prompt: str) -> bool:
        """Detect potential breaking changes."""
        breaking_indicators = [
            "remove", "delete", "deprecate", "breaking", "incompatible",
            "migrate", "upgrade", "version bump"
        ]
        return any(indicator in prompt.lower() for indicator in breaking_indicators)
    
    def _detects_manual_processes(self, prompt: str) -> bool:
        """Detect manual processes instead of automation."""
        manual_indicators = [
            "manually", "by hand", "manual", "step by step", "one by one"
        ]
        return any(indicator in prompt.lower() for indicator in manual_indicators)
    
    def _detects_quality_gates(self, prompt: str) -> bool:
        """Detect if quality gates are mentioned."""
        quality_indicators = [
            "lint", "type", "test", "coverage", "quality", "gate",
            "ruff", "black", "mypy", "pytest"
        ]
        return any(indicator in prompt.lower() for indicator in quality_indicators)
    
    def _detects_typescript_quality_gates(self, prompt: str) -> bool:
        """Detect TypeScript quality gates."""
        ts_quality_indicators = [
            "eslint", "prettier", "tsconfig", "strict", "typecheck"
        ]
        return any(indicator in prompt.lower() for indicator in ts_quality_indicators)
    
    def _detects_secrets_in_code(self, prompt: str) -> bool:
        """Detect secrets in code."""
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]
        return any(re.search(pattern, prompt, re.IGNORECASE) for pattern in secret_patterns)
    
    def _detects_privacy_risks(self, prompt: str) -> bool:
        """Detect privacy risks."""
        privacy_risks = [
            "log user data", "store personal", "track user", "collect data",
            "user information", "personal data"
        ]
        return any(risk in prompt.lower() for risk in privacy_risks)
    
    def _detects_structured_logging(self, prompt: str) -> bool:
        """Detect structured logging requirements."""
        structured_indicators = [
            "json", "structured", "log_schema", "traceId", "spanId"
        ]
        return any(indicator in prompt.lower() for indicator in structured_indicators)
    
    def _detects_required_log_fields(self, prompt: str) -> bool:
        """Detect required log fields."""
        required_fields = [
            "timestamp", "level", "service", "traceId", "requestId"
        ]
        return any(field in prompt.lower() for field in required_fields)
    
    def _detects_reactive_error_handling(self, prompt: str) -> bool:
        """Detect reactive error handling."""
        reactive_indicators = [
            "catch error", "handle exception", "try catch", "error handling"
        ]
        return any(indicator in prompt.lower() for indicator in reactive_indicators)
    
    def _detects_silent_error_handling(self, prompt: str) -> bool:
        """Detect silent error handling."""
        silent_indicators = [
            "silent", "ignore", "pass", "continue", "no error"
        ]
        return any(indicator in prompt.lower() for indicator in silent_indicators)
    
    def _detects_strict_mode(self, prompt: str) -> bool:
        """Detect TypeScript strict mode."""
        return "strict" in prompt.lower() or "tsconfig" in prompt.lower()
    
    def _detects_any_type_usage(self, prompt: str) -> bool:
        """Detect 'any' type usage."""
        return "any" in prompt.lower() and "typescript" in prompt.lower()
    
    def _detects_non_kebab_case(self, prompt: str) -> bool:
        """Detect non-kebab-case naming."""
        # Look for camelCase or snake_case in storage contexts
        camel_case = re.search(r'[a-z]+[A-Z][a-z]+', prompt)
        snake_case = re.search(r'[a-z]+_[a-z]+', prompt)
        return bool(camel_case or snake_case)
    
    def _detects_code_or_pii_in_storage(self, prompt: str) -> bool:
        """Detect code or PII in storage."""
        storage_risks = [
            "store code", "save source", "database code", "store personal"
        ]
        return any(risk in prompt.lower() for risk in storage_risks)
    
    def _detects_gsmd_paths(self, prompt: str) -> bool:
        """Detect GSMD source of truth paths."""
        gsmd_indicators = [
            "policy", "governance", "gsmd", "config/policy"
        ]
        return any(indicator in prompt.lower() for indicator in gsmd_indicators)
    
    def _detects_abbreviations(self, prompt: str) -> bool:
        """Detect abbreviations in variable names."""
        abbreviations = [
            "usr", "ctx", "mgr", "calc", "cfg", "conn", "pool", "proc", "temp", "var"
        ]
        return any(abbrev in prompt.lower() for abbrev in abbreviations)
    
    def _detects_advanced_concepts(self, prompt: str) -> bool:
        """Detect advanced programming concepts."""
        advanced_concepts = [
            "lambda", "closure", "decorator", "async", "await", "generator",
            "promise", "callback", "map", "filter", "reduce", "fold",
            "inheritance", "polymorphism", "abstract", "singleton", "factory"
        ]
        return any(concept in prompt.lower() for concept in advanced_concepts)
    
    def _detects_complex_data_structures(self, prompt: str) -> bool:
        """Detect complex data structures."""
        complex_structures = [
            "nested object", "hash map", "linked list", "tree", "graph",
            "array of objects", "complex object", "nested array"
        ]
        return any(structure in prompt.lower() for structure in complex_structures)
    
    def _detects_advanced_string_manipulation(self, prompt: str) -> bool:
        """Detect advanced string manipulation."""
        advanced_string = [
            "regex", "regular expression", "encoding", "decoding", "base64",
            "template literal", "string interpolation"
        ]
        return any(technique in prompt.lower() for technique in advanced_string)
    
    def _detects_complex_code(self, prompt: str) -> bool:
        """Detect complex code that 8th grader can't understand."""
        complexity_indicators = [
            "complex", "advanced", "sophisticated", "intricate", "elaborate",
            "recursive", "algorithm", "optimization", "performance"
        ]
        return any(indicator in prompt.lower() for indicator in complexity_indicators)


class ContextAwareRuleLoader:
    """
    Loads relevant Constitution rules based on context.
    
    This ensures only relevant rules are applied to specific file types and tasks.
    """
    
    def __init__(self):
        """Initialize the context-aware rule loader."""
        self.rule_categories = {
            'basic_work': (1, 75),
            'code_review': (76, 99),
            'security_privacy': (100, 131),
            'logging': (132, 149),
            'error_handling': (150, 180),
            'typescript': (181, 215),
            'storage_governance': (216, 228),
            'gsmd': (232, 252),
            'simple_readability': (253, 280)
        }
    
    def get_relevant_rules(self, file_type: str = None, task_type: str = None, 
                          prompt: str = None) -> List[str]:
        """
        Get relevant rules for current context.
        
        Args:
            file_type: Type of file being generated
            task_type: Type of task being performed
            prompt: The prompt being validated
            
        Returns:
            List of relevant rule categories
        """
        relevant_categories = []
        
        # Always include basic work rules
        relevant_categories.append('basic_work')
        
        # Always include code review rules
        relevant_categories.append('code_review')
        
        # Always include security/privacy rules
        relevant_categories.append('security_privacy')
        
        # Always include simple readability rules
        relevant_categories.append('simple_readability')
        
        # Context-specific rules
        if file_type:
            if file_type.lower() in ['typescript', 'ts', 'js']:
                relevant_categories.append('typescript')
        
        if task_type:
            if 'storage' in task_type.lower():
                relevant_categories.append('storage_governance')
            if 'policy' in task_type.lower() or 'governance' in task_type.lower():
                relevant_categories.append('gsmd')
            if 'log' in task_type.lower():
                relevant_categories.append('logging')
            if 'error' in task_type.lower():
                relevant_categories.append('error_handling')
        
        if prompt:
            if 'log' in prompt.lower():
                relevant_categories.append('logging')
            if 'error' in prompt.lower() or 'exception' in prompt.lower():
                relevant_categories.append('error_handling')
            if 'storage' in prompt.lower() or 'file' in prompt.lower():
                relevant_categories.append('storage_governance')
            if 'policy' in prompt.lower() or 'governance' in prompt.lower():
                relevant_categories.append('gsmd')
        
        return relevant_categories
    
    def get_rule_range(self, category: str) -> tuple:
        """Get rule range for a category."""
        return self.rule_categories.get(category, (0, 0))
    
    def get_all_rules(self) -> List[str]:
        """Get all rule categories."""
        return list(self.rule_categories.keys())


class PreImplementationHookManager:
    """
    Manages Pre-Implementation Hooks for comprehensive Constitution rule enforcement.
    """
    
    def __init__(self):
        """Initialize the hook manager."""
        self.validator = ComprehensivePreImplementationValidator()
        self.rule_loader = ContextAwareRuleLoader()
    
    def validate_before_generation(self, prompt: str, file_type: str = None, 
                                 task_type: str = None) -> Dict[str, Any]:
        """
        Validate prompt before AI code generation.
        
        Args:
            prompt: The prompt to validate
            file_type: Type of file being generated
            task_type: Type of task being performed
            
        Returns:
            Validation result with violations and recommendations
        """
        # Get relevant rule categories
        relevant_categories = self.rule_loader.get_relevant_rules(
            file_type, task_type, prompt
        )
        
        # Validate against relevant rules
        violations = self.validator.validate_prompt(prompt, file_type, task_type)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(violations, relevant_categories)
        
        return {
            'valid': len(violations) == 0,
            'violations': violations,
            'recommendations': recommendations,
            'relevant_categories': relevant_categories,
            'total_rules_checked': sum(
                self.rule_loader.get_rule_range(cat)[1] - self.rule_loader.get_rule_range(cat)[0] + 1
                for cat in relevant_categories
            )
        }
    
    def _generate_recommendations(self, violations: List[Violation], 
                                categories: List[str]) -> List[str]:
        """Generate recommendations based on violations."""
        recommendations = []
        
        for violation in violations:
            rule_id = violation.rule_id
            
            if rule_id.startswith('R253'):
                recommendations.append("Use plain English variable names instead of abbreviations")
            elif rule_id.startswith('R270'):
                recommendations.append("Avoid advanced programming concepts - use simple alternatives")
            elif rule_id.startswith('R271'):
                recommendations.append("Use simple data structures instead of complex ones")
            elif rule_id.startswith('R272'):
                recommendations.append("Use basic string operations instead of advanced manipulation")
            elif rule_id.startswith('R003'):
                recommendations.append("Remove any sensitive information from the prompt")
            elif rule_id.startswith('R004'):
                recommendations.append("Use configuration files instead of hardcoded values")
            else:
                recommendations.append(f"Review {rule_id} requirements and adjust prompt accordingly")
        
        return recommendations
