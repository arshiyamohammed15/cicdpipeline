"""
Shim package for the identity-access-management module.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


def _resolve_package_dir() -> Path:
    """Resolve the identity-access-management package directory with an env override."""
    repo_root = Path(__file__).resolve().parents[3]
    env_override = os.environ.get("IDENTITY_ACCESS_MANAGEMENT_PATH")
    if env_override:
        env_path = Path(env_override).expanduser().resolve()
        try:
            env_path.relative_to(repo_root)
        except ValueError:
            raise ImportError(
                "IDENTITY_ACCESS_MANAGEMENT_PATH must point inside the repository "
                f"(under {repo_root}), not {env_path}"
            )

        if (env_path / "__init__.py").is_file():
            return env_path
        raise ImportError(
            "IDENTITY_ACCESS_MANAGEMENT_PATH is set but __init__.py was not found "
            f"at {env_path}"
        )

    default_path = (
        Path(__file__).resolve()
        .parent.parent
        / "cloud_services"
        / "shared-services"
        / "identity-access-management"
    )
    if (default_path / "__init__.py").is_file():
        return default_path

    raise ImportError(
        "Cannot locate identity-access-management package. "
        "Set IDENTITY_ACCESS_MANAGEMENT_PATH to the package directory (within the repo) "
        f"or place it at {default_path}"
    )


def _load_package() -> None:
    package_dir = _resolve_package_dir()
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
