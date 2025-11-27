"""
Repository-level pytest configuration.

Ensures the top-level ``src`` directory is on ``sys.path`` so shim packages
(e.g., ``budgeting_rate_limiting_cost_observability``) resolve correctly.
"""

from __future__ import annotations

import sys
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parent / "src"
SRC_STR = str(SRC_PATH)
if SRC_STR not in sys.path:
    sys.path.insert(0, SRC_STR)


