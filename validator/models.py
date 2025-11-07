"""
Data models for the ZEROUI 2.0 Constitution validator.

This module contains the data classes used throughout the validation system.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from .rule_registry import get_rule_metadata, slugify_rule_name

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
    severity: Severity
    message: str
    file_path: str
    line_number: int
    rule_id: str = ""
    code_snippet: str = ""
    rule_name: str = ""
    column_number: int = 0
    fix_suggestion: Optional[str] = None
    category: Optional[str] = None
    # Legacy support
    rule_number: Optional[int] = None

    def __post_init__(self) -> None:
        """Populate rule metadata dynamically when available."""
        metadata = get_rule_metadata(self.rule_name) if self.rule_name else None

        if metadata:
            if not self.rule_id:
                self.rule_id = metadata.rule_id
            if self.rule_number is None:
                self.rule_number = metadata.number
            if not self.category:
                self.category = metadata.category
        else:
            # Fallback for unmapped/internal rules
            if not self.rule_id:
                resolved_name = self.rule_name or "Unmapped Rule"
                self.rule_id = f"rule:{slugify_rule_name(resolved_name)}"
            if self.rule_number is None:
                self.rule_number = None


@dataclass
class ValidationResult:
    """Results of code validation against constitution rules."""
    file_path: str
    total_violations: int
    violations_by_severity: Dict[Severity, int]
    violations: List[Violation]
    processing_time: float
    compliance_score: float
