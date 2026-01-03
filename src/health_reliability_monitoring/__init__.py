"""
Alias package for the Health & Reliability Monitoring service.

Allows importing the hyphenated directory `cloud-services/shared-services/health-reliability-monitoring`
using standard Python module syntax (`import health_reliability_monitoring`).
"""

from pathlib import Path

_root = Path(__file__).resolve().parent.parent

# Prefer the on-disk service package; fall back to the legacy hyphenated path if present.
_alias_path = _root / "cloud_services" / "shared-services" / "health-reliability-monitoring"
if not _alias_path.is_dir():
    fallback = _root / "cloud-services" / "shared-services" / "health-reliability-monitoring"
    _alias_path = fallback if fallback.is_dir() else _alias_path

__path__ = [str(_alias_path)]

