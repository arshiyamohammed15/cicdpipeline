"""
Tests for Challenge Traceability Matrix.

OBS-18: Challenge traceability validation tests.
"""

import json
import tempfile
import unittest
from pathlib import Path

from ..challenge_traceability_matrix import ChallengeMapping, ChallengeTraceabilityMatrix, load_matrix
from ..ci_validator import validate_challenge_traceability


class TestChallengeTraceability(unittest.TestCase):
    """Test challenge traceability matrix."""

    def test_load_matrix(self):
        """Test loading traceability matrix."""
        matrix = load_matrix()
        self.assertIsNotNone(matrix)
        self.assertEqual(len(matrix.get_all_challenges()), 20)

    def test_validate_matrix(self):
        """Test matrix validation."""
        matrix = load_matrix()
        result = matrix.validate()

        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["challenge_count"], 20)

    def test_get_challenge(self):
        """Test getting challenge by ID."""
        matrix = load_matrix()
        challenge = matrix.get_challenge(1)

        self.assertIsNotNone(challenge)
        self.assertEqual(challenge.challenge_id, 1)
        self.assertEqual(challenge.challenge_name, "LLM Error Analysis Challenges")
        self.assertIn("error.captured.v1", challenge.signals)
        self.assertIn("D2", challenge.dashboards)

    def test_validate_challenge_mapping(self):
        """Test challenge mapping validation."""
        # Valid challenge
        challenge = ChallengeMapping(
            challenge_id=1,
            challenge_name="Test Challenge",
            signals=["signal1"],
            dashboards=["D1"],
            alerts=["A1"],
            acceptance_tests=["AT-1"],
        )
        errors = challenge.validate()
        self.assertEqual(len(errors), 0)

        # Invalid challenge (missing signals)
        challenge_invalid = ChallengeMapping(
            challenge_id=2,
            challenge_name="Invalid Challenge",
            signals=[],
            dashboards=["D1"],
            alerts=[],
            acceptance_tests=[],
        )
        errors = challenge_invalid.validate()
        self.assertGreater(len(errors), 0)

    def test_validate_invalid_matrix(self):
        """Test validation of invalid matrix."""
        # Create temporary invalid matrix
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            invalid_matrix = {
                "version": "1.0",
                "challenges": [
                    {
                        "challenge_id": 1,
                        "challenge_name": "Test Challenge",
                        "signals": [],  # Missing signals
                        "dashboards": ["D1"],
                        "alerts": [],
                        "acceptance_tests": [],
                    },
                ],
            }
            json.dump(invalid_matrix, f)
            temp_path = Path(f.name)

        try:
            matrix = ChallengeTraceabilityMatrix(matrix_path=temp_path)
            result = matrix.validate()
            self.assertFalse(result["valid"])
            self.assertGreater(len(result["errors"]), 0)
        finally:
            temp_path.unlink()

    def test_ci_validator(self):
        """Test CI validator."""
        exit_code = validate_challenge_traceability()
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
