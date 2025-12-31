"""
Shared test harness for ZeroUI modules.

Provides reusable fixtures and utilities for:
- Multi-tenant isolation testing
- IAM token generation
- Performance benchmarking
- Evidence pack generation
- Chaos engineering toggles

All modules (DG&P, Alerting, Budgeting, Deployment) can import from here.
"""

from .tenants import TenantFactory, AttackerProfile
from .tokens import IAMTokenFactory
from .perf_runner import PerfRunner, PerfScenario
from .evidence import EvidencePackBuilder
from .alerting_fixtures import AlertFixtureFactory, AlertEvent
from .budgeting_fixtures import BudgetFixtureFactory, BudgetFixture, RateLimitFixture
from .deployment_fixtures import DeploymentFixtureFactory, EnvironmentConfig, DeploymentManifest
from .receipt_assertions import assert_enforcement_receipt_fields

__all__ = [
    "TenantFactory",
    "AttackerProfile",
    "IAMTokenFactory",
    "PerfRunner",
    "PerfScenario",
    "EvidencePackBuilder",
    "AlertFixtureFactory",
    "AlertEvent",
    "BudgetFixtureFactory",
    "BudgetFixture",
    "RateLimitFixture",
    "DeploymentFixtureFactory",
    "EnvironmentConfig",
    "DeploymentManifest",
    "assert_enforcement_receipt_fields",
]
