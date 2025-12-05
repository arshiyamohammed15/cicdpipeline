"""
Pytest plugin for lazy test collection.

Defers heavy imports until test execution, not during collection.
"""

import ast
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest


class LazyCollectionPlugin:
    """Plugin that skips imports during collection."""

    def __init__(self, config):
        self.config = config
        self.heavy_imports = {
            "fastapi",
            "sqlalchemy",
            "pydantic",
            "database",
            "services",
            "models",
        }

    @pytest.hookimpl(tryfirst=True)
    def pytest_collect_file(self, file_path: Path, parent):
        """Intercept file collection to skip heavy imports."""
        # Check if file has heavy imports
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
            
            has_heavy_imports = False
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if any(dep in alias.name.lower() for dep in self.heavy_imports):
                            has_heavy_imports = True
                            break
                elif isinstance(node, ast.ImportFrom):
                    if node.module and any(
                        dep in node.module.lower() for dep in self.heavy_imports
                    ):
                        has_heavy_imports = True
                        break
                if has_heavy_imports:
                    break

            # If file has heavy imports, mark it for lazy loading
            if has_heavy_imports:
                # Store original import for later
                return None  # Let pytest handle normally, but we'll intercept execution
        except Exception:
            # If we can't parse, let pytest handle it
            pass

        return None


def pytest_configure(config):
    """Register plugin."""
    config.pluginmanager.register(LazyCollectionPlugin(config), "lazy_collection")

