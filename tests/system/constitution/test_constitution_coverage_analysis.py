"""
WHAT: Analyze all 7 constitution JSON files and count total rules
WHY: Establish baseline for 100% test coverage requirement
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Seed for deterministic operations
TEST_RANDOM_SEED = 42


def load_constitution_file(file_path: Path) -> Dict:
    """Load and parse a constitution JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_all_constitution_files() -> Tuple[Dict[str, int], int]:
    """
    Analyze all 7 constitution files and return rule counts.

    Returns:
        Tuple of (file_counts dict, total_count int)
    """
    constitution_dir = Path(__file__).parent.parent.parent.parent / 'docs' / 'constitution'

    files = [
        'MASTER GENERIC RULES.json',
        'VSCODE EXTENSION RULES.json',
        'LOGGING & TROUBLESHOOTING RULES.json',
        'MODULES AND GSMD MAPPING RULES.json',
        'TESTING RULES.json',
        'COMMENTS RULES.json'
    ]

    file_counts = {}
    total = 0

    for filename in files:
        file_path = constitution_dir / filename
        if file_path.exists():
            data = load_constitution_file(file_path)
            rule_count = len(data.get('constitution_rules', []))
            file_counts[filename] = rule_count
            total += rule_count
        else:
            file_counts[filename] = 0

    return file_counts, total


if __name__ == '__main__':
    file_counts, total = analyze_all_constitution_files()
    print("Constitution Rules Analysis:")
    print("=" * 60)
    for filename, count in file_counts.items():
        print(f"{filename:45} {count:4} rules")
    print("=" * 60)
    print(f"{'TOTAL':45} {total:4} rules")
