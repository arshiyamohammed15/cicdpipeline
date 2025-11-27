"""
ZEROUI 2.0 Constitution Code Validator

A Python-based automated code review tool that validates code against
the ZeroUI 2.0 Constitution rules for enterprise-grade product development.

The total rule count is dynamically calculated from docs/constitution/*.json files
(single source of truth). Use config.constitution.rule_count_loader.get_rule_counts()
to get the current rule count.

Author: Constitution Validator System
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Constitution Validator System"

from .core import ConstitutionValidator
from .analyzer import CodeAnalyzer
from .reporter import ReportGenerator
from .models import Violation, ValidationResult, Severity

__all__ = [
    "ConstitutionValidator",
    "CodeAnalyzer",
    "ReportGenerator",
    "Violation",
    "ValidationResult",
    "Severity"
]
