"""
Service registry for MMM Engine real service clients.

Per PRD Phase 1, all mock clients replaced with real HTTP clients.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from .integrations.iam_client import IAMClient
from .integrations.eris_client import ERISClient
from .integrations.llm_gateway_client import LLMGatewayClient
from .integrations.policy_client import PolicyClient, PolicyCache
from .integrations.data_governance_client import DataGovernanceClient
from .integrations.ubi_client import UBIClient

logger = logging.getLogger(__name__)

_iam: Optional[IAMClient] = None
_eris: Optional[ERISClient] = None
_policy_client: Optional[PolicyClient] = None
_policy_cache: Optional[PolicyCache] = None
_llm_gateway: Optional[LLMGatewayClient] = None
_data_governance: Optional[DataGovernanceClient] = None
_ubi_signals: Optional[UBIClient] = None


def initialize_services() -> None:
    """Initialize real service clients with environment variable configuration."""
    global _iam, _eris, _policy_client, _policy_cache, _llm_gateway, _data_governance, _ubi_signals
    if _iam is not None:
        return

    # Initialize IAM client
    _iam = IAMClient(
        base_url=os.getenv("IAM_SERVICE_URL"),
        timeout_seconds=2.0,
    )

    # Initialize ERIS client
    _eris = ERISClient(
        base_url=os.getenv("ERIS_SERVICE_URL"),
        timeout_seconds=2.0,
    )

    # Initialize Policy client with cache
    _policy_client = PolicyClient(
        base_url=os.getenv("POLICY_SERVICE_URL"),
        timeout_seconds=0.5,
        latency_budget_ms=500,
    )
    _policy_cache = PolicyCache(
        client=_policy_client,
        max_staleness_seconds=60,
        fail_open_window_seconds=300,
    )

    # Initialize LLM Gateway client
    _llm_gateway = LLMGatewayClient(
        base_url=os.getenv("LLM_GATEWAY_SERVICE_URL"),
        timeout_seconds=3.0,
    )

    # Initialize Data Governance client
    _data_governance = DataGovernanceClient(
        base_url=os.getenv("DATA_GOVERNANCE_SERVICE_URL"),
        timeout_seconds=0.5,
    )

    # Initialize UBI client
    _ubi_signals = UBIClient(
        base_url=os.getenv("UBI_SERVICE_URL"),
        timeout_seconds=1.0,
    )

    logger.info("MMM service registry initialized with real clients")


def get_iam() -> IAMClient:
    """Get IAM client for authentication and authorization."""
    initialize_services()
    return _iam  # type: ignore[return-value]


def get_eris() -> ERISClient:
    """Get ERIS client for receipt emission."""
    initialize_services()
    return _eris  # type: ignore[return-value]


def get_policy_service() -> PolicyCache:
    """
    Get Policy service cache for policy evaluation.

    Returns PolicyCache which provides cached policy snapshots with
    fail-open/fail-closed logic.
    """
    initialize_services()
    return _policy_cache  # type: ignore[return-value]


def get_llm_gateway() -> LLMGatewayClient:
    """Get LLM Gateway client for Mentor/Multiplier content generation."""
    initialize_services()
    return _llm_gateway  # type: ignore[return-value]


def get_data_governance() -> DataGovernanceClient:
    """Get Data Governance client for tenant config and log redaction."""
    initialize_services()
    return _data_governance  # type: ignore[return-value]


def get_ubi_signal_service() -> UBIClient:
    """Get UBI client for recent BehaviouralSignals retrieval."""
    initialize_services()
    return _ubi_signals  # type: ignore[return-value]


