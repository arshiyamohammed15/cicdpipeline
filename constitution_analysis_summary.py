#!/usr/bin/env python3
"""
Quick Constitution Rules Analysis Summary

This script provides a quick summary of the constitution rules analysis.
"""

import json
from datetime import datetime
from pathlib import Path

def print_summary():
    """Print a summary of the constitution rules analysis."""
    
    print("=" * 60)
    print("CONSTITUTION RULES ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if analysis file exists
    analysis_files = list(Path('.').glob('constitution_analysis_*.json'))
    if not analysis_files:
        print("No analysis files found. Run analyze_constitution_rules.py first.")
        return
    
    # Load the most recent analysis
    latest_file = max(analysis_files, key=lambda f: f.stat().st_mtime)
    print(f"Analysis File: {latest_file}")
    print()
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Summary
        summary = data['summary']
        print("OVERALL STATUS:")
        print(f"  Sources Analyzed: {summary['total_sources_analyzed']}/4")
        print(f"  Consistency: {summary['consistency_status'].upper()}")
        print(f"  Total Issues: {summary['total_issues']}")
        print()
        
        # Rule counts
        print("RULE COUNTS BY SOURCE:")
        for source, count in summary['rule_counts'].items():
            status = "[OK]" if count == 293 else "[WARN]"
            print(f"  {status} {source.title()}: {count} rules")
        print()
        
        # Issues breakdown
        if summary['total_issues'] > 0:
            print("ISSUES FOUND:")
            if summary['missing_rules_count'] > 0:
                print(f"  • Missing Rules: {summary['missing_rules_count']}")
            if summary['extra_rules_count'] > 0:
                print(f"  • Extra Rules: {summary['extra_rules_count']}")
            if summary['content_mismatches_count'] > 0:
                print(f"  • Content Mismatches: {summary['content_mismatches_count']}")
            print()
        else:
            print("[OK] NO ISSUES FOUND - All sources are consistent!")
            print()
        
        # Recommendations
        if data.get('recommendations'):
            print("RECOMMENDATIONS:")
            for i, rec in enumerate(data['recommendations'], 1):
                print(f"  {i}. {rec}")
            print()
        
        # Detailed issues
        if data.get('issues'):
            print("DETAILED ISSUES:")
            for i, issue in enumerate(data['issues'], 1):
                print(f"  {i}. {issue['type'].replace('_', ' ').title()}")
                if 'source' in issue:
                    print(f"     Source: {issue['source']}")
                if 'missing_count' in issue:
                    print(f"     Missing: {issue['missing_count']} rules")
                if 'extra_count' in issue:
                    print(f"     Extra: {issue['extra_count']} rules")
            print()
        
        # Sources status
        print("SOURCE STATUS:")
        for source_name, source_data in data['sources'].items():
            status = "[OK]" if source_data.get('status') == 'success' else "[ERROR]"
            print(f"  {status} {source_name.title()}: {source_data.get('total_rules', 0)} rules")
        
        print()
        print("=" * 60)
        
    except Exception as e:
        print(f"Error reading analysis file: {e}")

if __name__ == "__main__":
    print_summary()
