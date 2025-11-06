"""
Rule Number Validation Utility

Provides utilities to validate rule numbers and look up rules programmatically.
Prevents errors from using JSON line numbers instead of actual rule numbers.

Root Cause Prevention:
- Never hardcode rule numbers
- Always validate rule numbers exist
- Always use programmatic lookup from constitution rules database
"""

from typing import Optional, Dict, Any
from config.constitution.constitution_rules_json import ConstitutionRulesJSON


class RuleNumberValidator:
    """
    Validates rule numbers and provides lookup utilities.
    
    Prevents errors where JSON line numbers (e.g., 4083) are mistaken
    for actual rule numbers (e.g., 172).
    """
    
    def __init__(self):
        """Initialize rule number validator."""
        self.rule_loader = ConstitutionRulesJSON()
        self.max_rule_number = 415  # From statistics in constitution_rules.json
    
    def validate_rule_number(self, rule_number: int) -> bool:
        """
        Validate that a rule number exists and is in valid range.
        
        Args:
            rule_number: Rule number to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If rule number is out of range or doesn't exist
        """
        # Check range first (fast validation)
        if rule_number < 1 or rule_number > self.max_rule_number:
            raise ValueError(
                f"Rule number {rule_number} is out of valid range (1-{self.max_rule_number}). "
                f"Did you use a JSON line number instead of rule_number field?"
            )
        
        # Check rule exists
        rule = self.rule_loader.get_rule_by_number(rule_number)
        if not rule:
            raise ValueError(
                f"Rule {rule_number} does not exist in constitution rules. "
                f"Valid range: 1-{self.max_rule_number}"
            )
        
        # Verify rule_number field matches
        actual_rule_number = rule.get('rule_number')
        if actual_rule_number != rule_number:
            raise ValueError(
                f"Rule number mismatch: requested {rule_number}, "
                f"but rule has rule_number={actual_rule_number}"
            )
        
        return True
    
    def get_rule_by_number(self, rule_number: int) -> Optional[Dict[str, Any]]:
        """
        Get rule by number with validation.
        
        Args:
            rule_number: Rule number to look up
            
        Returns:
            Rule dictionary or None if not found
            
        Raises:
            ValueError: If rule number is invalid
        """
        self.validate_rule_number(rule_number)
        return self.rule_loader.get_rule_by_number(rule_number)
    
    def get_rule_number_by_title(self, title_keyword: str) -> Optional[int]:
        """
        Get rule number by searching for title keyword.
        
        Args:
            title_keyword: Keyword in rule title (e.g., "Structured Logs")
            
        Returns:
            Rule number if found, None otherwise
        """
        all_rules = self.rule_loader.get_all_rules()
        
        for rule in all_rules:
            title = rule.get('title', '')
            if title_keyword.lower() in title.lower():
                return rule.get('rule_number')
        
        return None
    
    def validate_rule_numbers(self, rule_numbers: list[int]) -> Dict[int, bool]:
        """
        Validate multiple rule numbers at once.
        
        Args:
            rule_numbers: List of rule numbers to validate
            
        Returns:
            Dictionary mapping rule_number -> is_valid
        """
        results = {}
        for rule_num in rule_numbers:
            try:
                self.validate_rule_number(rule_num)
                results[rule_num] = True
            except ValueError as e:
                results[rule_num] = False
                print(f"ERROR: Rule {rule_num} validation failed: {e}")
        
        return results

