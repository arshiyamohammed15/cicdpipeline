"""
Shim package that proxies the real key-management-service package located in
cloud_services/shared-services/key-management-service.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

_TARGET_RELATIVE = (
    "cloud_services",
    "shared-services",
    "key-management-service",
)


def _target_package_dir() -> Path:
    return Path(__file__).resolve().parent.parent.joinpath(*_TARGET_RELATIVE)


def _load_package() -> ModuleType:
    package_dir = _target_package_dir()
    init_file = package_dir / "__init__.py"

    if not package_dir.exists():
        raise ImportError(f"Key management service package directory not found at {package_dir}")
    if not init_file.exists():
        raise ImportError(f"Key management service __init__.py missing at {init_file}")

    try:
        spec = importlib.util.spec_from_file_location(
            __name__, init_file, submodule_search_locations=[str(package_dir)]
        )
    except Exception as exc:
        raise ImportError(f"Failed to create import spec for key management service at {init_file}") from exc

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load key management service package: invalid spec from {init_file}")

    module = importlib.util.module_from_spec(spec)
    shim_module = sys.modules.get(__name__)
    sys.modules[__name__] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        if shim_module is not None:
            sys.modules[__name__] = shim_module
        else:
            sys.modules.pop(__name__, None)
        raise ImportError(f"Failed to execute key management service module at {init_file}") from exc
    else:
        if shim_module is not None:
            sys.modules[__name__] = shim_module
        else:
            sys.modules.pop(__name__, None)

    return module


_module = _load_package()
__all__ = getattr(_module, "__all__", tuple())


def __getattr__(name: str) -> Any:
    return getattr(_module, name)


def __dir__() -> list[str]:
    return sorted(set(__all__) if __all__ else dir(_module))
