"""
Service registry for MMM Engine shared mocks and singletons.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from .dependencies import (
    MockIAMClient,
    MockPolicyService,
    MockLLMGateway,
    MockDataGovernance,
    MockUBISignalService,
)
from .integrations.eris_client import ERISClient

logger = logging.getLogger(__name__)

_iam: Optional[MockIAMClient] = None
_eris: Optional[object] = None
_policy: Optional[MockPolicyService] = None
_llm_gateway: Optional[MockLLMGateway] = None
_data_governance: Optional[MockDataGovernance] = None
_ubi_signals: Optional[MockUBISignalService] = None


def initialize_services() -> None:
    """Initialize shared mocks."""
    global _iam, _eris, _policy, _llm_gateway, _data_governance, _ubi_signals
    if _iam is not None:
        return
    _iam = MockIAMClient()
    _eris = (
        ERISClient(base_url=os.getenv("MMM_ERIS_BASE_URL"))
        if os.getenv("MMM_ERIS_BASE_URL")
        else ERISClient(base_url=None)
    )
    _policy = MockPolicyService()
    _llm_gateway = MockLLMGateway()
    _data_governance = MockDataGovernance()
    _ubi_signals = MockUBISignalService()
    logger.info("MMM service registry initialized")


def get_iam() -> MockIAMClient:
    initialize_services()
    return _iam  # type: ignore[return-value]


def get_eris() -> ERISClient:
    initialize_services()
    return _eris  # type: ignore[return-value]


def get_policy_service() -> MockPolicyService:
    initialize_services()
    return _policy  # type: ignore[return-value]


def get_llm_gateway() -> MockLLMGateway:
    initialize_services()
    return _llm_gateway  # type: ignore[return-value]


def get_data_governance() -> MockDataGovernance:
    initialize_services()
    return _data_governance  # type: ignore[return-value]


def get_ubi_signal_service() -> MockUBISignalService:
    initialize_services()
    return _ubi_signals  # type: ignore[return-value]


