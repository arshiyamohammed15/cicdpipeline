from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from config.constitution import rule_extractor


@pytest.fixture
def tmp_constitution_dir(tmp_path):
    """Create temporary constitution directory with JSON files."""
    constitution_dir = tmp_path / "constitution"
    constitution_dir.mkdir()
    
    # Create sample JSON file
    file1 = constitution_dir / "basic_work.json"
    file1.write_text(json.dumps({
        "constitution_rules": [
            {
                "rule_id": "RULE_001",
                "title": "Test Rule 1",
                "description": "Test description",
                "category": "basic_work",
                "severity_level": "critical"
            }
        ]
    }), encoding="utf-8")
    
    return constitution_dir


@pytest.fixture
def extractor(tmp_constitution_dir):
    """Create rule extractor."""
    return rule_extractor.ConstitutionRuleExtractor(
        constitution_file="nonexistent.md",
        constitution_dir=str(tmp_constitution_dir)
    )


@pytest.mark.constitution
def test_extractor_initialization(extractor, tmp_constitution_dir):
    """Test extractor initialization."""
    assert extractor.constitution_dir == tmp_constitution_dir
    assert extractor.rules == []


@pytest.mark.constitution
def test_extract_all_rules_from_json(extractor):
    """Test extracting rules from JSON corpus."""
    rules = extractor.extract_all_rules()
    
    assert len(rules) > 0
    assert rules[0]["rule_number"] == 1
    assert rules[0]["title"] == "Test Rule 1"


@pytest.mark.constitution
def test_extract_all_rules_from_markdown(tmp_path):
    """Test extracting rules from markdown file."""
    markdown_file = tmp_path / "constitution.md"
    markdown_file.write_text("""
# Constitution

Rule 1: Test Rule Title

This is the content of rule 1.

Rule 2: Another Rule

This is the content of rule 2.
""", encoding="utf-8")
    
    extractor = rule_extractor.ConstitutionRuleExtractor(
        constitution_file=str(markdown_file),
        constitution_dir=str(tmp_path / "constitution")
    )
    
    rules = extractor.extract_all_rules()
    
    assert len(rules) >= 2
    assert any(r["rule_number"] == 1 for r in rules)
    assert any(r["rule_number"] == 2 for r in rules)


@pytest.mark.constitution
def test_extract_rule_header_pattern1():
    """Test extracting rule header with pattern 1."""
    extractor = rule_extractor.ConstitutionRuleExtractor()
    
    result = extractor._extract_rule_header("Rule 1: Do Exactly What's Asked")
    assert result == (1, "Do Exactly What's Asked")


@pytest.mark.constitution
def test_extract_rule_header_pattern2():
    """Test extracting rule header with pattern 2."""
    extractor = rule_extractor.ConstitutionRuleExtractor()
    
    result = extractor._extract_rule_header("## Rule 76: Roles & Scope")
    assert result == (76, "Roles & Scope")


@pytest.mark.constitution
def test_extract_rule_header_pattern3():
    """Test extracting rule header with pattern 3."""
    extractor = rule_extractor.ConstitutionRuleExtractor()
    
    result = extractor._extract_rule_header("##Rule 81: Evidence Required in PR")
    assert result == (81, "Evidence Required in PR")


@pytest.mark.constitution
def test_extract_rule_header_pattern4():
    """Test extracting rule header with pattern 4."""
    extractor = rule_extractor.ConstitutionRuleExtractor()
    
    result = extractor._extract_rule_header("**Rule 150: Prevent First**")
    assert result == (150, "Prevent First")


@pytest.mark.constitution
def test_extract_rule_header_pattern5():
    """Test extracting rule header with pattern 5."""
    extractor = rule_extractor.ConstitutionRuleExtractor()
    
    result = extractor._extract_rule_header("**Rule 182 — Title**")
    assert result == (182, "Title")


@pytest.mark.constitution
def test_extract_rule_header_invalid():
    """Test extracting invalid rule header."""
    extractor = rule_extractor.ConstitutionRuleExtractor()
    
    result = extractor._extract_rule_header("Not a rule header")
    assert result is None


@pytest.mark.constitution
def test_get_rule_category():
    """Test getting rule category."""
    extractor = rule_extractor.ConstitutionRuleExtractor()
    
    category, priority = extractor._get_rule_category(1)
    assert category == "basic_work"
    assert priority == "critical"
    
    category, priority = extractor._get_rule_category(19)
    assert category == "system_design"
    assert priority == "critical"
    
    category, priority = extractor._get_rule_category(999)
    assert category == "other"
    assert priority == "important"


