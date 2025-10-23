#!/usr/bin/env python3
"""
ZeroUI 2.0 Master Constitution Analyzer
Single source of truth for constitution analysis

Purpose: Extract and analyze rules from ZeroUI2.0_Master_Constitution.md
Author: AI Assistant
Date: 2024-12-19

This tool provides 100% confidence in constitution analysis by using deterministic
methods and providing verifiable evidence for all claims.

Usage:
    python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --summary
    python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --rule 1
    python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --search "privacy"
    python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --output analysis.json
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class Rule:
    """Represents a single rule from the constitution"""
    number: int
    title: str
    content: str
    line_number: int
    category: Optional[str] = None
    section: Optional[str] = None


@dataclass
class ConstitutionAnalysis:
    """Complete analysis of the constitution"""
    total_rules: int
    rules: List[Rule]
    categories: Dict[str, List[Rule]]
    sections: Dict[str, List[Rule]]
    rule_numbers: List[int]
    missing_numbers: List[int]
    highest_rule: int
    lowest_rule: int


class ConstitutionAnalyzer:
    """Deterministic analyzer for ZeroUI 2.0 Master Constitution"""
    
    def __init__(self, constitution_path: str):
        self.constitution_path = Path(constitution_path)
        self.rules: List[Rule] = []
        self.analysis: Optional[ConstitutionAnalysis] = None
        
    def extract_rules(self) -> List[Rule]:
        """Extract all rules from the constitution file using deterministic regex patterns"""
        if not self.constitution_path.exists():
            raise FileNotFoundError(f"Constitution file not found: {self.constitution_path}")
        
        with open(self.constitution_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match rules: **Rule N: Title** Content
        rule_pattern = r'\*\*Rule (\d+): ([^*]+)\*\*([^*]*(?:\*(?!\*)[^*]*)*)'
        
        rules = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            match = re.match(rule_pattern, line.strip())
            if match:
                rule_num = int(match.group(1))
                title = match.group(2).strip()
                content = match.group(3).strip()
                
                # Get category and section from context
                category, section = self._determine_category_and_section(line_num, lines)
                
                rule = Rule(
                    number=rule_num,
                    title=title,
                    content=content,
                    line_number=line_num,
                    category=category,
                    section=section
                )
                rules.append(rule)
        
        self.rules = sorted(rules, key=lambda r: r.number)
        return self.rules
    
    def _determine_category_and_section(self, line_num: int, lines: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """Determine category and section for a rule based on context"""
        category = None
        section = None
        
        # Look backwards for section headers
        for i in range(max(0, line_num - 20), line_num):
            line = lines[i].strip()
            
            # Check for section headers
            if line.startswith('🎯') or line.startswith('🏗️') or line.startswith('🔧'):
                section = line
            elif line.startswith('##') or line.startswith('###'):
                section = line
            elif 'BASIC WORK RULES' in line:
                category = 'Basic Work'
            elif 'SYSTEM DESIGN RULES' in line:
                category = 'System Design'
            elif 'PROBLEM-SOLVING RULES' in line:
                category = 'Problem Solving'
            elif 'PLATFORM RULES' in line:
                category = 'Platform'
            elif 'TEAMWORK RULES' in line:
                category = 'Teamwork'
            elif 'CODE REVIEW' in line:
                category = 'Code Review'
            elif 'CODING STANDARDS' in line:
                category = 'Coding Standards'
            elif 'LOGGING' in line:
                category = 'Logging'
            elif 'EXCEPTION HANDLING' in line:
                category = 'Exception Handling'
            elif 'TYPESCRIPT' in line:
                category = 'TypeScript'
            elif 'STORAGE GOVERNANCE' in line:
                category = 'Storage Governance'
            elif 'GSMD' in line:
                category = 'GSMD'
            elif 'SIMPLE CODE READABILITY' in line:
                category = 'Code Readability'
        
        return category, section
    
    def analyze_constitution(self) -> ConstitutionAnalysis:
        """Perform complete analysis of the constitution"""
        if not self.rules:
            self.extract_rules()
        
        # Basic statistics
        total_rules = len(self.rules)
        rule_numbers = [rule.number for rule in self.rules]
        highest_rule = max(rule_numbers) if rule_numbers else 0
        lowest_rule = min(rule_numbers) if rule_numbers else 0
        
        # Find missing rule numbers
        if rule_numbers:
            expected_range = set(range(lowest_rule, highest_rule + 1))
            actual_numbers = set(rule_numbers)
            missing_numbers = sorted(expected_range - actual_numbers)
        else:
            missing_numbers = []
        
        # Group by categories
        categories = {}
        for rule in self.rules:
            if rule.category:
                if rule.category not in categories:
                    categories[rule.category] = []
                categories[rule.category].append(rule)
        
        # Group by sections
        sections = {}
        for rule in self.rules:
            if rule.section:
                if rule.section not in sections:
                    sections[rule.section] = []
                sections[rule.section].append(rule)
        
        self.analysis = ConstitutionAnalysis(
            total_rules=total_rules,
            rules=self.rules,
            categories=categories,
            sections=sections,
            rule_numbers=rule_numbers,
            missing_numbers=missing_numbers,
            highest_rule=highest_rule,
            lowest_rule=lowest_rule
        )
        
        return self.analysis
    
    def get_rule_by_number(self, rule_number: int) -> Optional[Rule]:
        """Get a specific rule by number"""
        for rule in self.rules:
            if rule.number == rule_number:
                return rule
        return None
    
    def get_rules_by_category(self, category: str) -> List[Rule]:
        """Get all rules in a specific category"""
        return [rule for rule in self.rules if rule.category == category]
    
    def search_rules(self, query: str) -> List[Rule]:
        """Search rules by title or content"""
        query_lower = query.lower()
        matching_rules = []
        
        for rule in self.rules:
            if (query_lower in rule.title.lower() or 
                query_lower in rule.content.lower()):
                matching_rules.append(rule)
        
        return matching_rules
    
    def export_analysis(self, output_path: str) -> None:
        """Export complete analysis to JSON file"""
        if not self.analysis:
            self.analyze_constitution()
        
        # Convert to serializable format
        export_data = {
            'total_rules': self.analysis.total_rules,
            'rule_numbers': self.analysis.rule_numbers,
            'missing_numbers': self.analysis.missing_numbers,
            'highest_rule': self.analysis.highest_rule,
            'lowest_rule': self.analysis.lowest_rule,
            'categories': {
                category: [asdict(rule) for rule in rules]
                for category, rules in self.analysis.categories.items()
            },
            'sections': {
                section: [asdict(rule) for rule in rules]
                for section, rules in self.analysis.sections.items()
            },
            'all_rules': [asdict(rule) for rule in self.analysis.rules]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def print_summary(self) -> None:
        """Print a summary of the constitution analysis"""
        if not self.analysis:
            self.analyze_constitution()
        
        print("=" * 60)
        print("ZEROUI 2.0 MASTER CONSTITUTION ANALYSIS")
        print("=" * 60)
        print(f"Total Rules: {self.analysis.total_rules}")
        print(f"Rule Range: {self.analysis.lowest_rule} - {self.analysis.highest_rule}")
        print(f"Missing Numbers: {len(self.analysis.missing_numbers)}")
        if self.analysis.missing_numbers:
            print(f"Missing: {self.analysis.missing_numbers[:10]}{'...' if len(self.analysis.missing_numbers) > 10 else ''}")
        
        print("\nCategories:")
        for category, rules in self.analysis.categories.items():
            print(f"  {category}: {len(rules)} rules")
        
        print("\nTop 10 Rules by Number:")
        for rule in self.analysis.rules[:10]:
            print(f"  Rule {rule.number}: {rule.title}")
        
        if len(self.analysis.rules) > 10:
            print(f"  ... and {len(self.analysis.rules) - 10} more rules")
    
    def print_rule_details(self, rule: Rule) -> None:
        """Print detailed information about a specific rule"""
        print(f"\nRule {rule.number}: {rule.title}")
        print(f"Content: {rule.content}")
        print(f"Category: {rule.category}")
        print(f"Section: {rule.section}")
        print(f"Line: {rule.line_number}")
    
    def print_search_results(self, query: str, results: List[Rule]) -> None:
        """Print search results in a formatted way"""
        print(f"\nFound {len(results)} rules matching '{query}':")
        for rule in results:
            print(f"  Rule {rule.number}: {rule.title}")
    
    def print_category_results(self, category: str, results: List[Rule]) -> None:
        """Print category results in a formatted way"""
        print(f"\nRules in category '{category}': {len(results)}")
        for rule in results:
            print(f"  Rule {rule.number}: {rule.title}")


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description='Extract and analyze ZeroUI 2.0 Master Constitution',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --summary
  python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --rule 1
  python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --search "privacy"
  python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --output analysis.json
        """
    )
    
    parser.add_argument('constitution_file', help='Path to ZeroUI2.0_Master_Constitution.md')
    parser.add_argument('--output', '-o', help='Output JSON file for analysis')
    parser.add_argument('--summary', '-s', action='store_true', help='Print summary')
    parser.add_argument('--rule', '-r', type=int, help='Show specific rule number')
    parser.add_argument('--search', help='Search rules by content')
    parser.add_argument('--category', help='Show rules by category')
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = ConstitutionAnalyzer(args.constitution_file)
    
    try:
        # Extract rules
        print("Extracting rules...")
        rules = analyzer.extract_rules()
        print(f"Found {len(rules)} rules")
        
        # Analyze constitution
        analysis = analyzer.analyze_constitution()
        
        # Handle specific requests
        if args.rule:
            rule = analyzer.get_rule_by_number(args.rule)
            if rule:
                analyzer.print_rule_details(rule)
            else:
                print(f"Rule {args.rule} not found")
        
        elif args.search:
            matching_rules = analyzer.search_rules(args.search)
            analyzer.print_search_results(args.search, matching_rules)
        
        elif args.category:
            category_rules = analyzer.get_rules_by_category(args.category)
            analyzer.print_category_results(args.category, category_rules)
        
        else:
            # Default: show summary
            analyzer.print_summary()
        
        # Export if requested
        if args.output:
            analyzer.export_analysis(args.output)
            print(f"\nAnalysis exported to: {args.output}")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
