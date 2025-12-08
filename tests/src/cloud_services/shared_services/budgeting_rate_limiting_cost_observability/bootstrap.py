"""
Bootstrap helpers to load budgeting-rate-limiting-cost-observability modules with
stable package names for tests (handles hyphenated directory names).
"""

from __future__ import annotations

import importlib.machinery
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
    pkg.__spec__ = importlib.machinery.ModuleSpec(name, loader=None, is_package=True)
    return pkg


def _load_mod(name: str, path: Path, package: str | None = None) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__file__ = str(path)
    if package:
        module.__package__ = package
    sys.modules[name] = module
    with open(path, "r", encoding="utf-8") as fh:
        code = fh.read()
    exec(compile(code, str(path), "exec"), module.__dict__)
    return module


def ensure_brlco():
    root = Path(__file__).resolve().parents[5] / "src" / "cloud_services" / "shared-services" / "budgeting-rate-limiting-cost-observability"
    services_root = root / "services"
    database_root = root / "database"
    utils_root = root / "utils"

    base_pkg = _ensure_pkg("budgeting_rate_limiting_cost_observability", root)
    services_pkg = _ensure_pkg("budgeting_rate_limiting_cost_observability.services", services_root)
    database_pkg = _ensure_pkg("budgeting_rate_limiting_cost_observability.database", database_root)
    utils_pkg = _ensure_pkg("budgeting_rate_limiting_cost_observability.utils", utils_root)

    # Alias short names expected by tests
    sys.modules["services"] = services_pkg
    sys.modules["database"] = sys.modules.get("database") or types.ModuleType("database")
    sys.modules["database.models"] = sys.modules.get("database.models") or types.ModuleType("database.models")

    # Load dependencies first
    deps_module = _load_mod(
        "budgeting_rate_limiting_cost_observability.dependencies",
        root / "dependencies.py",
        package="budgeting_rate_limiting_cost_observability",
    )
    sys.modules["budgeting_rate_limiting_cost_observability.services.dependencies"] = deps_module
    sys.modules["services.dependencies"] = deps_module
    sys.modules["dependencies"] = deps_module

    db_module = _load_mod(
        "budgeting_rate_limiting_cost_observability.database.models",
        database_root / "models.py",
        package="budgeting_rate_limiting_cost_observability.database",
    )
    sys.modules["budgeting_rate_limiting_cost_observability.services.database.models"] = db_module
    sys.modules["database.models"] = db_module

    cache_module = _load_mod(
        "budgeting_rate_limiting_cost_observability.utils.cache",
        utils_root / "cache.py",
        package="budgeting_rate_limiting_cost_observability.utils",
    )
    sys.modules["budgeting_rate_limiting_cost_observability.services.utils.cache"] = cache_module

    txn_module = _load_mod(
        "budgeting_rate_limiting_cost_observability.utils.transactions",
        utils_root / "transactions.py",
        package="budgeting_rate_limiting_cost_observability.utils",
    )
    sys.modules["budgeting_rate_limiting_cost_observability.services.utils.transactions"] = txn_module

    event_service_module = _load_mod(
        "budgeting_rate_limiting_cost_observability.services.event_service",
        services_root / "event_service.py",
        package="budgeting_rate_limiting_cost_observability.services",
    )
    sys.modules["budgeting_rate_limiting_cost_observability.services.budget_service.event_service"] = event_service_module
    sys.modules["budgeting_rate_limiting_cost_observability.services.rate_limit_service.event_service"] = event_service_module

    budget_module = _load_mod(
        "budgeting_rate_limiting_cost_observability.services.budget_service",
        services_root / "budget_service.py",
        package="budgeting_rate_limiting_cost_observability.services",
    )
    rate_limit_module = _load_mod(
        "budgeting_rate_limiting_cost_observability.services.rate_limit_service",
        services_root / "rate_limit_service.py",
        package="budgeting_rate_limiting_cost_observability.services",
    )

    # Aliases for test imports
    services_pkg.BudgetService = budget_module.BudgetService
    services_pkg.RateLimitService = rate_limit_module.RateLimitService
    sys.modules["services.budget_service"] = budget_module
    sys.modules["services.rate_limit_service"] = rate_limit_module
    sys.modules["budgeting_rate_limiting_cost_observability.services.budget_service"] = budget_module
    sys.modules["budgeting_rate_limiting_cost_observability.services.rate_limit_service"] = rate_limit_module

    return {
        "BudgetService": budget_module.BudgetService,
        "RateLimitService": rate_limit_module.RateLimitService,
        "MockM29DataPlane": deps_module.MockM29DataPlane,
        "Base": db_module.Base,
    }

