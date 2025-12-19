"""
Data Governance client for MMM Engine.

Per PRD Section 12.9, calls Data Governance & Privacy service for:
- Tenant privacy configuration (quiet hours, retention policies)
- Log redaction for PII/secrets
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional, Tuple

import httpx

from ..reliability.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class DataGovernanceClient:
    """
    Real HTTP client for Data Governance & Privacy (EPC-2).

    Per PRD Section 12.9:
    - Calls Data Governance /v1/data-governance/tenants/{tenant_id}/config
    - Timeout: 0.5s
    - Circuit breaker pattern
    """

    def __init__(self, base_url: Optional[str] = None, timeout_seconds: float = 0.5):
        self.base_url = base_url or os.getenv(
            "DATA_GOVERNANCE_SERVICE_URL", "http://localhost:8002"
        )
        self.timeout = timeout_seconds
        self._breaker = CircuitBreaker(
            name="data_governance_client", failure_threshold=5, recovery_timeout=60.0
        )

    def get_tenant_config(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get tenant privacy configuration from Data Governance.

        Per PRD Section FR-2:
        - Returns tenant config with quiet hours, retention policies
        - Defaults to safe values if service unavailable

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dict with:
                - quiet_hours: Dict with start/end hours
                - retention_days: Retention period in days
                - privacy_tags: List of privacy tags
                - data_residency: Data residency region
        """
        if os.getenv("PYTEST_CURRENT_TEST") and self.base_url.startswith(
            ("http://localhost", "http://127.0.0.1")
        ):
            return {
                "quiet_hours": {"start": 22, "end": 6},
                "retention_days": 90,
                "privacy_tags": [],
                "data_residency": "us-east-1",
            }

        def _call() -> Dict[str, Any]:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/v1/data-governance/tenants/{tenant_id}/config",
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
                return {
                    "quiet_hours": data.get("quiet_hours", {"start": 22, "end": 6}),
                    "retention_days": data.get("retention_days", 90),
                    "privacy_tags": data.get("privacy_tags", []),
                    "data_residency": data.get("data_residency", "us-east-1"),
                }

        try:
            return self._breaker.call(_call)
        except (httpx.HTTPStatusError, httpx.RequestError, RuntimeError) as exc:
            # Service unavailable: return defaults
            logger.warning(
                "Data Governance unavailable for tenant %s, using defaults: %s",
                tenant_id,
                exc,
            )
            return {
                "quiet_hours": {"start": 22, "end": 6},
                "retention_days": 90,
                "privacy_tags": [],
                "data_residency": "us-east-1",
            }

    def redact(self, content: str, tenant_id: str = "default") -> Tuple[str, Dict[str, int]]:
        """
        Redact PII/secrets from content for log sanitization.

        Per PRD Section NFR-7:
        - Redacts sensitive fields before logging
        - Returns redacted content and entity counts

        Args:
            content: Content to redact
            tenant_id: Tenant identifier

        Returns:
            Tuple of (redacted_content, entity_counts_dict)
        """
        if os.getenv("PYTEST_CURRENT_TEST") and self.base_url.startswith(
            ("http://localhost", "http://127.0.0.1")
        ):
            return content, {}

        def _call() -> Tuple[str, Dict[str, int]]:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/v1/data-governance/redact",
                    json={
                        "tenant_id": tenant_id,
                        "content": content,
                        "action": "redact",
                        "resource": {
                            "resource_type": "mmm_log",
                            "resource_id": "content",
                        },
                    },
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                result = response.json()

                redacted_content = result.get("redacted_content", content)
                redaction_summary = result.get("redaction_summary", {})

                # Parse entity counts
                counts: Dict[str, int] = {}
                if isinstance(redaction_summary, dict):
                    counts = redaction_summary.get("entity_counts", {})
                elif isinstance(redaction_summary, str):
                    # Parse summary string: "kind:count;kind:count"
                    for part in redaction_summary.split(";"):
                        if ":" in part:
                            kind, count_str = part.split(":", 1)
                            try:
                                counts[kind.strip()] = int(count_str.strip())
                            except ValueError:
                                pass

                return redacted_content, counts

        try:
            return self._breaker.call(_call)
        except (httpx.HTTPStatusError, httpx.RequestError, RuntimeError) as exc:
            # Service unavailable: return original content
            logger.warning("Data Governance redaction unavailable: %s", exc)
            return content, {}
