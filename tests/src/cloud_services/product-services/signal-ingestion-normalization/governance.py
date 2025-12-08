"""
Test shim that proxies to the real governance module under src/.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_real():
    root = Path(__file__).resolve().parents[5] / "src" / "cloud_services" / "product_services" / "signal-ingestion-normalization"
    real_path = root / "governance.py"
    if not real_path.exists():
        raise FileNotFoundError(f"Real governance module not found at {real_path}")

    spec = importlib.util.spec_from_file_location("signal_ingestion_normalization.governance", real_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {real_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["signal_ingestion_normalization.governance"] = module
    spec.loader.exec_module(module)
    return module


_real = _load_real()

# Re-export everything
globals().update(_real.__dict__)

__all__ = [name for name in _real.__dict__ if not name.startswith("_")]

