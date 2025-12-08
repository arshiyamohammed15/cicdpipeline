"""
Test shim that loads the real SIN main module from src/.
This satisfies integration tests that look for tests/src/.../main.py.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_real_main():
    root = Path(__file__).resolve().parents[5] / "src" / "cloud_services" / "product_services" / "signal-ingestion-normalization"
    if not root.exists():
        raise FileNotFoundError(f"Real module root not found at {root}")

    pkg_name = "signal_ingestion_normalization"
    pkg = sys.modules.get(pkg_name)
    if pkg is None or not hasattr(pkg, "__path__"):
        pkg = types.ModuleType(pkg_name)
        sys.modules[pkg_name] = pkg
    pkg.__path__ = [str(root)]

    real_main = root / "main.py"
    if not real_main.exists():
        raise FileNotFoundError(f"Real main module not found at {real_main}")

    # Load the real main module under the expected package name.
    spec = importlib.util.spec_from_file_location(f"{pkg_name}.main", real_main)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {real_main}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{pkg_name}.main"] = module
    spec.loader.exec_module(module)
    return module


_real = _load_real_main()

# Re-export expected attributes
create_app = getattr(_real, "create_app", None)
app = getattr(_real, "app", None)

# Provide aliases for any other attributes that might be accessed
__all__ = [name for name in ("create_app", "app") if name in globals()]

