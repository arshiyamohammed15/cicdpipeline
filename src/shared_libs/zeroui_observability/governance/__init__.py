"""
Governance for ZeroUI Observability Layer.

Phase 4 - OBS-18: Challenge Traceability Gates

Validates that every challenge (1-20) has required mappings to signals, dashboards, alerts, and tests.
"""

from .challenge_traceability_matrix import ChallengeTraceabilityMatrix, load_matrix
from .ci_validator import validate_challenge_traceability

__all__ = [
    "ChallengeTraceabilityMatrix",
    "load_matrix",
    "validate_challenge_traceability",
]
