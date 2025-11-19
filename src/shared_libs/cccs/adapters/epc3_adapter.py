"""
EPC-3 (Configuration & Policy Management) façade adapter.

Calls EPC-3 service endpoints for policy evaluation and GSMD snapshot validation.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from ..exceptions import PolicyUnavailableError
from ..types import PolicyDecision, PolicySnapshot

logger = logging.getLogger(__name__)


@dataclass
class EPC3AdapterConfig:
    """Configuration for EPC-3 adapter."""

    base_url: str
    timeout_seconds: float = 5.0
    api_version: str = "v1"


class EPC3PolicyAdapter:
    """
    Façade adapter for EPC-3 Configuration & Policy Management service.

    Calls policy evaluation endpoints and validates GSMD snapshot signatures.
    """

    def __init__(self, config: EPC3AdapterConfig):
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            headers={"Content-Type": "application/json"},
        )
        self._snapshot_cache: Dict[str, PolicySnapshot] = {}

    def _hash_payload(self, payload: dict) -> str:
        """Generate SHA-256 hash of policy snapshot."""
        blob = json.dumps(payload, sort_keys=True).encode()
        digest = hashlib.sha256(blob).hexdigest()
        return f"sha256:{digest}"

    async def validate_snapshot_signature(
        self, payload: dict, signature: str, public_key_id: Optional[str] = None
    ) -> bool:
        """
        Validate GSMD snapshot signature via EPC-3.

        Args:
            payload: Policy snapshot payload
            signature: Ed25519 signature
            public_key_id: Optional public key ID for signature verification

        Returns:
            True if signature is valid

        Raises:
            PolicyUnavailableError: If signature validation fails
        """
        try:
            response = await self._client.post(
                f"/policy/{self._config.api_version}/validate-signature",
                json={
                    "payload": payload,
                    "signature": signature,
                    "public_key_id": public_key_id,
                },
            )
            response.raise_for_status()
            result = response.json()
            return result.get("valid", False)
        except httpx.HTTPStatusError as e:
            logger.error(f"EPC-3 signature validation failed: {e.response.status_code}")
            raise PolicyUnavailableError("Policy snapshot signature invalid") from e
        except httpx.RequestError as e:
            logger.error(f"EPC-3 request failed: {e}")
            raise PolicyUnavailableError("EPC-3 service unavailable") from e

    async def load_snapshot(
        self, payload: dict, signature: str, public_key_id: Optional[str] = None
    ) -> PolicySnapshot:
        """
        Load and validate signed policy snapshot from EPC-3.

        Args:
            payload: Policy snapshot payload with module_id, version, rules
            signature: Ed25519 signature
            public_key_id: Optional public key ID

        Returns:
            PolicySnapshot with validated signature and hash

        Raises:
            PolicyUnavailableError: If signature invalid or service unavailable
        """
        # Validate signature via EPC-3
        is_valid = await self.validate_snapshot_signature(payload, signature, public_key_id)
        if not is_valid:
            raise PolicyUnavailableError("Policy snapshot signature invalid")

        # Generate snapshot hash
        snapshot_hash = self._hash_payload(payload)

        # Parse rules (simplified - EPC-3 should provide structured rules)
        from ..types import PolicyRule

        rules = []
        for rule_data in payload.get("rules", []):
            rules.append(
                PolicyRule(
                    rule_id=rule_data["rule_id"],
                    priority=int(rule_data.get("priority", 100)),
                    conditions=rule_data.get("conditions", {}),
                    decision=rule_data.get("decision", "deny"),
                    rationale=rule_data.get("rationale", "unspecified"),
                )
            )
        rules.sort(key=lambda r: r.priority)

        snapshot = PolicySnapshot(
            module_id=payload["module_id"],
            version=str(payload["version"]),
            rules=tuple(rules),
            signature=signature,
            snapshot_hash=snapshot_hash,
        )

        # Cache snapshot by module_id
        self._snapshot_cache[payload["module_id"]] = snapshot
        return snapshot

    async def evaluate_policy(
        self, module_id: str, inputs: dict, snapshot_hash: Optional[str] = None
    ) -> PolicyDecision:
        """
        Evaluate policy via EPC-3 service.

        Args:
            module_id: Module identifier
            inputs: Policy evaluation inputs
            snapshot_hash: Optional snapshot hash for version negotiation

        Returns:
            PolicyDecision with decision, rationale, policy_version_ids, snapshot_hash

        Raises:
            PolicyUnavailableError: If policy unavailable or evaluation fails
        """
        try:
            payload = {
                "module_id": module_id,
                "inputs": inputs,
            }
            if snapshot_hash:
                payload["snapshot_hash"] = snapshot_hash

            response = await self._client.post(
                f"/policy/{self._config.api_version}/evaluate",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

            return PolicyDecision(
                decision=result.get("decision", "deny"),
                rationale=result.get("rationale", "no_rule_matched"),
                policy_version_ids=result.get("policy_version_ids", []),
                policy_snapshot_hash=result.get("policy_snapshot_hash", ""),
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"EPC-3 evaluation failed: {e.response.status_code} - {e.response.text}")
            raise PolicyUnavailableError(f"Policy evaluation failed: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"EPC-3 request failed: {e}")
            raise PolicyUnavailableError("EPC-3 service unavailable") from e

    async def negotiate_rule_version(
        self, module_id: str, requested_version: Optional[str] = None
    ) -> str:
        """
        Negotiate policy rule version with EPC-3.

        Args:
            module_id: Module identifier
            requested_version: Optional requested version

        Returns:
            Negotiated rule version

        Raises:
            PolicyUnavailableError: If version negotiation fails
        """
        try:
            payload = {"module_id": module_id}
            if requested_version:
                payload["requested_version"] = requested_version

            response = await self._client.post(
                f"/policy/{self._config.api_version}/negotiate-version",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("rule_version", "v1")
        except httpx.HTTPStatusError as e:
            logger.error(f"EPC-3 version negotiation failed: {e.response.status_code}")
            raise PolicyUnavailableError("Rule version negotiation failed") from e
        except httpx.RequestError as e:
            logger.error(f"EPC-3 request failed: {e}")
            raise PolicyUnavailableError("EPC-3 service unavailable") from e

    async def health_check(self) -> bool:
        """
        Check EPC-3 service health.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = await self._client.get(f"/policy/{self._config.api_version}/health")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()

