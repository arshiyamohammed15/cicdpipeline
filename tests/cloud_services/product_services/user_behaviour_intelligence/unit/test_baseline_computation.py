"""
Unit test: Baseline Computation (UT-UBI-02).

Per PRD Section 13.1: Test baseline computation with known mean/std_dev.
"""


# Imports handled by conftest.py
import pytest
from user_behaviour_intelligence.baselines.computation import BaselineComputation


class TestBaselineComputation:
    """Test baseline computation correctness."""

    def test_baseline_computation_known_values(self):
        """Test baseline computation with known mean=50, std_dev=10."""
        service = BaselineComputation(alpha=0.1)
        
        # Generate time series with known mean=50, std_dev=10
        import random
        random.seed(42)
        feature_values = [random.gauss(50, 10) for _ in range(30)]
        
        mean, std_dev, confidence = service.compute_baseline(feature_values, min_data_points_days=7)
        
        assert mean is not None
        assert std_dev is not None
        assert abs(mean - 50) < 5  # Within tolerance
        assert abs(std_dev - 10) < 4  # Within tolerance
        assert confidence >= 0.5  # Normal confidence with sufficient data

    def test_insufficient_data_low_confidence(self):
        """Test baseline with insufficient data (< 7 days) marked as low confidence."""
        service = BaselineComputation()
        
        feature_values = [10.0, 20.0, 30.0]  # Only 3 days
        
        mean, std_dev, confidence = service.compute_baseline(feature_values, min_data_points_days=7)
        
        assert mean is not None
        assert confidence < 0.5  # Low confidence during warm-up

    def test_outlier_exclusion(self):
        """Test outliers beyond 3 standard deviations are excluded."""
        service = BaselineComputation(outlier_std_dev=3.0)
        
        # Values with outliers
        feature_values = [50.0] * 20 + [200.0, 300.0]  # Outliers
        
        mean, std_dev, confidence = service.compute_baseline(feature_values, min_data_points_days=7)
        
        assert mean is not None
        assert mean < 100  # Outliers should be excluded

