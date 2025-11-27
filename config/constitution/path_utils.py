#!/usr/bin/env python3
"""
Path utilities for ZeroUI constitution storage.

Ensures that mutable storage artifacts (SQLite DB, logs, etc.) are always
redirected to external locations outside the repository tree, following the
folder-business rules. This module centralizes the resolution logic so every
caller lands on the same sanctioned path.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]


def _fallback_root() -> Path:
    """Platform-aware fallback root outside the repository."""
    if os.name == "nt":
        return Path("D:/ZeroUI").resolve()
    return (Path.home() / "ZeroUI").resolve()


def _default_zu_root() -> Path:
    """Return the preferred ZU_ROOT base (env override if it is safe)."""
    env_root = os.environ.get("ZU_ROOT")
    if env_root:
        candidate = Path(env_root).expanduser().resolve()
        if not _is_inside_repo(candidate):
            return candidate

    return _fallback_root()


def _default_storage_dir() -> Path:
    """Return the default directory that should contain SQLite artifacts."""
    return (_default_zu_root() / "ide" / "db").resolve()


def _is_inside_repo(path: Path) -> bool:
    """Check whether a path is inside the repository tree."""
    try:
        path.relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


def _ensure_external(path: Path) -> Path:
    """Ensure the given path resides outside the repository."""
    if _is_inside_repo(path):
        return (_default_storage_dir() / path.name).resolve()
    return path


def resolve_constitution_db_path(candidate: Optional[str]) -> Path:
    """
    Resolve the SQLite database path, guaranteeing it sits outside the repo.

    Resolution order:
      1. CONSTITUTION_DB_PATH env var
      2. Candidate argument (absolute paths win; relative paths use filename only)
      3. Fallback to `${ZU_ROOT}/ide/db/constitution_rules.db`
    """
    env_override = os.environ.get("CONSTITUTION_DB_PATH")
    if env_override:
        path = Path(env_override).expanduser()
    elif candidate:
        path = Path(candidate).expanduser()
    else:
        path = Path("constitution_rules.db")

    if not path.is_absolute():
        # Drop any relative parents (e.g., "config/…") and reuse the filename.
        path = _default_storage_dir() / path.name

    path = path.resolve()
    path = _ensure_external(path)

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def resolve_alerting_db_path(candidate: Optional[str] = None) -> Path:
    """
    Resolve the Alerting & Notification Service database path, guaranteeing it sits outside the repo.

    Resolution order:
      1. ALERTING_DB_PATH env var
      2. Candidate argument (absolute paths win; relative paths use filename only)
      3. Fallback to `${ZU_ROOT}/ide/db/alerting.db`
    """
    env_override = os.environ.get("ALERTING_DB_PATH")
    if env_override:
        path = Path(env_override).expanduser()
    elif candidate:
        path = Path(candidate).expanduser()
    else:
        path = Path("alerting.db")

    if not path.is_absolute():
        # Drop any relative parents and reuse the filename.
        path = _default_storage_dir() / path.name

    path = path.resolve()
    path = _ensure_external(path)

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def resolve_health_reliability_monitoring_db_path(candidate: Optional[str] = None) -> Path:
    """
    Resolve the Health & Reliability Monitoring database path, guaranteeing it sits outside the repo.

    Resolution order:
      1. HEALTH_RELIABILITY_MONITORING_DB_PATH env var
      2. Candidate argument (absolute paths win; relative paths use filename only)
      3. Fallback to `${ZU_ROOT}/ide/db/health_reliability_monitoring.db`
    """
    env_override = os.environ.get("HEALTH_RELIABILITY_MONITORING_DB_PATH")
    if env_override:
        path = Path(env_override).expanduser()
    elif candidate:
        path = Path(candidate).expanduser()
    else:
        path = Path("health_reliability_monitoring.db")

    if not path.is_absolute():
        # Drop any relative parents and reuse the filename.
        path = _default_storage_dir() / path.name

    path = path.resolve()
    path = _ensure_external(path)

    path.parent.mkdir(parents=True, exist_ok=True)
    return path
