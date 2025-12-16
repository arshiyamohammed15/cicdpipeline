"""
Shim package that exposes the hyphenated configuration-policy-management module
under the import-friendly name ``configuration_policy_management``.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Final


_DEFAULT_PACKAGE_DIR: Final[Path] = (
    Path(__file__).resolve()
    .parent.parent
    / "cloud_services"
    / "shared-services"
    / "configuration-policy-management"
)


def _resolve_package_dir() -> Path:
    """Resolve the on-disk package directory, optionally honoring an override."""
    override = os.environ.get("CONFIGURATION_POLICY_MANAGEMENT_PATH")
    package_dir = Path(override).expanduser().resolve() if override else _DEFAULT_PACKAGE_DIR

    init_file = package_dir / "__init__.py"
    if not init_file.is_file():
        raise ImportError(
            f"configuration-policy-management package not found at {package_dir}. "
            "Set CONFIGURATION_POLICY_MANAGEMENT_PATH to a valid location."
        )

    return package_dir


def _load_package() -> None:
    package_dir = _resolve_package_dir()
    init_file = package_dir / "__init__.py"

    spec = importlib.util.spec_from_file_location(
        __name__,
        init_file,
        submodule_search_locations=[str(package_dir)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load configuration-policy-management package from {package_dir}")

    # Defer execution of the target package until first attribute access to
    # avoid accidental side effects at import time.
    spec.loader = importlib.util.LazyLoader(spec.loader)

    module = importlib.util.module_from_spec(spec)
    sys.modules[__name__] = module
    spec.loader.exec_module(module)

    globals().update(module.__dict__)


_load_package()
