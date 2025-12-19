"""
Service registry for UBI Module (EPC-9).

What: Centralized accessors for shared mock services (IAM, ERIS, Data Governance)
Why: Avoid circular imports between modules (main, middleware, integrations)
Reads/Writes: Lazily initializes singleton mock clients
Contracts: Dependencies module mock contracts
Risks: Global state must be initialized before production usage
"""

import logging
from typing import Optional

from .dependencies import MockM21IAM, MockM7ERIS, MockM22DataGovernance  # EPC-1, PM-7, EPC-2 (legacy class names)

logger = logging.getLogger(__name__)

_iam: Optional[MockM21IAM] = None  # EPC-1 (Identity & Access Management)
_eris: Optional[MockM7ERIS] = None  # PM-7 (Evidence & Receipt Indexing Service / ERIS)
_data_governance: Optional[MockM22DataGovernance] = None  # EPC-2 (Data Governance & Privacy)


def initialize_services() -> None:
    """Initialize shared mock services if not already initialized."""
    global _iam, _eris, _data_governance
    if _iam is not None:
        return

    _iam = MockM21IAM()
    _eris = MockM7ERIS()
    _data_governance = MockM22DataGovernance()

    logger.info("UBI service registry initialized")


def get_iam_instance() -> MockM21IAM:
    """Return IAM mock instance."""
    global _iam
    if _iam is None:
        initialize_services()
    return _iam


def get_eris_instance() -> MockM7ERIS:
    """Return ERIS mock instance."""
    global _eris
    if _eris is None:
        initialize_services()
    return _eris


def get_data_governance_instance() -> MockM22DataGovernance:
    """Return Data Governance mock instance."""
    global _data_governance
    if _data_governance is None:
        initialize_services()
    return _data_governance


