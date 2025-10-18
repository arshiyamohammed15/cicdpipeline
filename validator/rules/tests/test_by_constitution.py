"""
Constitution-Based Dynamic Tests for ZeroUI 2.0 Rules

This module organizes tests by Constitution files, using dynamic discovery
to test all rules belonging to each Constitution without hardcoded rule IDs.
"""

import pytest
import sys
from pathlib import Path

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from .dynamic_test_factory import DynamicTestFactory, DataTestCase


class TestCodeReviewConstitution:
    """Test all rules from the Code Review Constitution."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.fixture(scope="class")
    def constitution_rules(self, test_factory):
        """Get all rules from Code Review Constitution."""
        return test_factory.get_rules_by_constitution("Code Review")

    def test_constitution_has_rules(self, constitution_rules):
        """Test that Code Review Constitution has rules."""
        assert len(constitution_rules) > 0, "Code Review Constitution should have rules"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_code_review_rules(self, test_case: DataTestCase):
        """Test all rules from Code Review Constitution."""
        assert test_case.constitution == "Code Review", f"Rule {test_case.rule_id} not from Code Review Constitution"

        # Code Review rules should be about process, governance, or quality
        assert test_case.category in ['scope', 'governance', 'process', 'quality', 'security'], \
            f"Code Review rule {test_case.rule_id} should be scope/governance/process/quality/security category"

        # Verify rule has appropriate validator
        if test_case.category in ['scope', 'governance', 'process', 'quality']:
            assert 'structure_validator' in test_case.validator, \
                f"Code Review rule {test_case.rule_id} should use structure_validator"
        elif test_case.category == 'security':
            assert 'security_validator' in test_case.validator, \
                f"Code Review security rule {test_case.rule_id} should use security_validator"

    def test_code_review_rule_coverage(self, constitution_rules):
        """Test that Code Review Constitution has expected rule types."""
        rule_ids = [rule['id'] for rule in constitution_rules]

        # Should have LOC limit rule
        assert 'R001' in rule_ids, "Code Review Constitution should have LOC limit rule (R001)"

        # Should have PR size guidance
        assert 'R002' in rule_ids, "Code Review Constitution should have PR size guidance (R002)"

        # Should have CODEOWNERS approval
        assert 'R003' in rule_ids, "Code Review Constitution should have CODEOWNERS approval (R003)"

        # Should have security rules
        security_rules = [rule for rule in constitution_rules if rule.get('category') == 'security']
        assert len(security_rules) > 0, "Code Review Constitution should have security rules"


class TestAPIContractsConstitution:
    """Test all rules from the API Contracts Constitution."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.fixture(scope="class")
    def constitution_rules(self, test_factory):
        """Get all rules from API Contracts Constitution."""
        return test_factory.get_rules_by_constitution("API Contracts")

    def test_constitution_has_rules(self, constitution_rules):
        """Test that API Contracts Constitution has rules."""
        assert len(constitution_rules) > 0, "API Contracts Constitution should have rules"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_api_contracts_rules(self, test_case: DataTestCase):
        """Test all rules from API Contracts Constitution."""
        assert test_case.constitution == "API Contracts", f"Rule {test_case.rule_id} not from API Contracts Constitution"

        # API Contracts rules should be about API design
        assert test_case.category == 'api', f"API Contracts rule {test_case.rule_id} should be API category"

        # Should use api_validator
        assert 'api_validator' in test_case.validator, \
            f"API Contracts rule {test_case.rule_id} should use api_validator"

    def test_api_contracts_rule_coverage(self, constitution_rules):
        """Test that API Contracts Constitution has expected rule types."""
        rule_ids = [rule['id'] for rule in constitution_rules]

        # Should have HTTP verbs rule
        assert 'R013' in rule_ids, "API Contracts Constitution should have HTTP verbs rule (R013)"

        # Should have URI structure rule
        assert 'R014' in rule_ids, "API Contracts Constitution should have URI structure rule (R014)"

        # Should have UUIDv7 IDs rule
        assert 'R015' in rule_ids, "API Contracts Constitution should have UUIDv7 IDs rule (R015)"

        # Should have idempotency rule
        assert 'R018' in rule_ids, "API Contracts Constitution should have idempotency rule (R018)"

        # Should have error envelope rule
        assert 'R020' in rule_ids, "API Contracts Constitution should have error envelope rule (R020)"


