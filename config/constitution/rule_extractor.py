#!/usr/bin/env python3
"""
Constitution Rule Extractor for ZeroUI 2.0

This module extracts all 215 constitution rules from the master constitution file
and categorizes them properly for database storage.
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional

class ConstitutionRuleExtractor:
    """
    Extracts and categorizes all 215 constitution rules from the master file.
    """
    
    def __init__(self, constitution_file: str = "ZeroUI2.0_Master_Constitution.md"):
        """
        Initialize the rule extractor.
        
        Args:
            constitution_file: Path to the constitution file
        """
        self.constitution_file = Path(constitution_file)
        self.rules = []
        
        # Define rule categories and their mappings
        self.categories = {
            "basic_work": {
                "rules": list(range(1, 19)),
                "priority": "critical",
                "description": "Core principles for all development work"
            },
            "system_design": {
                "rules": list(range(19, 31)),
                "priority": "critical", 
                "description": "System architecture and design principles"
            },
            "problem_solving": {
                "rules": list(range(31, 40)),
                "priority": "critical",
                "description": "Problem-solving methodologies and approaches"
            },
            "platform": {
                "rules": list(range(40, 50)),
                "priority": "critical",
                "description": "Platform-specific rules and guidelines"
            },
            "teamwork": {
                "rules": list(range(50, 76)),
                "priority": "critical",
                "description": "Collaboration and team dynamics"
            },
            "code_review": {
                "rules": list(range(76, 85)),
                "priority": "critical",
                "description": "Code review processes and standards"
            },
            "coding_standards": {
                "rules": list(range(86, 99)),
                "priority": "critical",
                "description": "Technical coding standards and best practices"
            },
            "comments": {
                "rules": list(range(100, 106)),
                "priority": "critical",
                "description": "Documentation and commenting standards"
            },
            "api_contracts": {
                "rules": list(range(107, 118)),
                "priority": "critical",
                "description": "API design, contracts, and governance"
            },
            "other": {
                "rules": list(range(119, 132)),
                "priority": "important",
                "description": "Miscellaneous rules"
            },
            "logging": {
                "rules": list(range(132, 150)),
                "priority": "critical",
                "description": "Logging and troubleshooting standards"
            },
            "exception_handling": {
                "rules": list(range(150, 159)) + list(range(160, 182)),  # Rules 150-158, 160-181 (skip 159)
                "priority": "critical",
                "description": "Exception handling, timeouts, retries, and error recovery"
            },
            "typescript": {
                "rules": list(range(182, 216)),  # Rules 182-215
                "priority": "critical",
                "description": "TypeScript coding standards, type safety, and best practices"
            }
        }
    
    def extract_all_rules(self) -> List[Dict[str, Any]]:
        """
        Extract all 215 rules from the constitution file.
        
        Returns:
            List of rule dictionaries with metadata
        """
        if not self.constitution_file.exists():
            raise FileNotFoundError(f"Constitution file not found: {self.constitution_file}")
        
        with open(self.constitution_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        rules = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for rule headers - multiple patterns
            rule_match = self._extract_rule_header(line)
            if rule_match:
                rule_number, title = rule_match
                
                # Skip if we already have this rule (avoid duplicates)
                if any(rule['rule_number'] == rule_number for rule in rules):
                    continue
                
                # Determine category
                category, priority = self._get_rule_category(rule_number)
                
                # Extract rule content
                content = self._extract_rule_content(lines, i)
                
                rule_data = {
                    'rule_number': rule_number,
                    'title': title,
                    'category': category,
                    'priority': priority,
                    'content': content,
                    'full_text': line + '\n' + content,
                    'extracted_at': self._get_timestamp()
                }
                
                rules.append(rule_data)
        
        # Sort by rule number
        rules.sort(key=lambda x: x['rule_number'])
        
        # Validate we have all 215 rules (1-181 + 182-215, but missing 159)
        if len(rules) != 215:
            print(f"Warning: Expected 215 rules, found {len(rules)}")
        
        return rules
    
    def _extract_rule_header(self, line: str) -> Optional[tuple]:
        """
        Extract rule number and title from a line.
        
        Args:
            line: Line to parse
            
        Returns:
            Tuple of (rule_number, title) or None if not a rule header
        """
        # Pattern 1: "Rule 1: Do Exactly What's Asked"
        pattern1 = r'^Rule\s+(\d+):\s*(.+)$'
        match = re.match(pattern1, line)
        if match:
            return int(match.group(1)), match.group(2).strip()
        
        # Pattern 2: "## Rule 76: Roles & Scope" (with markdown headers)
        pattern2 = r'^#+\s*Rule\s+(\d+):\s*(.+)$'
        match = re.match(pattern2, line)
        if match:
            return int(match.group(1)), match.group(2).strip()
        
        # Pattern 3: "##Rule 81: Evidence Required in PR" (no space after ##)
        pattern3 = r'^#+\s*Rule\s+(\d+):\s*(.+)$'
        match = re.match(pattern3, line)
        if match:
            return int(match.group(1)), match.group(2).strip()
        
        # Pattern 4: "**Rule 150: Prevent First**" (bold markdown format)
        pattern4 = r'^\*\*Rule\s+(\d+):\s*(.+?)\*\*$'
        match = re.match(pattern4, line)
        if match:
            return int(match.group(1)), match.group(2).strip()
        
        # Pattern 5: "**Rule 182 — Title**" (em-dash format)
        pattern5 = r'^\*\*Rule\s+(\d+)\s+—\s+(.+?)\*\*$'
        match = re.match(pattern5, line)
        if match:
            return int(match.group(1)), match.group(2).strip()
        
        return None
    
    def _get_rule_category(self, rule_number: int) -> tuple:
        """
        Get category and priority for a rule number.
        
        Args:
            rule_number: Rule number
            
        Returns:
            Tuple of (category, priority)
        """
        for category_name, category_data in self.categories.items():
            if rule_number in category_data["rules"]:
                return category_name, category_data["priority"]
        
        # Default fallback
        return "other", "important"
    
    def _extract_rule_content(self, lines: List[str], start_index: int) -> str:
        """
        Extract content for a rule starting from the given line index.
        
        Args:
            lines: All lines from the file
            start_index: Index of the rule header line
            
        Returns:
            Rule content as string
        """
        content_lines = []
        i = start_index + 1
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Stop at next rule header
            if self._extract_rule_header(line):
                break
            
            # Stop at section headers (##, ###)
            if line.startswith('##') or line.startswith('###'):
                break
            
            # Stop at major section breaks
            if line.startswith('---') and len(line) >= 3:
                break
            
            # Add non-empty lines
            if line:
                content_lines.append(lines[i])  # Keep original formatting
            
            i += 1
        
        return '\n'.join(content_lines).strip()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for extraction metadata."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_categories(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all categories with their metadata.
        
        Returns:
            Dictionary of categories with metadata
        """
        return self.categories
    
    def get_rules_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get rules for a specific category.
        
        Args:
            category: Category name
            
        Returns:
            List of rules in the category
        """
        all_rules = self.extract_all_rules()
        return [rule for rule in all_rules if rule['category'] == category]
    
    def validate_extraction(self) -> Dict[str, Any]:
        """
        Validate the rule extraction process.
        
        Returns:
            Validation results dictionary
        """
        rules = self.extract_all_rules()
        
        validation = {
            "total_rules": len(rules),
            "expected_rules": 215,
            "missing_rules": [],
            "duplicate_rules": [],
            "category_counts": {},
            "valid": True
        }
        
        # Check for missing rules
        rule_numbers = [rule['rule_number'] for rule in rules]
        for i in range(1, 216):  # Rules 1-215, but skip 159
            if i == 159:  # Rule 159 doesn't exist
                continue
            if i not in rule_numbers:
                validation["missing_rules"].append(i)
                validation["valid"] = False
        
        # Check for duplicates
        seen = set()
        for rule_num in rule_numbers:
            if rule_num in seen:
                validation["duplicate_rules"].append(rule_num)
                validation["valid"] = False
            seen.add(rule_num)
        
        # Count by category
        for rule in rules:
            category = rule['category']
            validation["category_counts"][category] = validation["category_counts"].get(category, 0) + 1
        
        return validation
    
    def export_rules_to_json(self, output_file: Optional[str] = None) -> str:
        """
        Export extracted rules to JSON format.
        
        Args:
            output_file: Optional output file path
            
        Returns:
            JSON string of rules
        """
        import json
        
        rules = self.extract_all_rules()
        json_data = json.dumps(rules, indent=2, ensure_ascii=False)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_data)
        
        return json_data
    
    def get_rule_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all extracted rules.
        
        Returns:
            Summary dictionary
        """
        rules = self.extract_all_rules()
        
        summary = {
            "total_rules": len(rules),
            "categories": {},
            "rule_range": {
                "min": min(rule['rule_number'] for rule in rules) if rules else 0,
                "max": max(rule['rule_number'] for rule in rules) if rules else 0
            }
        }
        
        # Count by category
        for rule in rules:
            category = rule['category']
            if category not in summary["categories"]:
                summary["categories"][category] = {
                    "count": 0,
                    "rules": []
                }
            summary["categories"][category]["count"] += 1
            summary["categories"][category]["rules"].append(rule['rule_number'])
        
        return summary


