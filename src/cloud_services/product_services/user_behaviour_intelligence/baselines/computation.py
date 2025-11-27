"""
Baseline Computation Algorithm for UBI Module (EPC-9).

What: Computes baselines using EMA algorithm per PRD FR-3
Why: Generate baselines for anomaly detection
Reads/Writes: Baseline computation (no storage)
Contracts: UBI PRD FR-3
Risks: Algorithm errors, outlier handling issues
"""

import logging
from typing import List, Optional, Tuple
import statistics
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BaselineComputation:
    """
    Baseline computation using EMA algorithm.

    Per UBI PRD FR-3:
    - EMA with configurable alpha (default: 0.1)
    - SMA for initial computation until sufficient data points
    - Minimum 7 days data requirement (warm-up period)
    - Outlier exclusion (beyond 3 standard deviations)
    - Confidence calculation (low confidence < 0.5 during warm-up)
    """

    def __init__(self, alpha: float = 0.1, outlier_std_dev: float = 3.0):
        """
        Initialize baseline computation.

        Args:
            alpha: EMA alpha parameter (default: 0.1)
            outlier_std_dev: Standard deviation threshold for outlier exclusion
        """
        self.alpha = alpha
        self.outlier_std_dev = outlier_std_dev

    def compute_baseline(
        self,
        feature_values: List[float],
        min_data_points_days: int = 7
    ) -> Tuple[Optional[float], Optional[float], float]:
        """
        Compute baseline (mean, std_dev, confidence).

        Args:
            feature_values: List of feature values
            min_data_points_days: Minimum data points in days

        Returns:
            Tuple of (mean, std_dev, confidence)
        """
        if not feature_values:
            return None, None, 0.0
        
        # Filter outliers
        filtered_values = self._filter_outliers(feature_values)
        
        if not filtered_values:
            return None, None, 0.0
        
        # Check if we have enough data points
        data_points = len(filtered_values)
        has_sufficient_data = data_points >= min_data_points_days
        
        # Compute mean and std_dev
        if has_sufficient_data:
            # Use EMA for sufficient data
            mean = self._compute_ema_mean(filtered_values)
            std_dev = statistics.stdev(filtered_values) if len(filtered_values) > 1 else 0.0
            confidence = 1.0
        else:
            # Use SMA for insufficient data (warm-up period)
            mean = statistics.mean(filtered_values)
            std_dev = statistics.stdev(filtered_values) if len(filtered_values) > 1 else 0.0
            confidence = data_points / min_data_points_days  # Low confidence during warm-up
        
        return mean, std_dev, min(confidence, 1.0)

    def _filter_outliers(self, values: List[float]) -> List[float]:
        """
        Filter outliers beyond threshold.

        Args:
            values: List of feature values

        Returns:
            Filtered list of values
        """
        if len(values) < 3:
            return values
        
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        
        if std_dev == 0:
            return values
        
        threshold = self.outlier_std_dev * std_dev
        filtered = [
            v for v in values
            if abs(v - mean) <= threshold
        ]
        
        if len(filtered) < len(values):
            logger.debug(f"Filtered {len(values) - len(filtered)} outliers from {len(values)} values")
        
        return filtered

    def _compute_ema_mean(self, values: List[float]) -> float:
        """
        Compute EMA mean.

        Args:
            values: List of feature values

        Returns:
            EMA mean
        """
        if not values:
            return 0.0
        
        # Start with first value
        ema = values[0]
        
        # Apply EMA to remaining values
        for value in values[1:]:
            ema = self.alpha * value + (1 - self.alpha) * ema
        
        return ema

    def compute_z_score(self, value: float, mean: float, std_dev: float) -> float:
        """
        Compute z-score for anomaly detection.

        Args:
            value: Feature value
            mean: Baseline mean
            std_dev: Baseline standard deviation

        Returns:
            Z-score
        """
        if std_dev == 0:
            return 0.0
        
        return (value - mean) / std_dev

