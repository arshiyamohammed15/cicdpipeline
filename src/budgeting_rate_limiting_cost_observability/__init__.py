"""
Alias package for Budgeting, Rate-Limiting & Cost Observability (M35).

Allows importing the hyphenated directory (`cloud-services/shared-services/...`)
using a Python-friendly package name.
"""

from pathlib import Path

_alias_path = (
    Path(__file__).resolve().parent.parent
    / "cloud-services"
    / "shared-services"
    / "budgeting-rate-limiting-cost-observability"
)

__path__ = [str(_alias_path)]

