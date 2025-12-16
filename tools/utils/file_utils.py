"""
File utility functions for tools.

This module provides common file operations to eliminate duplication
across tools scripts.
"""

import json
import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def setup_windows_console_encoding() -> None:
    """
    Setup UTF-8 encoding for Windows console.

    This function fixes Windows console encoding issues and should be called
    at the start of scripts that output Unicode characters.
    """
    if sys.platform == "win32":
        try:
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
            os.environ['PYTHONIOENCODING'] = 'utf-8'
        except Exception:
            # Fallback if codecs is not available
            pass


def load_rules_from_json_files(constitution_dir: str = "docs/constitution") -> List[Dict[str, Any]]:
    """
    Load all rules from JSON source files (single source of truth).

    This function provides a unified way to load constitution rules from
    JSON files, eliminating duplication across multiple tools.

    Args:
        constitution_dir: Path to directory containing constitution JSON files

    Returns:
        List of rule dictionaries

    Raises:
        FileNotFoundError: If constitution directory or JSON files not found

    Example:
        rules = load_rules_from_json_files("docs/constitution")
        print(f"Loaded {len(rules)} rules")
    """
    constitution_path = Path(constitution_dir)
    if not constitution_path.exists():
        raise FileNotFoundError(f"Constitution directory not found: {constitution_path}")

    json_files = sorted(list(constitution_path.glob("*.json")))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {constitution_path}")

    all_rules = []

    for json_file in json_files:
        logger.debug(f"Loading rules from {json_file.name}...")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                rules = data.get('constitution_rules', [])
                all_rules.extend(rules)
        except Exception as e:
            logger.error(f"Error loading {json_file.name}: {e}", exc_info=True)
            continue

    logger.info(f"Loaded {len(all_rules)} rules from {len(json_files)} files")
    return all_rules

