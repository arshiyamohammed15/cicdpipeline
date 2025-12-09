"""
Test registry utilities.

Exports common helpers so callers can import a stable entry point.
"""

from .path_normalizer import setup_path_normalization  # noqa: F401

__all__ = ["setup_path_normalization"]
