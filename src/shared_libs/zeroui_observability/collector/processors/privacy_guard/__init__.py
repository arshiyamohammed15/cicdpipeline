"""
Privacy Guard processor for OpenTelemetry Collector.

Applies allow/deny rules and verifies redaction_applied field.
"""

from .privacy_guard_processor import PrivacyGuardProcessor

__all__ = ["PrivacyGuardProcessor"]
