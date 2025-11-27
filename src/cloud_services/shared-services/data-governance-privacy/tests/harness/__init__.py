"""
Shared harness utilities for DG&P and downstream modules.

Exports lightweight factories so suites can import from a single namespace:

    from data_governance_privacy.tests.harness import TenantFactory
"""

from .tenants import (
    TenantFactory,
    TenantProfile,
    TenantIsolationAssertionError,
)
from .tokens import IAMTokenFactory, IssuedToken
from .fixtures import (
    ClassificationPayloadFactory,
    ConsentStateFactory,
    RetentionPolicyFactory,
)
from .perf_runner import PerfRunner, PerfScenario, PerfResult

__all__ = [
    "TenantFactory",
    "TenantProfile",
    "TenantIsolationAssertionError",
    "IAMTokenFactory",
    "IssuedToken",
    "ClassificationPayloadFactory",
    "ConsentStateFactory",
    "RetentionPolicyFactory",
    "PerfRunner",
    "PerfScenario",
    "PerfResult",
]

