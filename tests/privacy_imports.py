"""
Utility helpers to import modules from the hyphenated data-governance-privacy path.
"""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MODULE_ROOT = PROJECT_ROOT / "src" / "cloud-services" / "shared-services" / "data-governance-privacy"
PACKAGE_NAME = "data_governance_privacy"


def _ensure_package_registered() -> None:
    if PACKAGE_NAME in sys.modules:
        return
    package = types.ModuleType(PACKAGE_NAME)
    package.__path__ = [str(MODULE_ROOT)]  # type: ignore[attr-defined]
    sys.modules[PACKAGE_NAME] = package


def import_module(module_suffix: str):
    """
    Import module under the synthetic data_governance_privacy package.

    Args:
        module_suffix: e.g., "services", "main"
    """
    _ensure_package_registered()
    full_name = f"{PACKAGE_NAME}.{module_suffix}"
    return importlib.import_module(full_name)
