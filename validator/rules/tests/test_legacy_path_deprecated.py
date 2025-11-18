"""
Legacy constitution test path shim.

Running ``pytest validator/rules/tests`` used to execute constitution suites
directly under ``validator/rules``. The canonical suites now live under the
top-level ``tests`` package, so this shim instructs callers to use the updated
command instead of failing with a missing-directory error.
"""

import pytest


def test_legacy_constitution_command_deprecated():
    pytest.skip(
        "Legacy path deprecated. Run `python -m pytest tests -k \"constitution\" -q` instead."
    )
