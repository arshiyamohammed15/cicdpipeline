"""
Pre-Implementation Hooks for Constitution Rules

This module provides comprehensive validation of prompts before AI code generation,
ensuring ALL Constitution rules from docs/constitution JSON files (single source of truth)
are enforced at the source rather than after generation.

Rule counts are dynamically loaded from docs/constitution/*.json files.
No hardcoded rule counts exist in this module.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from validator.models import Violation, Severity


class ConstitutionRuleLoader:
    """
    Loads all constitution rules from JSON files in docs/constitution folder.
    """

    def __init__(self, constitution_dir: str = "docs/constitution"):
        """
        Initialize the rule loader.

        Args:
            constitution_dir: Path to directory containing constitution JSON files
        """
        self.constitution_dir = Path(constitution_dir)
        self.rules: List[Dict[str, Any]] = []
        self.rules_by_id: Dict[str, Dict[str, Any]] = {}
        self.rules_by_category: Dict[str, List[Dict[str, Any]]] = {}
        self._load_all_rules()

    def _load_all_rules(self):
        """Load all rules from all JSON files in constitution directory."""
        if not self.constitution_dir.exists():
            raise FileNotFoundError(f"Constitution directory not found: {self.constitution_dir}")

        json_files = sorted(list(self.constitution_dir.glob("*.json")))

        if not json_files:
            raise FileNotFoundError(f"No JSON files found in {self.constitution_dir}")

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    rules = data.get('constitution_rules', [])

                    for rule in rules:
                        if rule.get('enabled', True):
                            rule_id = rule.get('rule_id', '')
                            self.rules.append(rule)
                            self.rules_by_id[rule_id] = rule

                            category = rule.get('category', 'UNKNOWN')
                            if category not in self.rules_by_category:
                                self.rules_by_category[category] = []
                            self.rules_by_category[category].append(rule)

            except Exception as e:
                print(f"Warning: Could not load rules from {json_file}: {e}")
                continue

    def get_all_rules(self) -> List[Dict[str, Any]]:
        """Get all loaded rules."""
        return self.rules

    def get_rule_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific rule by its ID."""
        return self.rules_by_id.get(rule_id)

    def get_rules_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all rules in a specific category."""
        return self.rules_by_category.get(category, [])

    def get_total_rule_count(self) -> int:
        """Get total number of loaded rules."""
        return len(self.rules)


class PromptValidator:
    """
    Validates prompts against constitution rules.
    """

    def __init__(self, rule_loader: ConstitutionRuleLoader):
        """
        Initialize the prompt validator.

        Args:
            rule_loader: Loaded rule loader instance
        """
        self.rule_loader = rule_loader

    def validate_prompt(self, prompt: str, file_type: str = None, task_type: str = None) -> List[Violation]:
        """
        Validate a prompt against all relevant constitution rules.

        Args:
            prompt: The prompt to validate
            file_type: Type of file being generated (python, typescript, etc.)
            task_type: Type of task (api, storage, logging, etc.)

        Returns:
            List of violations found
        """
        violations = []
        prompt_lower = prompt.lower()

        # Get all enabled rules
        all_rules = self.rule_loader.get_all_rules()

        for rule in all_rules:
            rule_id = rule.get('rule_id', '')
            title = rule.get('title', '')
            category = rule.get('category', '')
            description = rule.get('description', '')
            requirements = rule.get('requirements', [])
            severity_str = rule.get('severity_level', 'Major')

            # Check if rule is applicable to this context
            if not self._is_rule_applicable(rule, file_type, task_type, prompt_lower):
                continue

            # Validate prompt against rule
            violation = self._check_rule_violation(rule, prompt, prompt_lower, file_type, task_type)

            if violation:
                violations.append(violation)

        return violations

    def _is_rule_applicable(self, rule: Dict[str, Any], file_type: str, task_type: str, prompt_lower: str) -> bool:
        """
        Determine if a rule is applicable to the current context.

        Args:
            rule: The rule to check
            file_type: Type of file being generated
            task_type: Type of task
            prompt_lower: Lowercase prompt for keyword matching

        Returns:
            True if rule is applicable
        """
        category = rule.get('category', '').upper()
        rule_id = rule.get('rule_id', '').upper()

        # Always check all rules - no filtering by context
        # This ensures all rules from source of truth are validated
        return True

    def _check_rule_violation(self, rule: Dict[str, Any], prompt: str, prompt_lower: str,
                             file_type: str, task_type: str) -> Optional[Violation]:
        """
        Check if prompt violates a specific rule.

        Args:
            rule: The rule to check against
            prompt: Original prompt
            prompt_lower: Lowercase prompt
            file_type: Type of file
            task_type: Type of task

        Returns:
            Violation if found, None otherwise
        """
        rule_id = rule.get('rule_id', '')
        title = rule.get('title', '')
        description = rule.get('description', '')
        requirements = rule.get('requirements', [])
        category = rule.get('category', '')
        severity_str = rule.get('severity_level', 'Major')

        # Map severity levels
        severity_map = {
            'Blocker': Severity.ERROR,
            'Critical': Severity.ERROR,
            'Major': Severity.ERROR,
            'Minor': Severity.WARNING,
            'Info': Severity.INFO
        }
        severity = severity_map.get(severity_str, Severity.ERROR)

        # Rule-specific validation patterns
        violation_indicators = self._get_violation_indicators(rule, prompt_lower)

        if violation_indicators:
            # Extract rule number if available (e.g., R-001 -> 1)
            rule_number = None
            if rule_id.startswith('R-'):
                try:
                    rule_number = int(rule_id.split('-')[1])
                except:
                    pass

            return Violation(
                rule_id=rule_id,
                severity=severity,
                message=f"Prompt violates {rule_id}: {title}",
                file_path="prompt",
                line_number=1,
                code_snippet=prompt[:200] + "..." if len(prompt) > 200 else prompt,
                fix_suggestion=self._generate_fix_suggestion(rule, requirements),
                category=category,
                rule_name=title,
                rule_number=rule_number
            )

        return None

    def _get_violation_indicators(self, rule: Dict[str, Any], prompt_lower: str) -> bool:
        """
        Detect violation indicators based on rule content from single source of truth.

        This method dynamically validates ALL rules by parsing their actual content
        (description, requirements, title) rather than using hardcoded patterns.

        Args:
            rule: The rule to check (from docs/constitution/*.json)
            prompt_lower: Lowercase prompt text

        Returns:
            True if violation detected, False otherwise
        """
        rule_id = rule.get('rule_id', '').upper()
        title = rule.get('title', '').upper()
        description = rule.get('description', '').lower()
        requirements = rule.get('requirements', [])
        category = rule.get('category', '').upper()
        error_condition = rule.get('error_condition', '')

        # Combine all rule text for comprehensive analysis
        all_rule_text = ' '.join([
            title.lower(),
            description,
            ' '.join([str(r).lower() for r in requirements if r]),
            error_condition.lower() if error_condition else ''
        ])

        # Extract prohibited terms and patterns from rule content
        prohibited_terms = self._extract_prohibited_terms_from_rule(rule, all_rule_text)

        # Extract required terms that must be present
        required_terms = self._extract_required_terms_from_rule(rule, all_rule_text)

        # Check for prohibited terms in prompt
        if prohibited_terms:
            for term in prohibited_terms:
                if term in prompt_lower:
                    return True

        # Check for missing required terms (if rule mandates them)
        if required_terms and self._is_requirement_mandatory(all_rule_text):
            # Check if prompt context matches rule context
            if self._is_prompt_relevant_to_rule(rule, prompt_lower, all_rule_text):
                # If relevant but missing required terms, it's a violation
                if not any(term in prompt_lower for term in required_terms):
                    return True

        # Check for explicit violation patterns in rule description
        violation_patterns = self._extract_violation_patterns(all_rule_text)
        for pattern in violation_patterns:
            if pattern in prompt_lower:
                return True

        # Check for category-specific violations
        if self._check_category_specific_violations(rule, prompt_lower, category, all_rule_text):
            return True

        # Check for rule-specific patterns based on rule_id prefixes
        if self._check_rule_id_specific_violations(rule_id, rule, prompt_lower, all_rule_text):
            return True

        return False

    def _extract_prohibited_terms_from_rule(self, rule: Dict[str, Any], all_rule_text: str) -> List[str]:
        """
        Extract prohibited terms from rule content (description, requirements, title).

        Args:
            rule: The rule dictionary
            all_rule_text: Combined text from title, description, requirements

        Returns:
            List of prohibited terms/phrases to check in prompts
        """
        prohibited = []
        rule_text_lower = all_rule_text.lower()

        # Extract explicit prohibitions
        prohibition_keywords = [
            'must not', 'prohibited', 'forbidden', 'disallow', 'never',
            'do not', "don't", 'avoid', 'prevent', 'ban', 'restrict'
        ]

        # Find sentences/phrases with prohibition keywords
        sentences = re.split(r'[.!?;]\s+', rule_text_lower)
        for sentence in sentences:
            for keyword in prohibition_keywords:
                if keyword in sentence:
                    # Extract the prohibited item from the sentence
                    # Look for common patterns: "must not [verb] [noun]", "prohibited [noun]", etc.
                    prohibited_items = self._extract_prohibited_items_from_sentence(sentence, keyword)
                    prohibited.extend(prohibited_items)

        # Extract common prohibited patterns from rule content
        if 'hardcoded' in rule_text_lower:
            prohibited.extend(['hardcoded password', 'hardcoded secret', 'hardcoded key',
                             'hardcoded token', 'hardcoded api key', 'hardcoded credential'])

        if 'cache' in rule_text_lower and ('disable' in rule_text_lower or 'purge' in rule_text_lower):
            prohibited.extend(['cache', 'caching', 'test cache', 'framework cache'])

        if 'any type' in rule_text_lower or "'any'" in rule_text_lower or 'any:' in rule_text_lower:
            prohibited.extend([': any', 'any[]', 'any>', '<any'])

        if 'privacy' in rule_text_lower or 'personal information' in rule_text_lower:
            prohibited.extend(['password', 'secret', 'api key', 'private key', 'ssn',
                             'credit card', 'ssn', 'social security', 'personal data'])

        if 'assume' in rule_text_lower or 'guess' in rule_text_lower:
            prohibited.extend(['assume', 'guess', 'probably', 'maybe', 'perhaps', 'likely'])

        if 'network' in rule_text_lower and 'not access' in rule_text_lower:
            prohibited.extend(['network', 'http', 'fetch', 'request', 'api call'])

        if 'system clock' in rule_text_lower and 'not access' in rule_text_lower:
            prohibited.extend(['datetime.now', 'time.now', 'date.now', 'system time'])

        if 'global state' in rule_text_lower and 'not access' in rule_text_lower:
            prohibited.extend(['global', 'singleton', 'static variable'])

        # Remove duplicates and empty strings
        prohibited = list(dict.fromkeys([p.strip() for p in prohibited if p.strip()]))

        return prohibited

    def _extract_prohibited_items_from_sentence(self, sentence: str, keyword: str) -> List[str]:
        """Extract what is prohibited from a sentence containing a prohibition keyword."""
        items = []

        # Pattern: "must not [verb] [noun]" or "prohibited [noun]"
        patterns = [
            r'must not\s+(\w+(?:\s+\w+){0,3})',
            r'prohibited\s+(\w+(?:\s+\w+){0,3})',
            r'forbidden\s+(\w+(?:\s+\w+){0,3})',
            r'never\s+(\w+(?:\s+\w+){0,3})',
            r'do not\s+(\w+(?:\s+\w+){0,3})',
            r"don't\s+(\w+(?:\s+\w+){0,3})",
            r'avoid\s+(\w+(?:\s+\w+){0,3})',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, sentence, re.IGNORECASE)
            items.extend(matches)

        return items

    def _extract_required_terms_from_rule(self, rule: Dict[str, Any], all_rule_text: str) -> List[str]:
        """
        Extract required terms that must be present when rule is applicable.

        Args:
            rule: The rule dictionary
            all_rule_text: Combined text from title, description, requirements

        Returns:
            List of required terms/phrases
        """
        required = []
        rule_text_lower = all_rule_text.lower()

        # Extract explicit requirements
        requirement_keywords = ['must', 'required', 'shall', 'need', 'mandatory', 'enforce']

        # Find sentences with requirement keywords
        sentences = re.split(r'[.!?;]\s+', rule_text_lower)
        for sentence in sentences:
            for keyword in requirement_keywords:
                if keyword in sentence:
                    # Extract the required item
                    required_items = self._extract_required_items_from_sentence(sentence, keyword)
                    required.extend(required_items)

        # Extract common required patterns
        if 'structured' in rule_text_lower or 'json' in rule_text_lower:
            if 'log' in rule_text_lower:
                required.extend(['structured log', 'json log', 'jsonl'])

        if 'schema version' in rule_text_lower:
            required.append('schema_version')

        if 'iso-8601' in rule_text_lower or 'timestamp' in rule_text_lower:
            required.extend(['iso-8601', 'timestamp', 'utc'])

        if 'deterministic' in rule_text_lower and 'test' in rule_text_lower:
            required.append('deterministic')

        if 'disable cache' in rule_text_lower or 'purge cache' in rule_text_lower:
            required.extend(['disable cache', 'no cache', 'purge cache'])

        # Remove duplicates and empty strings
        required = list(dict.fromkeys([r.strip() for r in required if r.strip()]))

        return required

    def _extract_required_items_from_sentence(self, sentence: str, keyword: str) -> List[str]:
        """Extract what is required from a sentence containing a requirement keyword."""
        items = []

        # Pattern: "must [verb] [noun]" or "required [noun]"
        patterns = [
            r'must\s+(\w+(?:\s+\w+){0,3})',
            r'required\s+(\w+(?:\s+\w+){0,3})',
            r'shall\s+(\w+(?:\s+\w+){0,3})',
            r'need\s+(\w+(?:\s+\w+){0,3})',
            r'mandatory\s+(\w+(?:\s+\w+){0,3})',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, sentence, re.IGNORECASE)
            items.extend(matches)

        return items

    def _is_requirement_mandatory(self, all_rule_text: str) -> bool:
        """Check if the rule has mandatory requirements (not just recommendations)."""
        mandatory_keywords = ['must', 'required', 'shall', 'mandatory', 'enforce', 'prohibit']
        return any(keyword in all_rule_text.lower() for keyword in mandatory_keywords)

    def _is_prompt_relevant_to_rule(self, rule: Dict[str, Any], prompt_lower: str, all_rule_text: str) -> bool:
        """Check if prompt is relevant to this rule's context."""
        # Extract context keywords from rule
        context_keywords = []

        # Get keywords from category
        category = rule.get('category', '').lower()
        if category:
            context_keywords.extend(category.split())

        # Get keywords from title
        title = rule.get('title', '').lower()
        if title:
            # Extract meaningful words (skip common words)
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            title_words = [w for w in title.split() if w not in stop_words and len(w) > 2]
            context_keywords.extend(title_words)

        # Get keywords from description (first sentence)
        description = rule.get('description', '').lower()
        if description:
            first_sentence = description.split('.')[0]
            desc_words = [w for w in first_sentence.split() if w not in stop_words and len(w) > 3]
            context_keywords.extend(desc_words[:5])  # Limit to first 5 meaningful words

        # Check if prompt contains any context keywords
        if context_keywords:
            return any(keyword in prompt_lower for keyword in context_keywords if len(keyword) > 3)

        return True  # If no context keywords, assume relevant

    def _extract_violation_patterns(self, all_rule_text: str) -> List[str]:
        """Extract specific violation patterns from rule text."""
        patterns = []
        rule_text_lower = all_rule_text.lower()

        # Common violation indicators
        if 'error:' in rule_text_lower:
            # Extract error codes mentioned in rules
            error_matches = re.findall(r'error:(\w+)', rule_text_lower)
            patterns.extend([f'error:{code}' for code in error_matches])

        # Extract specific violation phrases
        violation_phrases = [
            'scope violation', 'size violation', 'diff complexity',
            'comment drift', 'schema violation', 'unstructured log'
        ]

        for phrase in violation_phrases:
            if phrase in rule_text_lower:
                patterns.append(phrase)

        return patterns

    def _check_category_specific_violations(self, rule: Dict[str, Any], prompt_lower: str,
                                           category: str, all_rule_text: str) -> bool:
        """Check for category-specific violation patterns."""
        category_lower = category.lower()

        # Security/Privacy category
        if 'security' in category_lower or 'privacy' in category_lower:
            security_risks = ['hardcoded password', 'secret in code', 'api key in code',
                            'private key', 'credential', 'token in code']
            if any(risk in prompt_lower for risk in security_risks):
                return True

        # Testing category
        if 'testing' in category_lower or 'test' in category_lower:
            # Check for test-related violations
            if 'test' in prompt_lower:
                # Check for cache-related violations
                if 'cache' in prompt_lower and 'disable' not in prompt_lower and 'purge' not in prompt_lower:
                    if 'disable cache' in all_rule_text or 'purge cache' in all_rule_text:
                        return True

                # Check for deterministic requirement
                if 'deterministic' in all_rule_text and 'deterministic' not in prompt_lower:
                    return True

                # Check for network/system access violations
                if 'not access network' in all_rule_text or 'no network' in all_rule_text:
                    if any(term in prompt_lower for term in ['http', 'fetch', 'request', 'api call']):
                        return True

        # Logging/Observability category
        if 'logging' in category_lower or 'observability' in category_lower or 'log' in category_lower:
            if 'log' in prompt_lower:
                # Check for structured logging requirement
                if 'structured' in all_rule_text or 'json' in all_rule_text:
                    if 'structured' not in prompt_lower and 'json' not in prompt_lower and 'jsonl' not in prompt_lower:
                        return True

                # Check for schema version requirement
                if 'schema version' in all_rule_text or 'schema_version' in all_rule_text:
                    if 'schema_version' not in prompt_lower and 'schema version' not in prompt_lower:
                        return True

        # Comments/Documentation category
        if 'comment' in category_lower or 'documentation' in category_lower:
            # Check if code generation requires documentation
            if 'function' in prompt_lower or 'class' in prompt_lower or 'method' in prompt_lower:
                if 'synchronize comments' in all_rule_text or 'update comments' in all_rule_text:
                    if 'comment' not in prompt_lower and 'document' not in prompt_lower:
                        return True

        # TypeScript category
        if 'typescript' in category_lower:
            if 'typescript' in prompt_lower or 'ts' in prompt_lower:
                # Check for 'any' type prohibition
                if 'any type' in all_rule_text or "'any'" in all_rule_text:
                    if 'any' in prompt_lower and 'strict' not in prompt_lower:
                        return True

        return False

    def _check_rule_id_specific_violations(self, rule_id: str, rule: Dict[str, Any],
                                          prompt_lower: str, all_rule_text: str) -> bool:
        """Check for rule ID prefix-specific violations."""
        # R-001: Do Exactly What's Asked
        if rule_id.startswith('R-001') or 'do exactly' in all_rule_text:
            if any(word in prompt_lower for word in ['also add', 'also include', 'bonus', 'extra', 'additionally']):
                return True

        # R-002: Only Use Information Given
        if rule_id.startswith('R-002') or 'only use information' in all_rule_text:
            if any(word in prompt_lower for word in ['assume', 'guess', 'probably', 'maybe', 'perhaps']):
                return True

        # R-004: Use Settings Files, Not Hardcoded Numbers
        if rule_id.startswith('R-004') or ('settings' in all_rule_text and 'hardcoded' in all_rule_text):
            numbers = re.findall(r'\b\d+\b', prompt_lower)
            if len(numbers) > 3 and 'config' not in prompt_lower and 'setting' not in prompt_lower:
                return True

        # TST-* or FTP-*: Testing rules
        if rule_id.startswith(('TST-', 'FTP-')):
            if 'test' in prompt_lower:
                # Check specific testing rule violations
                if 'deterministic' in all_rule_text and 'deterministic' not in prompt_lower:
                    return True
                if 'disable cache' in all_rule_text or 'purge cache' in all_rule_text:
                    if 'cache' in prompt_lower and 'disable' not in prompt_lower and 'purge' not in prompt_lower:
                        return True

        # DOC-*: Documentation/Comments rules
        if rule_id.startswith('DOC-'):
            if 'synchronize comments' in all_rule_text or 'update comments' in all_rule_text:
                if any(word in prompt_lower for word in ['function', 'class', 'method']):
                    if 'comment' not in prompt_lower and 'document' not in prompt_lower:
                        return True

        # OBS-*: Observability/Logging rules
        if rule_id.startswith('OBS-'):
            if 'log' in prompt_lower:
                if 'structured' in all_rule_text or 'json' in all_rule_text:
                    if 'structured' not in prompt_lower and 'json' not in prompt_lower:
                        return True

        return False

    def _generate_fix_suggestion(self, rule: Dict[str, Any], requirements: List[str]) -> str:
        """
        Generate a fix suggestion based on rule requirements.

        Args:
            rule: The violated rule
            requirements: List of requirements

        Returns:
            Fix suggestion text
        """
        if requirements:
            return f"Review rule requirements: {requirements[0][:100]}..."

        description = rule.get('description', '')
        if description:
            return f"Review rule description: {description[:100]}..."

        return f"Review rule {rule.get('rule_id', '')} requirements and adjust prompt accordingly."


class PreImplementationHookManager:
    """
    Manages Pre-Implementation Hooks for comprehensive Constitution rule enforcement.

    This class loads all rules from JSON files (single source of truth) and validates prompts before
    AI code generation occurs.

    Rule counts are dynamically calculated from docs/constitution/*.json files.
    No hardcoded rule counts exist in this class.
    """

    def __init__(self, constitution_dir: str = "docs/constitution"):
        """
        Initialize the hook manager.

        Args:
            constitution_dir: Path to directory containing constitution JSON files
        """
        self.rule_loader = ConstitutionRuleLoader(constitution_dir)
        self.validator = PromptValidator(self.rule_loader)
        self.total_rules = self.rule_loader.get_total_rule_count()

    def validate_before_generation(self, prompt: str, file_type: str = None,
                                 task_type: str = None) -> Dict[str, Any]:
        """
        Validate prompt before AI code generation.

        Args:
            prompt: The prompt to validate
            file_type: Type of file being generated (python, typescript, etc.)
            task_type: Type of task being performed (api, storage, logging, etc.)

        Returns:
            Validation result with violations and recommendations
        """
        # Validate prompt against all rules
        violations = self.validator.validate_prompt(prompt, file_type, task_type)

        # Generate recommendations
        recommendations = self._generate_recommendations(violations)

        # Get relevant categories
        relevant_categories = self._get_relevant_categories(prompt, file_type, task_type)

        # Sort violations by rule_id for deterministic ordering
        violations_sorted = sorted(violations, key=lambda v: (v.rule_id, v.message))

        return {
            'valid': len(violations) == 0,
            'violations': violations_sorted,
            'recommendations': recommendations,
            'relevant_categories': relevant_categories,
            'total_rules_checked': self.total_rules
        }

    def _generate_recommendations(self, violations: List[Violation]) -> List[str]:
        """
        Generate recommendations based on violations.

        Args:
            violations: List of violations found

        Returns:
            List of recommendation strings
        """
        recommendations = []

        for violation in violations:
            rule_id = violation.rule_id

            if violation.fix_suggestion:
                recommendations.append(violation.fix_suggestion)
            else:
                recommendations.append(f"Review {rule_id} requirements and adjust prompt accordingly.")

        # Remove duplicates and sort for deterministic ordering
        unique_recommendations = list(dict.fromkeys(recommendations))
        return sorted(unique_recommendations)

    def _get_relevant_categories(self, prompt: str, file_type: str, task_type: str) -> List[str]:
        """
        Get relevant rule categories based on context.

        Args:
            prompt: The prompt
            file_type: Type of file
            task_type: Type of task

        Returns:
            List of relevant category names
        """
        categories = set()
        prompt_lower = prompt.lower()

        # Add categories based on file type
        if file_type:
            if file_type.lower() in ['typescript', 'ts']:
                categories.add('TypeScript')
            elif file_type.lower() in ['python', 'py']:
                categories.add('Python')

        # Add categories based on task type
        if task_type:
            task_lower = task_type.lower()
            if 'test' in task_lower:
                categories.add('Testing')
            if 'log' in task_lower:
                categories.add('Logging')
            if 'api' in task_lower:
                categories.add('API')
            if 'storage' in task_lower:
                categories.add('Storage')

        # Add categories based on prompt content
        if 'test' in prompt_lower:
            categories.add('Testing')
        if 'log' in prompt_lower:
            categories.add('Logging')
        if 'typescript' in prompt_lower or 'ts' in prompt_lower:
            categories.add('TypeScript')
        if 'security' in prompt_lower or 'privacy' in prompt_lower:
            categories.add('Security')
        if 'comment' in prompt_lower or 'document' in prompt_lower:
            categories.add('Comments')

        # Always include basic work rules
        categories.add('Basic Work')

        return sorted(list(categories))
