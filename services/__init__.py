"""
Shim package for services imports in tests. Routes to budgeting-rate-limiting-cost-observability services.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_real_package():
    root = Path(__file__).resolve().parents[1] / "src" / "cloud_services" / "shared-services" / "budgeting-rate-limiting-cost-observability" / "services"
    if not root.exists():
        return None

    pkg_name = "budgeting_rate_limiting_cost_observability.services"
    base_name = "budgeting_rate_limiting_cost_observability"

    # Ensure base package exists
    base_root = root.parent
    base_pkg = sys.modules.get(base_name)
    if base_pkg is None:
        base_pkg = types.ModuleType(base_name)
        sys.modules[base_name] = base_pkg
    base_pkg.__path__ = [str(base_root)]

    real_pkg = sys.modules.get(pkg_name)
    if real_pkg is None:
        spec = importlib.util.spec_from_file_location(pkg_name, root / "__init__.py")
        if spec and spec.loader:
            real_pkg = importlib.util.module_from_spec(spec)
            sys.modules[pkg_name] = real_pkg
            spec.loader.exec_module(real_pkg)

    shim_pkg = types.ModuleType("services")
    shim_pkg.__path__ = [str(Path(__file__).parent), str(root)]
    if real_pkg:
        shim_pkg.__dict__.update(getattr(real_pkg, "__dict__", {}))
    sys.modules["services"] = shim_pkg
    return shim_pkg


_load_real_package()

