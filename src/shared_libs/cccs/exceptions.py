"""
Custom exceptions for CCCS runtime.
"""

from __future__ import annotations


class CCCSError(Exception):
    """Base error for CCCS runtime."""


class ActorUnavailableError(CCCSError):
    """Raised when actor resolution cannot complete."""


class PolicyUnavailableError(CCCSError):
    """Raised when policy snapshot is missing or invalid."""


class RedactionBlockedError(CCCSError):
    """Raised when redaction rules are not available."""


class VersionMismatchError(CCCSError):
    """Raised when API versions are incompatible."""


class BudgetExceededError(CCCSError):
    """Raised when rate limiter denies an action."""


class ReceiptSchemaError(CCCSError):
    """Raised when receipts do not match canonical schema."""


class BootstrapTimeoutError(CCCSError):
    """Raised when bootstrap fails to complete within timeout."""


