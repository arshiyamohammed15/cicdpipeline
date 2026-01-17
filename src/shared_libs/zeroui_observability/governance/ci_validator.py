"""
CI Validator for Challenge Traceability Matrix.

OBS-18: CI validation script that fails if any challenge lacks required mappings.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .challenge_traceability_matrix import ChallengeTraceabilityMatrix, load_matrix

logger = logging.getLogger(__name__)


def validate_challenge_traceability(
    matrix_path: Optional[Path] = None,
    fail_on_warnings: bool = False,
) -> int:
    """
    Validate challenge traceability matrix.

    Args:
        matrix_path: Optional path to matrix JSON file
        fail_on_warnings: Whether to fail on warnings (default: False)

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        matrix = load_matrix(matrix_path)
        result = matrix.validate()

        if not result["valid"]:
            logger.error("Challenge traceability validation FAILED")
            for error in result["errors"]:
                logger.error(f"  ERROR: {error}")
            return 1

        if result["warnings"]:
            logger.warning("Challenge traceability validation passed with warnings")
            for warning in result["warnings"]:
                logger.warning(f"  WARNING: {warning}")

            if fail_on_warnings:
                logger.error("Failing due to warnings (fail_on_warnings=True)")
                return 1
        else:
            logger.info("Challenge traceability validation PASSED")

        logger.info(f"Validated {result['challenge_count']} challenges (matrix v{result['version']})")

        return 0

    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        return 1


def main() -> int:
    """
    Main entry point for CI validator.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate challenge traceability matrix")
    parser.add_argument(
        "--matrix-path",
        type=Path,
        help="Path to challenge traceability matrix JSON file",
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Fail validation if warnings are present",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    return validate_challenge_traceability(
        matrix_path=args.matrix_path,
        fail_on_warnings=args.fail_on_warnings,
    )


if __name__ == "__main__":
    sys.exit(main())
