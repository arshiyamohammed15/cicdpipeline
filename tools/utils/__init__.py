"""
Shared utilities for tools directory.

This module provides common utilities to eliminate code duplication
across tools scripts.
"""

from .db_utils import get_db_connection, execute_db_operation, get_all_rule_numbers
from .file_utils import load_rules_from_json_files, setup_windows_console_encoding

__all__ = [
    'get_db_connection',
    'execute_db_operation',
    'get_all_rule_numbers',
    'load_rules_from_json_files',
    'setup_windows_console_encoding',
]

