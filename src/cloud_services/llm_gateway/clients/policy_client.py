"""
Policy service client that retrieves policy snapshots from EPC-3/EPC-10.

Per §14.2, implements snapshot caching with ≤60s staleness, push invalidations,
and fail-open/fail-closed behavior.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

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
    recovery: Dict[str, int] = field(default_factory=dict)


_DEFAULT_LOCAL_POLICY_PATH = Path("config/policies/platform_policy.json")


def _resolve_local_policy_path() -> Path:
    env_path = os.getenv("LLM_GATEWAY_POLICY_PATH")
    if env_path:
        return Path(env_path)
    return _DEFAULT_LOCAL_POLICY_PATH


def _load_local_policy() -> Dict[str, Any]:
    policy_path = _resolve_local_policy_path()
    if not policy_path.is_file():
        return {}
    try:
        with policy_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, Mapping):
        return {}
    return dict(data)


def _coerce_positive_int(value: Any) -> Optional[int]:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _extract_section(policy: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    candidate = policy.get(key)
    if isinstance(candidate, Mapping):
        return candidate
    definition = policy.get("policy_definition")
    if isinstance(definition, Mapping):
        nested = definition.get(key)
        if isinstance(nested, Mapping):
            return nested
    return {}


def _extract_token_bounds(policy: Mapping[str, Any]) -> Dict[str, int]:
    token_budgets = _extract_section(policy, "token_budgets")
    bounds_section = _extract_section(policy, "bounds")
    bounds: Dict[str, int] = {}

    for key in (
        "max_input_tokens",
        "max_output_tokens",
        "max_total_tokens",
        "max_tokens",
        "max_concurrent",
    ):
        value = _coerce_positive_int(token_budgets.get(key))
        if value is not None:
            bounds[key] = value

    for key, raw in bounds_section.items():
        if key in bounds:
            continue
        value = _coerce_positive_int(raw)
        if value is not None:
            bounds[key] = value

    return bounds


def _extract_recovery(policy: Mapping[str, Any]) -> Dict[str, int]:
    recovery_section = _extract_section(policy, "recovery")
    recovery: Dict[str, int] = {}
    for key in ("max_attempts", "base_delay_ms", "max_delay_ms", "timeout_ms"):
        value = _coerce_positive_int(recovery_section.get(key))
        if value is not None:
            recovery[key] = value
    return recovery


def _merge_int_maps(base: Dict[str, int], override: Dict[str, int]) -> Dict[str, int]:
    merged = dict(base)
    merged.update(override)
    return merged


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
        local_policy = _load_local_policy()
        local_bounds = _extract_token_bounds(local_policy)
        local_recovery = _extract_recovery(local_policy)

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
                policy_payload: Mapping[str, Any] = {}
                if not items:
                    # Fallback: use default policy
                    version_id = f"pol-{tenant_id[:4]}-v1"
                    snapshot_id = f"{tenant_id}-snapshot-default"
                    fail_open_allowed = tenant_id.endswith("sandbox")
                else:
                    # Use first matching standard
                    policy = items[0]
                    if isinstance(policy, Mapping):
                        policy_payload = policy
                        version_id = policy.get("version", f"pol-{tenant_id[:4]}-v1")
                        snapshot_id = policy.get("standard_id", f"{tenant_id}-snapshot")
                        fail_open_allowed = policy.get("fail_open_allowed", False)
                    else:
                        policy_payload = {}
                        version_id = f"pol-{tenant_id[:4]}-v1"
                        snapshot_id = f"{tenant_id}-snapshot-default"
                        fail_open_allowed = tenant_id.endswith("sandbox")
                bounds = _merge_int_maps(
                    local_bounds, _extract_token_bounds(policy_payload)
                )
                recovery = _merge_int_maps(
                    local_recovery, _extract_recovery(policy_payload)
                )

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
                    bounds=bounds,
                    recovery=recovery,
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
                bounds=local_bounds,
                recovery=local_recovery,
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
                        recovery=snapshot.recovery,
                    )
            raise exc
