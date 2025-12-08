"""
Test shim that loads the real KMS main module from src/.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_real_main():
    root = Path(__file__).resolve().parents[5] / "src" / "cloud_services" / "shared-services" / "key-management-service"
    real_main = root / "main.py"
    if not real_main.exists():
        raise FileNotFoundError(f"Real main module not found at {real_main}")

    pkg_name = "key_management_service"
    pkg = types.ModuleType(pkg_name)
    pkg.__path__ = [str(root)]
    sys.modules[pkg_name] = pkg

    routes_path = root / "routes.py"
    spec_routes = importlib.util.spec_from_file_location(f"{pkg_name}.routes", routes_path)
    routes_mod = importlib.util.module_from_spec(spec_routes)
    sys.modules[f"{pkg_name}.routes"] = routes_mod
    spec_routes.loader.exec_module(routes_mod)

    spec = importlib.util.spec_from_file_location(f"{pkg_name}.main_real", real_main)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {real_main}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{pkg_name}.main_real"] = module
    spec.loader.exec_module(module)
    return module


_real = _load_real_main()
create_app = getattr(_real, "create_app", None)
app = getattr(_real, "app", None)

__all__ = [name for name in ("create_app", "app") if name in globals()]

