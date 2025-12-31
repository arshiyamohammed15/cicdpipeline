#!/usr/bin/env python3
"""
Legacy validator smoke tests (now enabled).
"""

from __future__ import annotations

import sys
from pathlib import Path
import json

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_imports():
    """Verify critical validator/tool modules import cleanly."""
    imports_to_test = [
        ("validator.pre_implementation_hooks", "PreImplementationHookManager"),
        ("validator.integrations.integration_registry", "IntegrationRegistry"),
        ("validator.integrations.api_service", "app"),
        ("validator.integrations.openai_integration", "OpenAIIntegration"),
        ("validator.integrations.cursor_integration", "CursorIntegration"),
        ("tools.enhanced_cli", "EnhancedCLI"),
        ("tools.start_validation_service", None),
    ]

    errors = []
    for module_name, class_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name] if class_name else [])
            if class_name:
                getattr(module, class_name)
            print(f"  OK {module_name}")
        except Exception as exc:  # pragma: no cover - diagnostic output retained
            print(f"  ERROR {module_name}: {exc}")
            errors.append((module_name, str(exc)))

    assert errors == []


def test_basic_functionality():
    """Exercise PreImplementationHookManager end-to-end."""
    from validator.pre_implementation_hooks import PreImplementationHookManager

    hook_manager = PreImplementationHookManager()
    result = hook_manager.validate_before_generation("test prompt", "python", "general")
    print(f"  OK Basic validation: {len(result['violations'])} violations")
    assert "valid" in result and "violations" in result


def test_json_files():
    """Ensure key JSON config files are well-formed."""
    json_files = [
        PROJECT_ROOT / "config" / "hook_config.json",
        PROJECT_ROOT / "config" / "constitution_rules.json",
        PROJECT_ROOT / "config" / "constitution_config.json",
    ]

    for path in json_files:
        with path.open("r", encoding="utf-8") as handle:
            json.load(handle)
        print(f"  OK {path}")


def test_vs_code_files():
    """Ensure VS Code extension metadata and code are present."""
    pkg = PROJECT_ROOT / "src" / "vscode-extension" / "package.json"
    ext = PROJECT_ROOT / "src" / "vscode-extension" / "extension.ts"

    with pkg.open("r", encoding="utf-8") as handle:
        json.load(handle)
    with ext.open("r", encoding="utf-8") as handle:
        content = handle.read()
        assert "ConstitutionValidator" in content

    print(f"  OK {pkg}")
    print(f"  OK {ext}")
