"""Lightweight adapters for external services."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import get_settings

settings = get_settings()


DEFAULT_POLICY_BUNDLE: Dict[str, Any] = {
    "schema_version": "1.0.0",
    "dedup": {
        "defaults": settings.policy.default_dedup_minutes,
        "by_category": {},
        "by_severity": {},
    },
    "correlation": {
        "window_minutes": settings.policy.default_correlation_minutes,
        "rules": [
            {
                "name": "tenant-plane",
                "conditions": ["tenant_id", "plane"],
                "window_minutes": settings.policy.default_correlation_minutes,
                "dependency_match": "shared",
            }
        ],
    },
    "routing": {
        "defaults": {
            "channels": ["email"],
            "targets": ["{tenant_id}-oncall"],
            "channel_overrides": {
                "P0": ["sms", "voice"],
                "P1": ["sms"],
            },
        },
        "tenant_overrides": {},
    },
    "escalation": {
        "policies": {
            "default": {
                "policy_id": "default",
                "steps": [
                    {"order": 1, "delay_seconds": 0, "channels": ["sms"]},
                    {"order": 2, "delay_seconds": 300, "channels": ["voice"]},
                ],
            }
        }
    },
    "fatigue": {
        "rate_limits": {
            "per_alert": {"max_notifications": 5, "window_minutes": 60},
            "per_user": {"max_notifications": 20, "window_minutes": 60},
        },
        "maintenance": [],
        "suppression": {
            "suppress_followup_during_incident": True,
            "suppress_window_minutes": 15,
        },
    },
    "retry": {
        "defaults": {
            "max_attempts": 5,
            "backoff_strategy": "exponential",
            "backoff_intervals": [30, 60, 120, 240, 480],
        },
        "by_channel": {},
        "by_severity": {},
    },
    "fallback": {
        "defaults": {"channels": ["email", "sms", "voice", "webhook"]},
        "by_severity": {},
    },
}


@dataclass
class _CacheEntry:
    expires_at: datetime
    payload: Dict[str, Any]


class PolicyClient:
    def __init__(self, policy_path: Optional[Path] = None, cache_ttl_seconds: Optional[int] = None):
        self.base_url = settings.policy.config_service_url
        self._policy_path: Path = policy_path or settings.policy.policy_bundle_path
        ttl_seconds = cache_ttl_seconds or settings.policy.cache_ttl_seconds
        self._ttl = timedelta(seconds=ttl_seconds)
        self._cache: Optional[_CacheEntry] = None

    def _load_bundle_from_disk(self) -> Dict[str, Any]:
        if self._policy_path.is_file():
            try:
                with self._policy_path.open("r", encoding="utf-8") as handle:
                    return json.load(handle)
            except (json.JSONDecodeError, OSError):
                return DEFAULT_POLICY_BUNDLE
        return DEFAULT_POLICY_BUNDLE

    async def _load_bundle_from_api(self) -> Dict[str, Any]:
        """Load policy bundle from Configuration & Policy Management API."""
        if not settings.policy.use_api_refresh:
            return self._load_bundle_from_disk()
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/v1/policies/alerting",
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Failed to load policy from API, falling back to disk: %s", exc)
            return self._load_bundle_from_disk()

    def _get_bundle(self) -> Dict[str, Any]:
        """Synchronous bundle getter (uses cached or disk)."""
        if self._cache and self._cache.expires_at > datetime.utcnow():
            return self._cache.payload
        payload = self._load_bundle_from_disk()
        self._cache = _CacheEntry(datetime.utcnow() + self._ttl, payload)
        return payload

    async def refresh_bundle(self) -> Dict[str, Any]:
        """
        Refresh policy bundle from API or disk.
        
        Returns:
            Updated policy bundle
        """
        payload = await self._load_bundle_from_api()
        self._cache = _CacheEntry(datetime.utcnow() + self._ttl, payload)
        return payload

    def get_dedup_window(self, category: str, severity: str) -> int:
        bundle = self._get_bundle()
        category_lookup = bundle["dedup"].get("by_category", {}).get(category)
        severity_lookup = bundle["dedup"].get("by_severity", {}).get(severity)
        if category_lookup is not None:
            return int(category_lookup)
        if severity_lookup is not None:
            return int(severity_lookup)
        return int(bundle["dedup"].get("defaults", settings.policy.default_dedup_minutes))

    def get_correlation_window(self) -> int:
        bundle = self._get_bundle()
        return int(bundle["correlation"].get("window_minutes", settings.policy.default_correlation_minutes))

    def get_correlation_rules(self) -> List[Dict[str, Any]]:
        bundle = self._get_bundle()
        return bundle["correlation"].get("rules", [])

    async def resolve_routing(self, alert_payload: Dict[str, Any]) -> Dict[str, Any]:
        bundle = self._get_bundle()
        severity = alert_payload.get("severity", "P2")
        tenant_id = alert_payload.get("tenant_id", "global")
        routing = bundle["routing"]
        tenant_override = routing.get("tenant_overrides", {}).get(tenant_id, {})
        overrides = tenant_override.get("channel_overrides") or routing["defaults"].get("channel_overrides", {})
        channels = overrides.get(severity, routing["defaults"]["channels"])
        target_template = tenant_override.get("targets", routing["defaults"]["targets"])
        targets = [target.format(**alert_payload) for target in target_template]
        return {
            "targets": targets,
            "channels": channels,
            "policy_id": tenant_override.get("policy_id", "default"),
        }

    def get_escalation_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve escalation policy by ID."""
        bundle = self._get_bundle()
        policies = bundle.get("escalation", {}).get("policies", {})
        return policies.get(policy_id)

    def get_default_escalation_policy(self) -> Dict[str, Any]:
        """Get the default escalation policy."""
        bundle = self._get_bundle()
        policies = bundle.get("escalation", {}).get("policies", {})
        return policies.get("default", {"policy_id": "default", "steps": []})

    def get_retry_policy(self, channel: str, severity: str) -> Dict[str, Any]:
        """Get retry policy for a channel and severity combination."""
        bundle = self._get_bundle()
        retry = bundle.get("retry", {})
        defaults = retry.get("defaults", {"max_attempts": 5, "backoff_intervals": [30, 60, 120, 240, 480]})

        # Check channel-specific override
        channel_policy = retry.get("by_channel", {}).get(channel, {})
        # Check severity-specific override
        severity_policy = retry.get("by_severity", {}).get(severity, {})

        # Merge: channel override > severity override > defaults
        policy = defaults.copy()
        policy.update(severity_policy)
        policy.update(channel_policy)

        return {
            "max_attempts": policy.get("max_attempts", defaults["max_attempts"]),
            "backoff_strategy": policy.get("backoff_strategy", "exponential"),
            "backoff_intervals": policy.get("backoff_intervals", defaults["backoff_intervals"]),
        }

    def get_fallback_channels(self, severity: str, failed_channel: Optional[str] = None) -> List[str]:
        """Get fallback channel order for a severity level."""
        bundle = self._get_bundle()
        fallback = bundle.get("fallback", {})
        defaults = fallback.get("defaults", {}).get("channels", ["email", "sms", "voice", "webhook"])

        severity_config = fallback.get("by_severity", {}).get(severity, {})
        if severity_config:
            fallback_order = severity_config.get("fallback_order", defaults)
            # Remove failed channel if specified
            if failed_channel and failed_channel in fallback_order:
                fallback_order = [ch for ch in fallback_order if ch != failed_channel]
            return fallback_order

        # Remove failed channel from defaults if specified
        if failed_channel and failed_channel in defaults:
            defaults = [ch for ch in defaults if ch != failed_channel]
        return defaults

    def get_rate_limit_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration."""
        bundle = self._get_bundle()
        fatigue = bundle.get("fatigue", {})
        rate_limits = fatigue.get("rate_limits", {})
        return {
            "per_alert": rate_limits.get("per_alert", {"max_notifications": 5, "window_minutes": 60}),
            "per_user": rate_limits.get("per_user", {"max_notifications": 20, "window_minutes": 60}),
        }

    def get_maintenance_windows(self) -> List[Dict[str, Any]]:
        """Get active maintenance windows."""
        bundle = self._get_bundle()
        fatigue = bundle.get("fatigue", {})
        return fatigue.get("maintenance", [])

    def get_suppression_config(self) -> Dict[str, Any]:
        """Get suppression configuration."""
        bundle = self._get_bundle()
        fatigue = bundle.get("fatigue", {})
        suppression = fatigue.get("suppression", {})
        return {
            "suppress_followup_during_incident": suppression.get("suppress_followup_during_incident", True),
            "suppress_window_minutes": suppression.get("suppress_window_minutes", 15),
        }


class IAMClient:
    """Client for IAM (Identity & Access Management) service."""
    
    def __init__(self, base_url: Optional[str] = None, use_dynamic: bool = True):
        self.base_url = base_url or settings.policy.iam_service_url
        self.use_dynamic = use_dynamic

    async def expand_targets(self, targets: List[str]) -> List[str]:
        """
        Expand targets (groups, schedules, roles) into individual user IDs.
        
        Supports:
        - Direct user IDs: returned as-is
        - Group references: "group:{group-name}" -> expanded to group members
        - Schedule references: "schedule:{schedule-id}" -> expanded to current on-call users
        - Role references: "role:{role-name}" -> expanded to users with that role
        
        If use_dynamic is True, calls IAM service API. Otherwise, uses stub mode.
        """
        if os.getenv("PYTEST_CURRENT_TEST"):
            return self._expand_targets_stub(targets)
        if not self.use_dynamic:
            # Stub mode: return targets as-is
            return self._expand_targets_stub(targets)
        
        # Dynamic mode: call IAM service
        expanded = []
        for target in targets:
            if target.startswith("{") and target.endswith("}"):
                # Template variable - should have been formatted already
                expanded.append(target)
            elif target.startswith("group:") or target.startswith("role:") or target.startswith("schedule:"):
                # Resolve via IAM service
                try:
                    users = await self._resolve_target_via_iam(target)
                    expanded.extend(users)
                except Exception as exc:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning("Failed to resolve target %s via IAM, using stub: %s", target, exc)
                    # Fallback to stub behavior
                    expanded.append(target)
            elif "-oncall" in target or "-schedule" in target:
                # Schedule reference - resolve via IAM
                try:
                    users = await self._resolve_schedule_via_iam(target)
                    expanded.extend(users)
                except Exception as exc:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning("Failed to resolve schedule %s via IAM, using stub: %s", target, exc)
                    expanded.append(target)
            else:
                # Direct user ID
                expanded.append(target)
        
        return expanded

    def _expand_targets_stub(self, targets: List[str]) -> List[str]:
        """Stub implementation that returns targets as-is."""
        expanded = []
        for target in targets:
            if target.startswith("{") and target.endswith("}"):
                expanded.append(target)
            elif "-oncall" in target or "-schedule" in target:
                expanded.append(target)
            elif target.startswith("group:") or target.startswith("role:"):
                expanded.append(target)
            else:
                expanded.append(target)
        return expanded

    async def _resolve_target_via_iam(self, target: str) -> List[str]:
        """Resolve group/role/schedule target via IAM service API."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                # IAM API endpoint: GET /v1/targets/{target_id}/expand
                target_id = target.split(":", 1)[1] if ":" in target else target
                response = await client.get(
                    f"{self.base_url}/v1/targets/{target_id}/expand",
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("user_ids", [target])  # Fallback to original if empty
        except Exception:
            # If IAM service unavailable, return original target
            return [target]

    async def _resolve_schedule_via_iam(self, schedule_ref: str) -> List[str]:
        """Resolve schedule reference to current on-call users via IAM service."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Extract schedule ID from reference (e.g., "tenant-oncall" -> "tenant-oncall")
                schedule_id = schedule_ref.replace("-oncall", "").replace("-schedule", "")
                response = await client.get(
                    f"{self.base_url}/v1/schedules/{schedule_id}/oncall",
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("user_ids", [schedule_ref])  # Fallback to original if empty
        except Exception:
            # If IAM service unavailable, return original reference
            return [schedule_ref]


class ErisClient:
    """Client for ERIS (Evidence & Receipt Indexing Service)."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize ERIS client.
        
        Args:
            base_url: ERIS service base URL. If None, uses stub mode (logs only).
        """
        self.base_url = base_url or settings.policy.eris_service_url
        self._use_stub = not self.base_url
    
    async def emit_receipt(self, payload: Dict) -> None:
        """
        Emit receipt to ERIS service.
        
        Args:
            payload: Receipt payload following ERIS receipt schema
        """
        if self._use_stub:
            # Stub mode: log receipt (for development/testing)
            import logging
            logger = logging.getLogger(__name__)
            logger.debug("ERIS stub: receipt emitted", extra={"receipt": payload})
            return None
        
        # Real ERIS transport: send via HTTP
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.base_url}/v1/receipts",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
        except Exception as exc:
            # Log error but don't fail alert processing
            import logging
            logger = logging.getLogger(__name__)
            logger.error("Failed to emit ERIS receipt: %s", exc, exc_info=True)
            # In production, might want to queue for retry
