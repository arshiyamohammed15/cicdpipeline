"""
Shim package for the data-governance-privacy module.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_package() -> None:
    package_dir = (
        Path(__file__).resolve()
        .parent.parent
        / "cloud_services"
        / "shared-services"
        / "data-governance-privacy"
    )
    init_file = package_dir / "__init__.py"

    if not package_dir.is_dir():
        raise ImportError(f"data-governance-privacy package directory not found at {package_dir}")
    if not init_file.is_file():
        raise ImportError(f"data-governance-privacy __init__.py missing at {init_file}")

    spec = importlib.util.spec_from_file_location(
        __name__,
        init_file,
        submodule_search_locations=[str(package_dir)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load data-governance-privacy package from {package_dir}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[__name__] = module
    spec.loader.exec_module(module)

    globals().update(module.__dict__)


_load_package()
