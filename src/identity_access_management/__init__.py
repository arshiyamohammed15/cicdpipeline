"""
Shim package for the identity-access-management module.
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
        / "identity-access-management"
    )
    init_file = package_dir / "__init__.py"

    spec = importlib.util.spec_from_file_location(
        __name__,
        init_file,
        submodule_search_locations=[str(package_dir)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load identity-access-management package from {package_dir}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[__name__] = module
    spec.loader.exec_module(module)

    globals().update(module.__dict__)


_load_package()
