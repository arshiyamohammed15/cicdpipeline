"""
Shim for tests expecting database.models from budgeting_rate_limiting_cost_observability.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _ensure_pkg(name: str, path: Path) -> types.ModuleType:
    pkg = sys.modules.get(name)
    if pkg is None:
        pkg = types.ModuleType(name)
        sys.modules[name] = pkg
    pkg.__path__ = [str(path)]
    return pkg


def _load_real():
    root = Path(__file__).resolve().parents[1] / "src" / "cloud_services" / "shared-services" / "budgeting-rate-limiting-cost-observability"
    db_root = root / "database"
    _ensure_pkg("budgeting_rate_limiting_cost_observability", root)
    _ensure_pkg("budgeting_rate_limiting_cost_observability.database", db_root)

    real_path = db_root / "models.py"
    if not real_path.exists():
        raise FileNotFoundError(f"Real models module not found at {real_path}")
    spec = importlib.util.spec_from_file_location(
        "budgeting_rate_limiting_cost_observability.database.models",
        real_path,
        submodule_search_locations=[str(db_root)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {real_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["budgeting_rate_limiting_cost_observability.database.models"] = module
    spec.loader.exec_module(module)
    return module


_real = _load_real()
globals().update(_real.__dict__)

__all__ = [name for name in _real.__dict__ if not name.startswith("_")]

