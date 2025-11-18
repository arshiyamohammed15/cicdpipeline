"""
Constitution Rules Database Module for ZeroUI 2.0

This module provides a SQLite database system to store and manage
constitution rules with configuration management for enabling/disabling rules.

Rule counts are dynamically calculated from docs/constitution/*.json files (single source of truth).
No hardcoded rule counts exist in this module.

All rules are enabled by default and can be toggled on/off through the
configuration system.
"""

__version__ = "1.0.0"
__author__ = "ZeroUI 2.0 Constitution System"

from .database import ConstitutionRulesDB
from .rule_extractor import ConstitutionRuleExtractor
from .config_manager import ConstitutionRuleManager
from .queries import ConstitutionQueries
from .base_manager import BaseConstitutionManager
from .constitution_rules_json import ConstitutionRulesJSON
from .config_manager_json import ConstitutionRuleManagerJSON
from .backend_factory import (
    get_constitution_manager, get_backend_factory, switch_backend, get_backend_status,
    get_active_backend_config, migrate_configuration, validate_configuration, get_migration_info
)
from .sync_manager import get_sync_manager, sync_backends, verify_sync
from .migration import get_migration_manager, migrate_sqlite_to_json, migrate_json_to_sqlite, repair_sync
from .logging_config import get_constitution_logger, setup_logging
from .rule_count_loader import RuleCountLoader, get_rule_count_loader, get_rule_counts

__all__ = [
    "ConstitutionRulesDB",
    "ConstitutionRuleExtractor",
    "ConstitutionRuleManager",
    "ConstitutionQueries",
    "BaseConstitutionManager",
    "ConstitutionRulesJSON",
    "ConstitutionRuleManagerJSON",
    "get_constitution_manager",
    "get_backend_factory",
    "switch_backend",
    "get_backend_status",
    "get_active_backend_config",
    "migrate_configuration",
    "validate_configuration",
    "get_migration_info",
    "get_sync_manager",
    "sync_backends",
    "verify_sync",
    "get_migration_manager",
    "migrate_sqlite_to_json",
    "migrate_json_to_sqlite",
    "repair_sync",
    "get_constitution_logger",
    "setup_logging",
    "RuleCountLoader",
    "get_rule_count_loader",
    "get_rule_counts"
]
