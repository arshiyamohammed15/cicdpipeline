"""
Shim to route services.budget_service imports to the budgeting-rate-limiting-cost-observability implementation.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
import runpy


def _ensure_pkg(name: str, path: Path) -> types.ModuleType:
    pkg = sys.modules.get(name)
    if pkg is None:
        pkg = types.ModuleType(name)
        sys.modules[name] = pkg
    pkg.__path__ = [str(path)]
    return pkg


def _load_real():
    root = Path(__file__).resolve().parents[1] / "src" / "cloud_services" / "shared-services" / "budgeting-rate-limiting-cost-observability"
    services_root = root / "services"
    database_root = root / "database"
    utils_root = root / "utils"

    _ensure_pkg("budgeting_rate_limiting_cost_observability", root)
    _ensure_pkg("budgeting_rate_limiting_cost_observability.services", services_root)
    _ensure_pkg("budgeting_rate_limiting_cost_observability.database", database_root)
    _ensure_pkg("budgeting_rate_limiting_cost_observability.utils", utils_root)

    def _load_dep(mod_name: str, path: Path):
        spec = importlib.util.spec_from_file_location(mod_name, path, submodule_search_locations=[str(path.parent)])
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)
            return module
        raise ImportError(f"Cannot load dependency {mod_name} from {path}")

    # Preload modules used by budget_service relative imports.
    _load_dep("budgeting_rate_limiting_cost_observability.database.models", database_root / "models.py")
    _load_dep("budgeting_rate_limiting_cost_observability.dependencies", root / "dependencies.py")
    _load_dep("budgeting_rate_limiting_cost_observability.utils.cache", utils_root / "cache.py")
    _load_dep("budgeting_rate_limiting_cost_observability.utils.transactions", utils_root / "transactions.py")
    event_mod = _load_dep("budgeting_rate_limiting_cost_observability.services.event_service", services_root / "event_service.py")
    sys.modules["budgeting_rate_limiting_cost_observability.services.budget_service.event_service"] = event_mod

    real_path = services_root / "budget_service.py"
    if not real_path.exists():
        raise FileNotFoundError(f"Real budget_service not found at {real_path}")

    name = "budgeting_rate_limiting_cost_observability.services.budget_service"
    module = types.ModuleType(name)
    module.__file__ = str(real_path)
    module.__package__ = "budgeting_rate_limiting_cost_observability.services"
    module.__path__ = [str(services_root)]
    sys.modules[name] = module
    runpy.run_path(str(real_path), init_globals=module.__dict__)
    return module


_real = _load_real()
globals().update(_real.__dict__)

__all__ = [name for name in _real.__dict__ if not name.startswith("_")]