class TestCodingStandardsConstitution:
    """Test all rules from the Coding Standards Constitution."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.fixture(scope="class")
    def constitution_rules(self, test_factory):
        """Get all rules from Coding Standards Constitution."""
        return test_factory.get_rules_by_constitution("Coding Standards")

    def test_constitution_has_rules(self, constitution_rules):
        """Test that Coding Standards Constitution has rules."""
        assert len(constitution_rules) > 0, "Coding Standards Constitution should have rules"

    @pytest.mark.parametrize("test_case",
                           [tc for tc in DynamicTestFactory().create_test_cases() if tc.constitution == 'Coding Standards'],
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_coding_standards_rules(self, test_case: DataTestCase):
        """Test all rules from Coding Standards Constitution."""
        assert test_case.constitution == "Coding Standards", f"Rule {test_case.rule_id} not from Coding Standards Constitution"

        # Coding Standards rules should be about code quality, security, or logging
        assert test_case.category in ['code_quality', 'security', 'logging'], \
            f"Coding Standards rule {test_case.rule_id} should be code_quality/security/logging category"

        # Should use appropriate validator
        if test_case.category == 'code_quality':
            assert 'code_quality_validator' in test_case.validator, \
                f"Coding Standards code quality rule {test_case.rule_id} should use code_quality_validator"
        elif test_case.category == 'security':
            assert 'security_validator' in test_case.validator, \
                f"Coding Standards security rule {test_case.rule_id} should use security_validator"
        elif test_case.category == 'logging':
            assert 'logging_validator' in test_case.validator, \
                f"Coding Standards logging rule {test_case.rule_id} should use logging_validator"

    def test_coding_standards_rule_coverage(self, constitution_rules):
        """Test that Coding Standards Constitution has expected rule types."""
        rule_ids = [rule['id'] for rule in constitution_rules]

        # Should have Python tools rule
        assert 'R027' in rule_ids, "Coding Standards Constitution should have Python tools rule (R027)"

        # Should have Python runtime rule
        assert 'R028' in rule_ids, "Coding Standards Constitution should have Python runtime rule (R028)"

        # Should have TypeScript strict rule
        assert 'R030' in rule_ids, "Coding Standards Constitution should have TypeScript strict rule (R030)"

        # Should have structured logs rule
        assert 'R043' in rule_ids, "Coding Standards Constitution should have structured logs rule (R043)"

        # Should have test coverage rule
        assert 'R045' in rule_ids, "Coding Standards Constitution should have test coverage rule (R045)"


class TestCommentsConstitution:
    """Test all rules from the Comments Constitution."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.fixture(scope="class")
    def constitution_rules(self, test_factory):
        """Get all rules from Comments Constitution."""
        return test_factory.get_rules_by_constitution("Comments")

    def test_constitution_has_rules(self, constitution_rules):
        """Test that Comments Constitution has rules."""
        assert len(constitution_rules) > 0, "Comments Constitution should have rules"

    @pytest.mark.parametrize("test_case",
                           [tc for tc in DynamicTestFactory().create_test_cases() if tc.constitution == 'Comments'],
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_comments_rules(self, test_case: DataTestCase):
        """Test all rules from Comments Constitution."""
        assert test_case.constitution == "Comments", f"Rule {test_case.rule_id} not from Comments Constitution"

        # Comments rules should be about documentation
        assert test_case.category == 'documentation', f"Comments rule {test_case.rule_id} should be documentation category"

        # Should use comment_validator
        assert 'comment_validator' in test_case.validator, \
            f"Comments rule {test_case.rule_id} should use comment_validator"

    def test_comments_rule_coverage(self, constitution_rules):
        """Test that Comments Constitution has expected rule types."""
        rule_ids = [rule['id'] for rule in constitution_rules]

        # Should have short sentences rule
        assert 'R046' in rule_ids, "Comments Constitution should have short sentences rule (R046)"

        # Should have file headers rule
        assert 'R047' in rule_ids, "Comments Constitution should have file headers rule (R047)"

        # Should have function documentation rule
        assert 'R049' in rule_ids, "Comments Constitution should have function documentation rule (R049)"

        # Should have TODO policy rule
        assert 'R089' in rule_ids, "Comments Constitution should have TODO policy rule (R089)"


class TestFolderStandardsConstitution:
    """Test all rules from the Folder Standards Constitution."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.fixture(scope="class")
    def constitution_rules(self, test_factory):
        """Get all rules from Folder Standards Constitution."""
        return test_factory.get_rules_by_constitution("Folder Standards")

    def test_constitution_has_rules(self, constitution_rules):
        """Test that Folder Standards Constitution has rules."""
        assert len(constitution_rules) > 0, "Folder Standards Constitution should have rules"

    @pytest.mark.parametrize("test_case",
                           [tc for tc in DynamicTestFactory().create_test_cases() if tc.constitution == 'Folder Standards'],
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_folder_standards_rules(self, test_case: DataTestCase):
        """Test all rules from Folder Standards Constitution."""
        assert test_case.constitution == "Folder Standards", f"Rule {test_case.rule_id} not from Folder Standards Constitution"

        # Folder Standards rules should be about structure
        assert test_case.category == 'structure', f"Folder Standards rule {test_case.rule_id} should be structure category"

        # Should use structure_validator
        assert 'structure_validator' in test_case.validator, \
            f"Folder Standards rule {test_case.rule_id} should use structure_validator"

    def test_folder_standards_rule_coverage(self, constitution_rules):
        """Test that Folder Standards Constitution has expected rule types."""
        rule_ids = [rule['id'] for rule in constitution_rules]

        # Should have ZEROUI_ROOT paths rule
        assert 'R054' in rule_ids, "Folder Standards Constitution should have ZEROUI_ROOT paths rule (R054)"

        # Should have allowlisted directories rule
        assert 'R055' in rule_ids, "Folder Standards Constitution should have allowlisted directories rule (R055)"

        # Should have server names rule
        assert 'R056' in rule_ids, "Folder Standards Constitution should have server names rule (R056)"

        # Should have junction persistence rule
        assert 'R057' in rule_ids, "Folder Standards Constitution should have junction persistence rule (R057)"


class TestLoggingConstitution:
    """Test all rules from the Logging Constitution."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.fixture(scope="class")
    def constitution_rules(self, test_factory):
        """Get all rules from Logging Constitution."""
        return test_factory.get_rules_by_constitution("Logging")

    def test_constitution_has_rules(self, constitution_rules):
        """Test that Logging Constitution has rules."""
        assert len(constitution_rules) > 0, "Logging Constitution should have rules"

    @pytest.mark.parametrize("test_case",
                           [tc for tc in DynamicTestFactory().create_test_cases() if tc.constitution == 'Logging'],
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_logging_rules(self, test_case: DataTestCase):
        """Test all rules from Logging Constitution."""
        assert test_case.constitution == "Logging", f"Rule {test_case.rule_id} not from Logging Constitution"

        # Logging rules should be about logging
        assert test_case.category == 'logging', f"Logging rule {test_case.rule_id} should be logging category"

        # Should use logging_validator
        assert 'logging_validator' in test_case.validator, \
            f"Logging rule {test_case.rule_id} should use logging_validator"

    def test_logging_rule_coverage(self, constitution_rules):
        """Test that Logging Constitution has expected rule types."""
        rule_ids = [rule['id'] for rule in constitution_rules]

        # Should have JSONL format rule
        assert 'R063' in rule_ids, "Logging Constitution should have JSONL format rule (R063)"

        # Should have ISO-8601 timestamps rule
        assert 'R064' in rule_ids, "Logging Constitution should have ISO-8601 timestamps rule (R064)"

        # Should have required log fields rule
        assert 'R067' in rule_ids, "Logging Constitution should have required log fields rule (R067)"

        # Should have W3C trace context rule
        assert 'R068' in rule_ids, "Logging Constitution should have W3C trace context rule (R068)"

        # Should have stable event names rule
        assert 'R069' in rule_ids, "Logging Constitution should have stable event names rule (R069)"


class TestConstitutionCoverage:
    """Test overall Constitution coverage and organization."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    def test_all_constitutions_have_rules(self, test_factory):
        """Test that all constitutions have rules."""
        constitutions = test_factory.get_constitutions()
        expected_constitutions = [
            "Code Review", "API Contracts", "Coding Standards",
            "Comments", "Folder Standards", "Logging"
        ]

        for constitution in expected_constitutions:
            assert constitution in constitutions, f"Constitution '{constitution}' not found"
            rules = test_factory.get_rules_by_constitution(constitution)
            assert len(rules) > 0, f"Constitution '{constitution}' has no rules"

    def test_constitution_rule_distribution(self, test_factory):
        """Test that rules are distributed across constitutions."""
        constitutions = test_factory.get_constitutions()

        # Each constitution should have a reasonable number of rules
        for constitution in constitutions:
            rules = test_factory.get_rules_by_constitution(constitution)
            assert len(rules) >= 3, f"Constitution '{constitution}' should have at least 3 rules"
            assert len(rules) <= 30, f"Constitution '{constitution}' should have at most 30 rules"

    def test_no_orphaned_rules(self, test_factory):
        """Test that all rules belong to a constitution."""
        all_rules = test_factory.get_all_rules()
        constitutions = test_factory.get_constitutions()

        for rule in all_rules:
            constitution = rule.get('constitution', '')
            assert constitution in constitutions, f"Rule {rule['id']} has invalid constitution: {constitution}"
            assert constitution, f"Rule {rule['id']} has no constitution"

    def test_constitution_category_alignment(self, test_factory):
        """Test that constitution rules align with expected categories."""
        constitution_category_map = {
            "Code Review": ['scope', 'governance', 'process', 'quality', 'security'],
            "API Contracts": ['api'],
            "Coding Standards": ['code_quality', 'security', 'logging'],
            "Comments": ['documentation'],
            "Folder Standards": ['structure'],
            "Logging": ['logging']
        }

        for constitution, expected_categories in constitution_category_map.items():
            rules = test_factory.get_rules_by_constitution(constitution)
            rule_categories = {rule.get('category') for rule in rules}

            for rule in rules:
                rule_category = rule.get('category')
                assert rule_category in expected_categories, \
                    f"Rule {rule['id']} in {constitution} has unexpected category: {rule_category}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
