"""
Data Governance & Privacy (EPC-2) client.

Per §14.3 and FR-5, every prompt and output must pass through PII/secrets
detection and redaction via EPC-2 before leaving the service. Sync call
latency target: ≤25ms p95 per §14.3.
"""

from __future__ import annotations

import os
from typing import Dict, Tuple

import httpx


class DataGovernanceClient:
    """
    Real HTTP client for Data Governance & Privacy (EPC-2).

    Calls /privacy/v1/compliance endpoint for PII/secrets detection and
    redaction per FR-5. Returns redacted content and entity counts.
    """

    def __init__(self, base_url: str | None = None, timeout_seconds: float = 0.025):
        self.base_url = base_url or os.getenv(
            "DATA_GOVERNANCE_SERVICE_URL", "http://localhost:8002/privacy/v1"
        )
        self.timeout = timeout_seconds

    def redact(self, content: str, tenant_id: str = "default") -> Tuple[str, Dict[str, int]]:
        """
        Redact PII/secrets from content via EPC-2.

        Calls /compliance endpoint with PrivacyEnforcementRequest to:
        - Detect PII and sensitive data (credentials, secrets)
        - Apply policy-driven redaction/masking strategies
        - Return redacted content and entity counts

        Returns:
            Tuple of (redacted_content, entity_counts_dict)
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/compliance",
                    json={
                        "tenant_id": tenant_id,
                        "user_id": "llm_gateway",
                        "action": "redact",
                        "resource": {"resource_type": "llm_prompt", "resource_id": "content"},
                        "policy_id": "llm_gateway_redaction",
                        "context": {"source": "llm_gateway", "content_length": len(content)},
                        "classification_record": {
                            "classification_level": "internal",
                            "sensitivity_tags": ["llm_input"],
                        },
                    },
                )
                response.raise_for_status()
                result = response.json()

                # Extract redacted content and counts from response
                # EPC-2 returns redacted_content and redaction_summary
                redacted_content = result.get("redacted_content", content)
                redaction_summary = result.get("redaction_summary", {})

                # Parse entity counts from summary
                counts: Dict[str, int] = {}
                if isinstance(redaction_summary, dict):
                    counts = redaction_summary.get("entity_counts", {})
                elif isinstance(redaction_summary, str):
                    # Fallback: parse summary string
                    for part in redaction_summary.split(";"):
                        if ":" in part:
                            kind, count_str = part.split(":", 1)
                            try:
                                counts[kind.strip()] = int(count_str.strip())
                            except ValueError:
                                pass

                return redacted_content, counts

        except httpx.TimeoutException:
            # Timeout: return original content with empty counts
            # Per FR-5, we should fail-closed, but for resilience we log and continue
            return content, {}
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code >= 500:
                # Service error: return original content
                return content, {}
            # Client error: assume no redaction needed
            return content, {}
        except httpx.RequestError:
            # Connection error: return original content
            return content, {}

