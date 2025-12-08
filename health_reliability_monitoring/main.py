"""
Root-level shim to expose create_app/app for tests.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
import prometheus_client
from prometheus_client import REGISTRY


def _load_real():
    root = Path(__file__).resolve().parent.parent / "src" / "cloud_services" / "shared-services" / "health-reliability-monitoring"
    real_main = root / "main.py"
    if not real_main.exists():
        raise FileNotFoundError(f"Real main module not found at {real_main}")
    pkg_name = "health_reliability_monitoring"
    pkg = types.ModuleType(pkg_name)
    pkg.__path__ = [str(root)]
    sys.modules[pkg_name] = pkg

    spec = importlib.util.spec_from_file_location("health_reliability_monitoring.main_real", real_main, submodule_search_locations=[str(root)])
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {real_main}")

    # Avoid duplicate metric registration when re-importing in tests.
    # Reset the default registry to avoid duplicate metric registration across repeated imports.
    try:
        REGISTRY._names_to_collectors = {}
        REGISTRY._collector_to_names = {}
    except Exception:
        pass

    class _NoopMetric:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            return None

        def observe(self, *args, **kwargs):
            return None

        def set(self, *args, **kwargs):
            return None

    prometheus_client.Counter = _NoopMetric  # type: ignore
    prometheus_client.Gauge = _NoopMetric  # type: ignore
    prometheus_client.Histogram = _NoopMetric  # type: ignore

    module = importlib.util.module_from_spec(spec)
    sys.modules["health_reliability_monitoring.main_real"] = module
    spec.loader.exec_module(module)
    return module


_real = _load_real()
app = getattr(_real, "app", None)
create_app = getattr(_real, "create_app", None) or (lambda: app)

__all__ = ["create_app", "app"]

