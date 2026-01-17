#!/usr/bin/env python3
"""
CI Validation Script for Phase 4 Observability Implementation.

Validates OBS-18: Challenge Traceability Gates
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))

from shared_libs.zeroui_observability.governance.ci_validator import validate_challenge_traceability


def main() -> int:
    """Main entry point."""
    return validate_challenge_traceability()


if __name__ == "__main__":
    sys.exit(main())
