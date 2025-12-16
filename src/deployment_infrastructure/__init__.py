"""
Shim package for the deployment-infrastructure module, enabling
``import deployment_infrastructure``.
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
        / "deployment-infrastructure"
    )
    init_file = package_dir / "__init__.py"

    if not package_dir.is_dir():
        raise ImportError(f"deployment-infrastructure package directory not found at {package_dir}")
    if not init_file.is_file():
        raise ImportError(f"__init__.py missing for deployment-infrastructure at {init_file}")

    spec = importlib.util.spec_from_file_location(
        __name__,
        init_file,
        submodule_search_locations=[str(package_dir)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load deployment-infrastructure package from {package_dir}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[__name__] = module
    spec.loader.exec_module(module)

    globals().update(module.__dict__)


_load_package()
