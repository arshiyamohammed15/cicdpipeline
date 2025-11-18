"""
ZeroUI 2.0 test package initializer.

Pytest discovers dozens of suites under ``tests/`` and this file simply marks
the directory as an importable package so ``python -m pytest`` can resolve
modules such as ``tests.test_api_endpoints`` without loader errors.
"""

__all__ = []
