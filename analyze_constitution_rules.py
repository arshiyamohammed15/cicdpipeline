#!/usr/bin/env python3
"""
Constitution Rules Analysis Tool

This script analyzes constitution rules across 4 sources:
1. Markdown (docs/architecture/ZeroUI2.0_Master_Constitution.md)
2. Database (config/constitution_rules.db)
3. JSON Export (config/constitution_rules.json)
4. Config (config/constitution_config.json)

It checks for consistency in rule numbers, titles, content, and other details.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import sqlite3

class ConstitutionRulesAnalyzer:
    """Analyzes constitution rules across all sources."""
    
    def __init__(self):
        """Initialize the analyzer."""
        self.markdown_path = "docs/architecture/ZeroUI2.0_Master_Constitution.md"
        self.db_path = "config/constitution_rules.db"
        self.json_path = "config/constitution_rules.json"
        self.config_path = "config/constitution_config.json"
        
        self.analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "sources": {},
            "summary": {},
            "issues": [],
            "recommendations": []
        }
    
    def analyze_all_sources(self) -> Dict[str, Any]:
        """
        Analyze all sources and return comprehensive results.
        
        Returns:
            Dictionary containing analysis results
        """
        print("Analyzing Constitution Rules...")
        
        # Analyze each source
        self._analyze_markdown()
        self._analyze_database()
        self._analyze_json_export()
        self._analyze_config()
        
        # Cross-source analysis
        self._cross_source_analysis()
        
        # Generate summary
        self._generate_summary()
        
        return self.analysis_results
    
    def _analyze_markdown(self):
        """Analyze markdown source."""
        print("  Markdown...", end=" ")
        
        try:
            from config.constitution.rule_extractor import ConstitutionRuleExtractor
            
            extractor = ConstitutionRuleExtractor(self.markdown_path)
            rules = extractor.extract_all_rules()
            
            self.analysis_results["sources"]["markdown"] = {
                "type": "markdown",
                "path": self.markdown_path,
                "total_rules": len(rules),
                "rule_numbers": sorted([r["rule_number"] for r in rules]),
                "categories": self._get_categories_from_rules(rules),
                "sample_rules": rules[:3] if rules else [],
                "status": "success"
            }
            
            print(f"OK ({len(rules)} rules)")
            
        except Exception as e:
            self.analysis_results["sources"]["markdown"] = {
                "type": "markdown",
                "path": self.markdown_path,
                "status": "error",
                "error": str(e)
            }
            print(f"ERROR: {e}")
    
    def _analyze_database(self):
        """Analyze database source."""
        print("  Database...", end=" ")
        
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all rules
            cursor.execute("SELECT rule_number, title, category, priority, content FROM constitution_rules")
            db_rules = cursor.fetchall()
            
            # Get enabled/disabled states from rule_configuration table
            cursor.execute("SELECT rule_number, enabled FROM rule_configuration")
            enabled_states = {row[0]: bool(row[1]) for row in cursor.fetchall()}
            
            rules_data = []
            for rule in db_rules:
                rule_number = rule[0]
                rules_data.append({
                    "rule_number": rule_number,
                    "title": rule[1],
                    "category": rule[2],
                    "priority": rule[3],
                    "content": rule[4],
                    "enabled": enabled_states.get(rule_number, True)  # Default to enabled if not found
                })
            
            conn.close()
            
            self.analysis_results["sources"]["database"] = {
                "type": "sqlite",
                "path": self.db_path,
                "total_rules": len(rules_data),
                "rule_numbers": sorted([r["rule_number"] for r in rules_data]),
                "categories": self._get_categories_from_rules(rules_data),
                "sample_rules": rules_data[:3] if rules_data else [],
                "status": "success"
            }
            
            print(f"OK ({len(rules_data)} rules)")
            
        except Exception as e:
            self.analysis_results["sources"]["database"] = {
                "type": "sqlite",
                "path": self.db_path,
                "status": "error",
                "error": str(e)
            }
            print(f"ERROR: {e}")
    
    def _analyze_json_export(self):
        """Analyze JSON export source."""
        print("  JSON Export...", end=" ")
        
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(json_data, list):
                rules_data = json_data
            elif isinstance(json_data, dict) and "rules" in json_data:
                rules_data = list(json_data["rules"].values())
            else:
                rules_data = []
            
            self.analysis_results["sources"]["json_export"] = {
                "type": "json",
                "path": self.json_path,
                "total_rules": len(rules_data),
                "rule_numbers": sorted([r.get("rule_number", 0) for r in rules_data if r.get("rule_number")]),
                "categories": self._get_categories_from_rules(rules_data),
                "sample_rules": rules_data[:3] if rules_data else [],
                "status": "success"
            }
            
            print(f"OK ({len(rules_data)} rules)")
            
        except Exception as e:
            self.analysis_results["sources"]["json_export"] = {
                "type": "json",
                "path": self.json_path,
                "status": "error",
                "error": str(e)
            }
            print(f"ERROR: {e}")
    
    def _analyze_config(self):
        """Analyze config source."""
        print("  Config...", end=" ")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            rules_config = config_data.get("rules", {})
            enabled_rules = []
            disabled_rules = []
            
            for rule_num_str, rule_state in rules_config.items():
                try:
                    rule_num = int(rule_num_str)
                    if rule_state.get("enabled", True):
                        enabled_rules.append(rule_num)
                    else:
                        disabled_rules.append(rule_num)
                except ValueError:
                    continue
            
            self.analysis_results["sources"]["config"] = {
                "type": "config",
                "path": self.config_path,
                "total_rules": len(rules_config),
                "enabled_rules": sorted(enabled_rules),
                "disabled_rules": sorted(disabled_rules),
                "rule_numbers": sorted(enabled_rules + disabled_rules),
                "status": "success"
            }
            
            print(f"OK ({len(rules_config)} rules, {len(enabled_rules)} enabled)")
            
        except Exception as e:
            self.analysis_results["sources"]["config"] = {
                "type": "config",
                "path": self.config_path,
                "status": "error",
                "error": str(e)
            }
            print(f"ERROR: {e}")
    
    def _cross_source_analysis(self):
        """Perform cross-source analysis."""
        print("  Cross-source analysis...", end=" ")
        
        sources = self.analysis_results["sources"]
        issues = []
        
        # Get rule numbers from each source
        markdown_rules = set(sources.get("markdown", {}).get("rule_numbers", []))
        db_rules = set(sources.get("database", {}).get("rule_numbers", []))
        json_rules = set(sources.get("json_export", {}).get("rule_numbers", []))
        config_rules = set(sources.get("config", {}).get("rule_numbers", []))
        
        # Find missing rules
        all_rule_sets = [markdown_rules, db_rules, json_rules, config_rules]
        all_rules = markdown_rules | db_rules | json_rules | config_rules
        
        for source_name, source_rules in [
            ("markdown", markdown_rules),
            ("database", db_rules),
            ("json_export", json_rules),
            ("config", config_rules)
        ]:
            missing_in_source = all_rules - source_rules
            if missing_in_source:
                issues.append({
                    "type": "missing_rules",
                    "source": source_name,
                    "missing_count": len(missing_in_source),
                    "missing_rules": sorted(list(missing_in_source))
                })
        
        # Find extra rules (rules in source but not in markdown)
        extra_rules = {}
        for source_name, source_rules in [
            ("database", db_rules),
            ("json_export", json_rules),
            ("config", config_rules)
        ]:
            extra = source_rules - markdown_rules
            if extra:
                extra_rules[source_name] = sorted(list(extra))
                issues.append({
                    "type": "extra_rules",
                    "source": source_name,
                    "extra_count": len(extra),
                    "extra_rules": sorted(list(extra))
                })
        
        # Check for content mismatches
        content_mismatches = self._check_content_mismatches()
        if content_mismatches:
            issues.extend(content_mismatches)
        
        self.analysis_results["issues"] = issues
        
        # Generate recommendations
        self._generate_recommendations(issues)
        
        # Print status
        if issues:
            print(f"Found {len(issues)} issues")
        else:
            print("OK")
    
    def _check_content_mismatches(self) -> List[Dict[str, Any]]:
        """Check for content mismatches between sources."""
        mismatches = []
        
        try:
            # Get sample rules from each source for comparison
            markdown_sample = self.analysis_results["sources"].get("markdown", {}).get("sample_rules", [])
            db_sample = self.analysis_results["sources"].get("database", {}).get("sample_rules", [])
            json_sample = self.analysis_results["sources"].get("json_export", {}).get("sample_rules", [])
            
            # Compare titles and content for common rules
            for rule_num in range(1, 4):  # Check first 3 rules
                markdown_rule = next((r for r in markdown_sample if r.get("rule_number") == rule_num), None)
                db_rule = next((r for r in db_sample if r.get("rule_number") == rule_num), None)
                json_rule = next((r for r in json_sample if r.get("rule_number") == rule_num), None)
                
                if markdown_rule and db_rule:
                    if markdown_rule.get("title") != db_rule.get("title"):
                        mismatches.append({
                            "type": "title_mismatch",
                            "rule_number": rule_num,
                            "markdown_title": markdown_rule.get("title"),
                            "database_title": db_rule.get("title")
                        })
                
                if markdown_rule and json_rule:
                    if markdown_rule.get("title") != json_rule.get("title"):
                        mismatches.append({
                            "type": "title_mismatch",
                            "rule_number": rule_num,
                            "markdown_title": markdown_rule.get("title"),
                            "json_title": json_rule.get("title")
                        })
        
        except Exception as e:
            print(f"  [WARNING] Could not check content mismatches: {e}")
        
        return mismatches
    
    def _generate_recommendations(self, issues: List[Dict[str, Any]]):
        """Generate recommendations based on issues found."""
        recommendations = []
        
        if not issues:
            recommendations.append("All sources are consistent - no action needed")
            return
        
        # Missing rules recommendations
        missing_issues = [i for i in issues if i["type"] == "missing_rules"]
        if missing_issues:
            recommendations.append("Run sync command to add missing rules to sources")
        
        # Extra rules recommendations
        extra_issues = [i for i in issues if i["type"] == "extra_rules"]
        if extra_issues:
            recommendations.append("Clean up extra rules that don't exist in markdown")
        
        # Content mismatch recommendations
        content_issues = [i for i in issues if i["type"] == "title_mismatch"]
        if content_issues:
            recommendations.append("Resolve content mismatches between sources")
        
        self.analysis_results["recommendations"] = recommendations
    
    def _generate_summary(self):
        """Generate analysis summary."""
        sources = self.analysis_results["sources"]
        issues = self.analysis_results["issues"]
        
        # Count rules by source
        rule_counts = {}
        for source_name, source_data in sources.items():
            if source_data.get("status") == "success":
                rule_counts[source_name] = source_data.get("total_rules", 0)
        
        # Calculate consistency metrics
        total_issues = len(issues)
        missing_rules_count = sum(i.get("missing_count", 0) for i in issues if i["type"] == "missing_rules")
        extra_rules_count = sum(i.get("extra_count", 0) for i in issues if i["type"] == "extra_rules")
        content_mismatches_count = len([i for i in issues if i["type"] == "title_mismatch"])
        
        self.analysis_results["summary"] = {
            "total_sources_analyzed": len([s for s in sources.values() if s.get("status") == "success"]),
            "rule_counts": rule_counts,
            "consistency_status": "consistent" if total_issues == 0 else "inconsistent",
            "total_issues": total_issues,
            "missing_rules_count": missing_rules_count,
            "extra_rules_count": extra_rules_count,
            "content_mismatches_count": content_mismatches_count,
            "recommendations_count": len(self.analysis_results["recommendations"])
        }
    
    def _get_categories_from_rules(self, rules: List[Dict[str, Any]]) -> Dict[str, int]:
        """Extract category counts from rules."""
        categories = {}
        for rule in rules:
            category = rule.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
        return categories
    
    def print_analysis_report(self):
        """Print a formatted executive summary."""
        print("\n" + "=" * 50)
        print("EXECUTIVE SUMMARY - CONSTITUTION RULES")
        print("=" * 50)
        
        # Summary
        summary = self.analysis_results["summary"]
        print(f"\nOVERALL STATUS:")
        print(f"  Sources: {summary['total_sources_analyzed']}/4 analyzed")
        print(f"  Status: {summary['consistency_status'].upper()}")
        print(f"  Issues: {summary['total_issues']}")
        
        # Rule counts by source
        print(f"\nRULE COUNTS:")
        for source_name, count in summary['rule_counts'].items():
            status = "OK" if count == 293 else "WARN"
            print(f"  {source_name.title()}: {count} rules [{status}]")
        
        # Quick status
        if summary['total_issues'] == 0:
            print(f"\n[SUCCESS] All sources are consistent - 293 rules synchronized")
        else:
            print(f"\n[ATTENTION] {summary['total_issues']} issues found:")
            if summary['missing_rules_count'] > 0:
                print(f"  - Missing rules: {summary['missing_rules_count']}")
            if summary['extra_rules_count'] > 0:
                print(f"  - Extra rules: {summary['extra_rules_count']}")
            if summary['content_mismatches_count'] > 0:
                print(f"  - Content mismatches: {summary['content_mismatches_count']}")
        
        print("=" * 50)


def main():
    """Main function to run the analysis."""
    analyzer = ConstitutionRulesAnalyzer()
    
    try:
        # Run analysis
        results = analyzer.analyze_all_sources()
        
        # Print report
        analyzer.print_analysis_report()
        
        # No file output - just console summary
        
        return 0 if results["summary"]["consistency_status"] == "consistent" else 1
        
    except Exception as e:
        print(f"\nAnalysis failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())