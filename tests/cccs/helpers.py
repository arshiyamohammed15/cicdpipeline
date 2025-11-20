"""Shared helpers for CCCS tests aligned with offline runtime behavior."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Dict

SIGNING_SECRET = b"policy-secret"

# All dependencies required by CCCS runtime (edge + pm-7)
DEPENDENCY_HEALTH_READY: Dict[str, bool] = {
    "epc-1": True,
    "epc-3": True,
    "epc-13": True,
    "epc-11": True,
    "pm-7": True,
}


def sign_snapshot(payload: dict) -> str:
    """Generate HMAC signature for offline policy snapshots."""
    blob = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hmac.new(SIGNING_SECRET, blob, hashlib.sha256).hexdigest()


def dependency_health(**overrides: bool) -> Dict[str, bool]:
    """Return dependency health map with optional overrides (e.g., to simulate failures)."""
    health = DEPENDENCY_HEALTH_READY.copy()
    health.update(overrides)
    return health

