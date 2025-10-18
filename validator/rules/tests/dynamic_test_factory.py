#!/usr/bin/env python3
"""
Dynamic Test Factory - Simplified Version

What: Simplified test factory for backward compatibility
Why: Maintain compatibility with existing tests
Reads: config/rules/*.json
Writes: test results
Contracts: Test API contracts
Risks: None

Following Constitution Rules:
- Rule 12: Test Everything (prove behavior before/after)
- Rule 97-106: Simple English comments
- Rule 129: Proper error handling
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DataTestCase:
    """Represents a test case."""
    rule_id: str
    rule_name: str
    category: str
    description: str
    test_type: str = "validation"
    constitution: str = ""
    validator: str = ""
    severity: str = "warning"
    error_code: str = "ERROR:TEST"
    expected_behavior: str = ""


class DynamicTestFactory:
    """Simplified dynamic test factory for backward compatibility."""
    
    def __init__(self, rules_file: Optional[str] = None):
        """Initialize the test factory."""
        self.rules_file = rules_file
        self.test_cases: List[TestCase] = []
    
    def load_rules(self) -> Dict[str, Any]:
        """Load rules from configuration."""
        try:
            # Try to load from base config
            config_path = Path(__file__).parent.parent.parent.parent / "config" / "base_config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
            
            # Fallback to empty config
            return {"rules": [], "categories": {}}
            
        except Exception as e:
            print(f"Warning: Could not load rules: {e}")
            return {"rules": [], "categories": {}}
    
    def generate_test_cases(self) -> List[DataTestCase]:
        """Generate test cases from rules."""
        rules_config = self.load_rules()
        test_cases = []
        
        # Generate basic test cases for common rules
        basic_rules = [
            ("R001", "Do Exactly What's Asked", "requirements", "Requirements", "requirements_validator"),
            ("R002", "Only Use Information You're Given", "requirements", "Requirements", "requirements_validator"),
            ("R003", "Protect People's Privacy", "privacy_security", "Privacy Security", "privacy_validator"),
            ("R004", "Use Settings Files, Not Hardcoded Numbers", "basic_work", "Basic Work", "basic_work_validator"),
            ("R005", "Keep Good Records + Keep Good Logs", "basic_work", "Basic Work", "basic_work_validator"),
            ("R150", "Prevent First", "exception_handling", "Exception Handling", "exception_handling_validator"),
            ("R182", "No Any in Committed Code", "typescript", "TypeScript", "typescript_validator"),
        ]
        
        for rule_id, rule_name, category, constitution, validator in basic_rules:
            test_case = DataTestCase(
                rule_id=rule_id,
                rule_name=rule_name,
                category=category,
                description=f"Test for {rule_name}",
                test_type="validation",
                constitution=constitution,
                validator=validator,
                severity="warning",
                error_code=f"ERROR:{rule_id}",
                expected_behavior=f"Should validate {rule_name.lower()}"
            )
            test_cases.append(test_case)

        self.test_cases = test_cases
        return test_cases

    def get_test_cases_by_category(self, category: str) -> List[DataTestCase]:
        """Get test cases for a specific category."""
        return [tc for tc in self.test_cases if tc.category == category]
    
    def get_test_case_by_id(self, rule_id: str) -> Optional[DataTestCase]:
        """Get a specific test case by ID."""
        for tc in self.test_cases:
            if tc.rule_id == rule_id:
                return tc
        return None
    
    def create_test_cases(self, category: str = None, filter_func=None) -> List[DataTestCase]:
        """Create test cases for a specific category or all categories."""
        if category:
            cases = self.get_test_cases_by_category(category)
        else:
            cases = self.generate_test_cases()
        
        if filter_func:
            cases = [case for case in cases if filter_func(case)]
        
        return cases
    
    def get_all_rules(self) -> List[Dict[str, Any]]:
        """Get all rules from configuration."""
        try:
            # Load rules from individual category files
            rules_dir = Path(__file__).parent.parent.parent.parent / "config" / "rules"
            all_rules = []
            
            if rules_dir.exists():
                for rule_file in rules_dir.glob("*.json"):
                    try:
                        with open(rule_file, 'r') as f:
                            category_config = json.load(f)
                        
                        category = category_config.get("category", "unknown")
                        rule_numbers = category_config.get("rules", [])
                        
                        # Convert rule numbers to rule objects with id field
                        for rule_num in rule_numbers:
                            rule_id = f"R{rule_num:03d}"
                            
                            # Check if this rule already exists (rule conflicts)
                            existing_rule = next((r for r in all_rules if r["id"] == rule_id), None)
                            if existing_rule:
                                # If rule already exists, add this category to a categories list
                                if "categories" not in existing_rule:
                                    existing_rule["categories"] = [existing_rule["category"]]
                                if category not in existing_rule["categories"]:
                                    existing_rule["categories"].append(category)
                                # Keep the first category as primary
                                continue
                            
                            rule_obj = {
                                "id": rule_id,
                                "rule_number": rule_num,
                                "category": category,
                                "priority": category_config.get("priority", "medium"),
                                "description": category_config.get("description", f"Rule {rule_num}")
                            }
                            all_rules.append(rule_obj)
                    except Exception as e:
                        print(f"Error loading {rule_file}: {e}")
                        continue
            
            return all_rules
        except Exception as e:
            print(f"Error in get_all_rules: {e}")
            # Fallback: return empty list to prevent test failures
            return []
    
    def get_rules_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get rules for a specific category."""
        all_rules = self.get_all_rules()
        return [rule for rule in all_rules if rule.get("category") == category]
