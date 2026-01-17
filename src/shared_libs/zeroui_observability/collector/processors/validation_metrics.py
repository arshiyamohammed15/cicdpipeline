"""
Validation metrics for Schema Guard processor.

Tracks validation counts, rejections, and performance metrics.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ValidationMetrics:
    """
    Metrics for schema validation.

    Tracks:
    - Total events validated
    - Total events rejected (by reason)
    - Validation duration histogram
    """

    validated_total: int = 0
    rejected_total: int = 0
    rejected_by_reason: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    validation_durations: List[float] = field(default_factory=list)
    _max_duration_samples: int = 1000  # Keep last 1000 samples

    def record_validation(self, is_valid: bool, duration_ms: float) -> None:
        """
        Record validation result.

        Args:
            is_valid: Whether validation passed
            duration_ms: Validation duration in milliseconds
        """
        if is_valid:
            self.validated_total += 1
        else:
            self.rejected_total += 1

        # Track duration
        self.validation_durations.append(duration_ms)
        if len(self.validation_durations) > self._max_duration_samples:
            self.validation_durations.pop(0)

    def record_rejection(self, reason_code: str) -> None:
        """
        Record rejection with reason code.

        Args:
            reason_code: Rejection reason code
        """
        self.rejected_total += 1
        self.rejected_by_reason[reason_code] += 1

    def get_metrics(self) -> Dict[str, any]:
        """
        Get metrics as dictionary.

        Returns:
            Dictionary of metrics
        """
        durations = self.validation_durations
        duration_stats = {}
        if durations:
            duration_stats = {
                "p50": self._percentile(durations, 50),
                "p95": self._percentile(durations, 95),
                "p99": self._percentile(durations, 99),
                "mean": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
            }

        return {
            "zeroui_obsv_events_validated_total": self.validated_total,
            "zeroui_obsv_events_rejected_total": self.rejected_total,
            "zeroui_obsv_events_rejected_by_reason": dict(self.rejected_by_reason),
            "zeroui_obsv_validation_duration_seconds": duration_stats,
        }

    def _percentile(self, data: List[float], percentile: int) -> float:
        """
        Calculate percentile.

        Args:
            data: List of values
            percentile: Percentile (0-100)

        Returns:
            Percentile value
        """
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]
