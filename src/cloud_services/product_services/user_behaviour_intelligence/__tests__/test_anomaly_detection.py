"""
Unit test: Anomaly Threshold Logic (UT-UBI-03).

Per PRD Section 13.1: Test anomaly detection with z-score thresholds.
"""

import pytest
from cloud_services.product_services.user_behaviour_intelligence.anomalies.detection import AnomalyDetectionEngine
from cloud_services.product_services.user_behaviour_intelligence.models import Severity, Dimension


class TestAnomalyDetection:
    """Test anomaly detection logic."""

    def test_z_score_at_warn_threshold(self):
        """Test anomaly triggered at WARN threshold (z-score = 2.5)."""
        engine = AnomalyDetectionEngine(warn_threshold=2.5, critical_threshold=3.5)
        
        baseline_mean = 50.0
        baseline_std_dev = 10.0
        feature_value = baseline_mean + 2.5 * baseline_std_dev  # Exactly at threshold
        
        is_anomaly, severity, z_score = engine.detect_anomaly(
            feature_value=feature_value,
            baseline_mean=baseline_mean,
            baseline_std_dev=baseline_std_dev,
            dimension=Dimension.ACTIVITY
        )
        
        assert is_anomaly is True
        assert severity == Severity.WARN
        assert abs(z_score - 2.5) < 0.1

    def test_z_score_above_critical_threshold(self):
        """Test anomaly triggered at CRITICAL threshold (z-score = 3.6)."""
        engine = AnomalyDetectionEngine()
        
        baseline_mean = 50.0
        baseline_std_dev = 10.0
        feature_value = baseline_mean + 3.6 * baseline_std_dev
        
        is_anomaly, severity, z_score = engine.detect_anomaly(
            feature_value=feature_value,
            baseline_mean=baseline_mean,
            baseline_std_dev=baseline_std_dev,
            dimension=Dimension.ACTIVITY
        )
        
        assert is_anomaly is True
        assert severity == Severity.CRITICAL
        assert abs(z_score - 3.6) < 0.1

