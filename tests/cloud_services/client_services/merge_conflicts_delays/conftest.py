"""
Test fixtures for Merge Conflicts Delays.

Module-specific fixtures and test utilities.
"""
import pytest
from pathlib import Path
import sys

# Add module to path for imports
MODULE_ROOT = Path(__file__).resolve().parents[3] / "src" / "cloud_services" / "client-services" / "merge-conflicts-delays"
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

