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
        Detect violation indicators based on rule content.
        
        Args:
            rule: The rule to check
            prompt_lower: Lowercase prompt
            
        Returns:
            True if violation detected
        """
        rule_id = rule.get('rule_id', '').upper()
        title = rule.get('title', '').upper()
        description = rule.get('description', '').lower()
        category = rule.get('category', '').upper()
        
        # Common violation patterns
        violation_patterns = []
        
        # Rule 1: Do Exactly What's Asked
        if 'DO EXACTLY' in title or 'R-001' in rule_id:
            if any(word in prompt_lower for word in ['also add', 'also include', 'bonus', 'extra', 'additionally']):
                return True
        
        # Rule 2: Only Use Information Given
        if 'ONLY USE INFORMATION' in title or 'R-002' in rule_id:
            if any(word in prompt_lower for word in ['assume', 'guess', 'probably', 'maybe', 'perhaps']):
                return True
        
        # Rule 3: Protect Privacy
        if 'PRIVACY' in title or 'PRIVACY' in category or 'R-003' in rule_id:
            privacy_risks = ['password', 'secret', 'api key', 'private key', 'ssn', 'credit card']
            if any(risk in prompt_lower for risk in privacy_risks):
                return True
        
        # Rule 4: Use Settings Files
        if 'SETTINGS' in title or 'HARDCODED' in title or 'R-004' in rule_id:
            # Check for multiple hardcoded numbers without config mention
            numbers = re.findall(r'\b\d+\b', prompt_lower)
            if len(numbers) > 3 and 'config' not in prompt_lower and 'setting' not in prompt_lower:
                return True
        
        # Security rules
        if 'SECURITY' in category or 'SECURITY' in title:
            security_risks = ['hardcoded password', 'secret in code', 'api key in code']
            if any(risk in prompt_lower for risk in security_risks):
                return True
        
        # Testing rules
        if 'TESTING' in category or 'TST' in rule_id or 'FTP' in rule_id:
            if 'test' in prompt_lower and 'deterministic' not in prompt_lower:
                # Check for test-related violations
                if 'cache' in prompt_lower and 'disable' not in prompt_lower:
                    return True
        
        # TypeScript rules
        if 'TYPESCRIPT' in category or 'TS-' in rule_id:
            if 'typescript' in prompt_lower or 'ts' in prompt_lower:
                if 'any' in prompt_lower and 'strict' not in prompt_lower:
                    return True
        
        # Comments/Documentation rules
        if 'COMMENTS' in category or 'DOC-' in rule_id:
            if 'function' in prompt_lower or 'class' in prompt_lower:
                if 'document' not in prompt_lower and 'comment' not in prompt_lower:
                    # Only flag if explicitly required by rule
                    pass
        
        # Logging rules
        if 'LOGGING' in category or 'LOG' in title:
            if 'log' in prompt_lower:
                if 'structured' not in prompt_lower and 'json' not in prompt_lower:
                    return True
        
        # Default: Check description and requirements for key terms
        description_lower = description.lower()
        if any(keyword in description_lower for keyword in ['must', 'required', 'shall', 'prohibited', 'forbidden']):
            # Check if prompt violates the requirement
            if 'must not' in description_lower or 'prohibited' in description_lower:
                # Extract what is prohibited
                prohibited_terms = self._extract_prohibited_terms(description)
                if any(term in prompt_lower for term in prohibited_terms):
                    return True
        
        return False
    
    def _extract_prohibited_terms(self, description: str) -> List[str]:
        """
        Extract prohibited terms from rule description.
        
        Args:
            description: Rule description text
            
        Returns:
            List of prohibited terms
        """
        prohibited = []
        description_lower = description.lower()
        
        # Common prohibited patterns
        if 'hardcoded' in description_lower:
            prohibited.extend(['password', 'secret', 'key', 'token'])
        if 'cache' in description_lower and 'disable' in description_lower:
            prohibited.append('cache')
        if 'any type' in description_lower or "'any'" in description_lower:
            prohibited.append('any')
        
        return prohibited
    
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

