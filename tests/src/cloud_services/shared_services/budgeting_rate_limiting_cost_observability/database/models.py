"""
Shim for budgeting_rate_limiting_cost_observability database models in tests.
Resolves to the real module under src/cloud_services/shared_services/budgeting-rate-limiting-cost-observability/database/models.py.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_real():
    root = Path(__file__).resolve().parents[5] / "src" / "cloud_services" / "shared-services" / "budgeting-rate-limiting-cost-observability" / "database"
    real_path = root / "models.py"
    if not real_path.exists():
        raise FileNotFoundError(f"Real models module not found at {real_path}")

    spec = importlib.util.spec_from_file_location("budgeting_rate_limiting_cost_observability.database.models", real_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {real_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["database.models"] = module
    sys.modules["budgeting_rate_limiting_cost_observability.database.models"] = module
    spec.loader.exec_module(module)
    return module


_real = _load_real()

globals().update(_real.__dict__)

__all__ = [name for name in _real.__dict__ if not name.startswith("_")]

