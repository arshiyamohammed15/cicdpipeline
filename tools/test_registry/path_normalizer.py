"""
Path normalization helpers for the test framework.

Purpose:
- Keep the repository root at the front of sys.path so shared packages
  (e.g., `config`) resolve to the intended modules.
- Provide lightweight alias packages for hyphenated service directories,
  allowing imports such as `identity_access_management` to resolve into
  `src/cloud_services/shared-services/identity-access-management`.
"""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path
from typing import Iterable

# Mapping of on-disk hyphenated service directories to import-safe names.
MODULE_MAPPINGS = {
    # Shared services
    "identity-access-management": "identity_access_management",
    "key-management-service": "key_management_service",
    "alerting-notification-service": "alerting_notification_service",
    "budgeting-rate-limiting-cost-observability": "budgeting_rate_limiting_cost_observability",
    "configuration-policy-management": "configuration_policy_management",
    "contracts-schema-registry": "contracts_schema_registry",
    "data-governance-privacy": "data_governance_privacy",
    "deployment-infrastructure": "deployment_infrastructure",
    "evidence-receipt-indexing-service": "evidence_receipt_indexing_service",
    "health-reliability-monitoring": "health_reliability_monitoring",
    "ollama-ai-agent": "ollama_ai_agent",
    # Client services
    "integration-adapters": "integration_adapters",
    # Product services
    "detection-engine-core": "detection_engine_core",
    "signal-ingestion-normalization": "signal_ingestion_normalization",
    "user-behaviour-intelligence": "user_behaviour_intelligence",
    "mmm_engine": "mmm_engine",
}


def _dedupe_and_prepend(path: str) -> None:
    """Ensure `path` is at the front of sys.path."""
    if path in sys.path:
        sys.path.remove(path)
    sys.path.insert(0, path)


def _ensure_alias(pkg_name: str, module_path: Path) -> None:
    """Register a simple package alias with a __path__ pointing at module_path."""
    if pkg_name in sys.modules:
        return
    pkg = types.ModuleType(pkg_name)
    pkg.__path__ = [str(module_path)]
    sys.modules[pkg_name] = pkg


def _iter_service_paths(root: Path) -> Iterable[tuple[str, Path]]:
    """Yield (import_name, path) tuples for known service directories."""
    base = root / "src" / "cloud_services"
    for category in ("shared-services", "client-services", "product-services"):
        cat_dir = base / category
        if not cat_dir.exists():
            continue
        for item in cat_dir.iterdir():
            if not item.is_dir():
                continue
            import_name = MODULE_MAPPINGS.get(item.name, item.name.replace("-", "_"))
            yield import_name, item


def pin_repo_config(root: Path) -> None:
    """
    Ensure the repository-level `config` package is the one that gets imported.

    This prevents service-local `config.py` files from shadowing the real package.
    """
    _dedupe_and_prepend(str(root))
    try:
        config_pkg = importlib.import_module("config")
    except Exception:
        return
    sys.modules["config"] = config_pkg


def setup_path_normalization(project_root: str | Path | None = None) -> None:
    """
    Normalize import paths for tests.

    - Keeps the repository root at the front of sys.path.
    - Registers alias packages for hyphenated service directories.
    - Pins the repo `config` package to avoid name collisions.
    """
    root = Path(project_root) if project_root else Path(__file__).resolve().parents[2]
    root = root.resolve()

    _dedupe_and_prepend(str(root))
    pin_repo_config(root)

    for import_name, module_path in _iter_service_paths(root):
        _ensure_alias(import_name, module_path)


__all__ = ["setup_path_normalization", "pin_repo_config", "MODULE_MAPPINGS"]
