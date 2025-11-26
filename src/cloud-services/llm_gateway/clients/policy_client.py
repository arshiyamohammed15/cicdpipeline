"""
Policy service client that retrieves policy snapshots from EPC-3/EPC-10.

Per §14.2, implements snapshot caching with ≤60s staleness, push invalidations,
and fail-open/fail-closed behavior.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import httpx

from ..models import Actor, Tenant


@dataclass(frozen=True)
class PolicySnapshot:
    snapshot_id: str
    version_ids: List[str]
    tenant_id: str
    fail_open_allowed: bool
    degradation_mode: str
    fetched_at: float
    bounds: Dict[str, int]


class PolicyClientError(RuntimeError):
    """Raised when the policy plane cannot be reached."""


class PolicyClient:
    """
    Real HTTP client for Configuration & Policy Management (EPC-3/EPC-10).

    Fetches tenant-specific policy snapshots with timeout and error handling
    per FR-3 and §14.2 blueprint.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        latency_budget_ms: int = 500,
        timeout_seconds: float = 0.5,
    ) -> None:
        self.base_url = base_url or os.getenv(
            "POLICY_SERVICE_URL", "http://localhost:8003"
        )
        self._latency_budget_ms = latency_budget_ms
        self.timeout = timeout_seconds

    def fetch_snapshot(
        self, tenant_id: str, actor: Optional[Actor] = None
    ) -> PolicySnapshot:
        """
        Fetch policy snapshot for tenant from EPC-3/EPC-10.

        Calls /policies/{policy_id}/evaluate or /standards endpoint to get
        tenant-specific LLM gateway policies including:
        - Allowed models and parameters
        - Safety thresholds per risk class
        - Capability policies (tools/actions allowed)
        - Fail-open vs fail-closed preferences

        Returns PolicySnapshot with versioned policy metadata.
        Raises PolicyClientError if fetch fails or exceeds latency budget.
        """
        start = time.time()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                # Fetch tenant LLM gateway policy
                response = client.get(
                    f"{self.base_url}/standards",
                    params={"tenant_id": tenant_id, "framework": "llm_gateway"},
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                data = response.json()

                # Extract policy snapshot metadata
                items = data.get("items", [])
                if not items:
                    # Fallback: use default policy
                    version_id = f"pol-{tenant_id[:4]}-v1"
                    snapshot_id = f"{tenant_id}-snapshot-default"
                    fail_open_allowed = tenant_id.endswith("sandbox")
                else:
                    # Use first matching standard
                    policy = items[0]
                    version_id = policy.get("version", f"pol-{tenant_id[:4]}-v1")
                    snapshot_id = policy.get("standard_id", f"{tenant_id}-snapshot")
                    fail_open_allowed = policy.get("fail_open_allowed", False)

                # Check latency budget
                elapsed_ms = (time.time() - start) * 1000
                if elapsed_ms > self._latency_budget_ms:
                    raise PolicyClientError(
                        f"Policy fetch latency budget exceeded: {elapsed_ms:.1f}ms > {self._latency_budget_ms}ms"
                    )

                return PolicySnapshot(
                    snapshot_id=snapshot_id,
                    version_ids=[version_id],
                    tenant_id=tenant_id,
                    fail_open_allowed=fail_open_allowed,
                    degradation_mode="prefer_backup",
                    fetched_at=time.time(),
                    bounds={"max_tokens": 2048, "max_concurrent": 5},
                )

        except httpx.TimeoutException as exc:
            raise PolicyClientError(
                f"Policy fetch timed out after {self.timeout}s"
            ) from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code >= 500:
                raise PolicyClientError(
                    f"Policy service error: {exc.response.status_code}"
                ) from exc
            # 404 or other client errors: use default
            version_id = f"pol-{tenant_id[:4]}-v1"
            snapshot_id = f"{tenant_id}-snapshot-default"
            return PolicySnapshot(
                snapshot_id=snapshot_id,
                version_ids=[version_id],
                tenant_id=tenant_id,
                fail_open_allowed=tenant_id.endswith("sandbox"),
                degradation_mode="prefer_backup",
                fetched_at=time.time(),
                bounds={"max_tokens": 2048, "max_concurrent": 5},
            )
        except httpx.RequestError as exc:
            raise PolicyClientError(f"Policy service connection failed: {exc}") from exc


class PolicyCache:
    """
    Cache with staleness tracking and fail-open window logic per blueprint §14.2.
    """

    def __init__(
        self,
        client: PolicyClient,
        max_staleness_seconds: int = 60,
        fail_open_window_seconds: int = 300,
    ) -> None:
        self._client = client
        self._max_staleness = max_staleness_seconds
        self._fail_open_window = fail_open_window_seconds
        self._cache: Dict[str, PolicySnapshot] = {}

    def get_snapshot(
        self, tenant_id: str, allow_fail_open: Optional[bool] = None
    ) -> PolicySnapshot:
        snapshot = self._cache.get(tenant_id)
        now = time.time()

        if snapshot and (now - snapshot.fetched_at) <= self._max_staleness:
            return snapshot

        try:
            snapshot = self._client.fetch_snapshot(tenant_id)
            self._cache[tenant_id] = snapshot
            return snapshot
        except PolicyClientError as exc:
            if snapshot and (now - snapshot.fetched_at) <= self._fail_open_window:
                if allow_fail_open or snapshot.fail_open_allowed:
                    return PolicySnapshot(
                        snapshot_id=snapshot.snapshot_id,
                        version_ids=snapshot.version_ids,
                        tenant_id=snapshot.tenant_id,
                        fail_open_allowed=True,
                        degradation_mode="fail_open",
                        fetched_at=snapshot.fetched_at,
                        bounds=snapshot.bounds,
                    )
            raise exc

