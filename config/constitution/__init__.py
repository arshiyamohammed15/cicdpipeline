"""
Constitution package (lazy imports to avoid circular dependencies).

Rule counts and metadata come from docs/constitution (or docs/architecture/constitution).
Heavy modules are loaded on demand via __getattr__ to prevent import cycles.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__version__ = "1.0.0"
__author__ = "ZeroUI 2.0 Constitution System"

_EXPORTS = {
    "ConstitutionRulesDB": "database",
    "ConstitutionRuleExtractor": "rule_extractor",
    "ConstitutionRuleManager": "config_manager",
    "ConstitutionQueries": "queries",
    "BaseConstitutionManager": "base_manager",
    "ConstitutionRulesJSON": "constitution_rules_json",
    "ConstitutionRuleManagerJSON": "config_manager_json",
    "get_constitution_manager": "backend_factory",
    "get_backend_factory": "backend_factory",
    "switch_backend": "backend_factory",
    "get_backend_status": "backend_factory",
    "get_active_backend_config": "backend_factory",
    "migrate_configuration": "backend_factory",
    "validate_configuration": "backend_factory",
    "get_migration_info": "backend_factory",
    "get_sync_manager": "sync_manager",
    "sync_backends": "sync_manager",
    "verify_sync": "sync_manager",
    "get_migration_manager": "migration",
    "migrate_sqlite_to_json": "migration",
    "migrate_json_to_sqlite": "migration",
    "repair_sync": "migration",
    "get_constitution_logger": "logging_config",
    "setup_logging": "logging_config",
    "RuleCountLoader": "rule_count_loader",
    "get_rule_count_loader": "rule_count_loader",
    "get_rule_counts": "rule_count_loader",
}

__all__ = sorted(_EXPORTS.keys())


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__} has no attribute {name}")
    module = import_module(f"{__name__}.{_EXPORTS[name]}")
    return getattr(module, name)
