"""
Tenant fixtures used across all ZeroUI module test suites.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List, Tuple
from uuid import uuid4


class TenantIsolationAssertionError(AssertionError):
    """Raised when an operation violates declared tenant isolation constraints."""


@dataclass(frozen=True)
class TenantProfile:
    tenant_id: str
    name: str
    tier: str
    region: str
    policies: Dict[str, str] = field(default_factory=dict)
    consent_flags: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_headers(self) -> Dict[str, str]:
        """Return canonical headers used by API clients."""
        return {
            "x-tenant-id": self.tenant_id,
            "x-tenant-tier": self.tier,
            "x-tenant-region": self.region,
        }


class TenantFactory:
    """Factory that generates deterministic tenant fixtures for tests."""

    def __init__(self, seed_prefix: str = "tenant") -> None:
        self._seed_prefix = seed_prefix
        self._counter = 0

    def create(self, *, tier: str = "enterprise", region: str = "us-east") -> TenantProfile:
        self._counter += 1
        suffix = f"{self._counter:04d}"
        tenant_id = f"{self._seed_prefix}-{suffix}"
        metadata = {
            "created_at": datetime.utcnow().isoformat(),
            "compliance_zone": "gdpr" if region.startswith("eu") else "global",
        }
        return TenantProfile(
            tenant_id=tenant_id,
            name=f"Tenant {suffix}",
            tier=tier,
            region=region,
            policies={
                "privacy_policy_version": "1.3",
                "consent_model": "opt_in",
            },
            consent_flags={
                "marketing": False,
                "product_updates": True,
            },
            metadata=metadata,
        )

    def create_pair(self) -> Tuple[TenantProfile, TenantProfile]:
        """Convenience helper returning two distinct tenants (A/B)."""
        return self.create(tier="enterprise"), self.create(tier="growth")

    def create_attacker_profile(self) -> TenantProfile:
        """Return a synthetic tenant used in cross-tenant attack tests."""
        attacker = self.create(tier="red-team")
        attacker.metadata = {**attacker.metadata, "threat_model": "attacker"}
        return attacker

    @staticmethod
    def assert_isolated(actor: TenantProfile, target: TenantProfile) -> None:
        if actor.tenant_id == target.tenant_id:
            return
        raise TenantIsolationAssertionError(
            f"Actor {actor.tenant_id} attempted to access tenant {target.tenant_id}"
        )

    @staticmethod
    def build_matrix(tenants: Iterable[TenantProfile]) -> List[Tuple[str, str]]:
        """Return all cross-tenant combinations, useful when parameterizing tests."""
        mapping = list(tenants)
        pairs: List[Tuple[str, str]] = []
        for i, actor in enumerate(mapping):
            for target in mapping[i + 1 :]:
                pairs.append((actor.tenant_id, target.tenant_id))
        return pairs


@dataclass(frozen=True)
class AttackerProfile:
    """Synthetic profile for security tests simulating malicious actors."""

    tenant_id: str
    user_id: str
    attack_vector: str  # e.g., "cross_tenant_export", "scope_escalation"

    def to_headers(self) -> Dict[str, str]:
        return {
            "x-tenant-id": self.tenant_id,
            "x-user-id": self.user_id,
        }


def random_identifier(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"

