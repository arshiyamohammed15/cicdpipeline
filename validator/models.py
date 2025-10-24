"""
Data models for the ZEROUI 2.0 Constitution validator.

This module contains the data classes used throughout the validation system.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class Severity(Enum):
    """Severity levels for rule violations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Violation:
    """Represents a rule violation found in code."""
    rule_id: str
    severity: Severity
    message: str
    file_path: str
    line_number: int
    code_snippet: str = ""
    rule_name: str = ""
    column_number: int = 0
    fix_suggestion: Optional[str] = None
    category: Optional[str] = None
    # Legacy support
    rule_number: Optional[int] = None


@dataclass
class ValidationResult:
    """Results of code validation against constitution rules."""
    file_path: str
    total_violations: int
    violations_by_severity: Dict[Severity, int]
    violations: List[Violation]
    processing_time: float
    compliance_score: float