# Example usage and testing
def main():
    """Example usage of the Constitution Rule Extractor."""
    
    extractor = ConstitutionRuleExtractor()
    
    print("Extracting all 215 constitution rules...")
    rules = extractor.extract_all_rules()
    
    print(f"Extracted {len(rules)} rules")
    
    # Validate extraction
    validation = extractor.validate_extraction()
    print(f"\nValidation Results:")
    print(f"Total rules: {validation['total_rules']}")
    print(f"Expected: {validation['expected_rules']}")
    print(f"Valid: {validation['valid']}")
    
    if validation['missing_rules']:
        print(f"Missing rules: {validation['missing_rules']}")
    
    if validation['duplicate_rules']:
        print(f"Duplicate rules: {validation['duplicate_rules']}")
    
    # Show category counts
    print(f"\nRules by category:")
    for category, count in validation['category_counts'].items():
        print(f"  {category}: {count} rules")
    
    # Show first few rules
    print(f"\nFirst 5 rules:")
    for rule in rules[:5]:
        print(f"  Rule {rule['rule_number']}: {rule['title']} ({rule['category']})")
    
    # Get summary
    summary = extractor.get_rule_summary()
    print(f"\nSummary:")
    print(f"Rule range: {summary['rule_range']['min']} - {summary['rule_range']['max']}")
    print(f"Categories: {len(summary['categories'])}")


if __name__ == "__main__":
    main()