@pytest.mark.constitution
def test_extract_rule_content(tmp_path):
    """Test extracting rule content."""
    markdown_file = tmp_path / "test.md"
    markdown_file.write_text("""
Rule 1: Test Rule

This is the content.
It spans multiple lines.

Rule 2: Next Rule
""", encoding="utf-8")
    
    extractor = rule_extractor.ConstitutionRuleExtractor(constitution_file=str(markdown_file))
    
    with open(markdown_file, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n')
    
    content = extractor._extract_rule_content(lines, 2)  # Rule 1 starts at line 2
    assert "This is the content" in content
    assert "It spans multiple lines" in content


@pytest.mark.constitution
def test_get_categories():
    """Test getting all categories."""
    extractor = rule_extractor.ConstitutionRuleExtractor()
    
    categories = extractor.get_categories()
    
    assert isinstance(categories, dict)
    assert "basic_work" in categories
    assert "system_design" in categories
    assert "problem_solving" in categories


@pytest.mark.constitution
def test_get_rules_by_category(extractor):
    """Test getting rules by category."""
    rules = extractor.get_rules_by_category("basic_work")
    
    assert isinstance(rules, list)
    # Should include rules from JSON
    assert len(rules) > 0


@pytest.mark.constitution
def test_validate_extraction(extractor):
    """Test validating extraction."""
    validation = extractor.validate_extraction()
    
    assert "total_rules" in validation
    assert "missing_rules" in validation
    assert "duplicate_rules" in validation
    assert "category_counts" in validation
    assert "valid" in validation


@pytest.mark.constitution
def test_export_rules_to_json(extractor, tmp_path):
    """Test exporting rules to JSON."""
    output_file = tmp_path / "exported_rules.json"
    
    json_data = extractor.export_rules_to_json(str(output_file))
    
    assert isinstance(json_data, str)
    assert output_file.exists()
    
    # Verify JSON is valid
    parsed = json.loads(json_data)
    assert isinstance(parsed, list)


@pytest.mark.constitution
def test_export_rules_to_json_no_file(extractor):
    """Test exporting rules to JSON without file."""
    json_data = extractor.export_rules_to_json()
    
    assert isinstance(json_data, str)
    parsed = json.loads(json_data)
    assert isinstance(parsed, list)


@pytest.mark.constitution
def test_get_rule_summary(extractor):
    """Test getting rule summary."""
    summary = extractor.get_rule_summary()
    
    assert "total_rules" in summary
    assert "categories" in summary
    assert "rule_range" in summary
    assert "min" in summary["rule_range"]
    assert "max" in summary["rule_range"]


@pytest.mark.constitution
def test_derive_rule_number():
    """Test deriving rule number from JSON rule."""
    extractor = rule_extractor.ConstitutionRuleExtractor()
    
    # Rule with explicit rule_number
    rule1 = {"rule_number": 5}
    assert extractor._derive_rule_number(rule1, 1) == 5
    
    # Rule with rule_id containing number
    rule2 = {"rule_id": "RULE_123"}
    assert extractor._derive_rule_number(rule2, 1) == 123
    
    # Rule with no number, use fallback
    rule3 = {"title": "Test"}
    assert extractor._derive_rule_number(rule3, 10) == 10


@pytest.mark.constitution
def test_load_from_json_corpus_not_found(tmp_path):
    """Test loading from non-existent JSON corpus."""
    extractor = rule_extractor.ConstitutionRuleExtractor(
        constitution_file="nonexistent.md",
        constitution_dir=str(tmp_path / "nonexistent")
    )
    
    with pytest.raises(FileNotFoundError):
        extractor._load_from_json_corpus()


@pytest.mark.constitution
def test_load_from_json_corpus_no_files(tmp_path):
    """Test loading from empty JSON corpus."""
    constitution_dir = tmp_path / "constitution"
    constitution_dir.mkdir()
    
    extractor = rule_extractor.ConstitutionRuleExtractor(
        constitution_file="nonexistent.md",
        constitution_dir=str(constitution_dir)
    )
    
    with pytest.raises(FileNotFoundError):
        extractor._load_from_json_corpus()

