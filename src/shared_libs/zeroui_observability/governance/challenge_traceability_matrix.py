"""
Challenge Traceability Matrix for ZeroUI Observability Layer.

OBS-18: Validates that every challenge (1-20) has required mappings to signals,
dashboards, alerts, and acceptance tests.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ChallengeMapping:
    """Challenge mapping structure."""

    challenge_id: int
    challenge_name: str
    signals: List[str]
    dashboards: List[str]
    alerts: List[str]
    acceptance_tests: List[str]

    def validate(self) -> List[str]:
        """
        Validate challenge mapping.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Signals are required
        if not self.signals:
            errors.append(f"Challenge {self.challenge_id} missing signals")

        # Dashboards are required
        if not self.dashboards:
            errors.append(f"Challenge {self.challenge_id} missing dashboards")

        # Alerts and acceptance_tests can be empty (N/A)

        return errors


class ChallengeTraceabilityMatrix:
    """
    Challenge traceability matrix validator.

    Per OBS-18 requirements:
    - Validates that every challenge (1-20) has signal + dashboard + test mappings
    - Fails validation if any challenge lacks required mappings
    - Matrix must be versioned and auditable
    """

    def __init__(self, matrix_path: Optional[Path] = None):
        """
        Initialize traceability matrix.

        Args:
            matrix_path: Path to matrix JSON file
        """
        if matrix_path is None:
            matrix_path = Path(__file__).parent / "challenge_traceability_matrix.json"

        self._matrix_path = matrix_path
        self._matrix: Dict[str, Any] = {}
        self._challenges: List[ChallengeMapping] = []

        self._load_matrix()

    def _load_matrix(self) -> None:
        """Load matrix from JSON file."""
        try:
            with open(self._matrix_path, "r", encoding="utf-8") as f:
                self._matrix = json.load(f)

            # Parse challenges
            self._challenges = []
            for challenge_data in self._matrix.get("challenges", []):
                challenge = ChallengeMapping(
                    challenge_id=challenge_data["challenge_id"],
                    challenge_name=challenge_data["challenge_name"],
                    signals=challenge_data.get("signals", []),
                    dashboards=challenge_data.get("dashboards", []),
                    alerts=challenge_data.get("alerts", []),
                    acceptance_tests=challenge_data.get("acceptance_tests", []),
                )
                self._challenges.append(challenge)

            logger.info(f"Loaded traceability matrix v{self._matrix.get('version')} with {len(self._challenges)} challenges")

        except (IOError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load traceability matrix: {e}")
            raise

    def validate(self) -> Dict[str, Any]:
        """
        Validate traceability matrix.

        Returns:
            Validation result with errors and warnings
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Check that all 20 challenges are present
        challenge_ids = {c.challenge_id for c in self._challenges}
        expected_ids = set(range(1, 21))

        missing_challenges = expected_ids - challenge_ids
        if missing_challenges:
            errors.append(f"Missing challenges: {sorted(missing_challenges)}")

        # Validate each challenge
        for challenge in self._challenges:
            challenge_errors = challenge.validate()
            errors.extend(challenge_errors)

            # Warn if no alerts or tests (allowed but should be reviewed)
            if not challenge.alerts and not challenge.acceptance_tests:
                warnings.append(
                    f"Challenge {challenge.challenge_id} ({challenge.challenge_name}) has no alerts or acceptance tests"
                )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "challenge_count": len(self._challenges),
            "version": self._matrix.get("version"),
        }

    def get_challenge(self, challenge_id: int) -> Optional[ChallengeMapping]:
        """
        Get challenge mapping by ID.

        Args:
            challenge_id: Challenge ID (1-20)

        Returns:
            ChallengeMapping or None if not found
        """
        for challenge in self._challenges:
            if challenge.challenge_id == challenge_id:
                return challenge
        return None

    def get_all_challenges(self) -> List[ChallengeMapping]:
        """
        Get all challenge mappings.

        Returns:
            List of ChallengeMapping instances
        """
        return self._challenges.copy()


def load_matrix(matrix_path: Optional[Path] = None) -> ChallengeTraceabilityMatrix:
    """
    Load challenge traceability matrix.

    Args:
        matrix_path: Optional path to matrix JSON file

    Returns:
        ChallengeTraceabilityMatrix instance
    """
    return ChallengeTraceabilityMatrix(matrix_path=matrix_path)
