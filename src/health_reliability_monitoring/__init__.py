"""
Alias package for the Health & Reliability Monitoring service.

Allows importing the hyphenated directory `cloud-services/shared-services/health-reliability-monitoring`
using standard Python module syntax (`import health_reliability_monitoring`).
"""

from pathlib import Path

_alias_path = (
    Path(__file__).resolve().parent.parent
    / "cloud-services"
    / "shared-services"
    / "health-reliability-monitoring"
)

__path__ = [str(_alias_path)]

