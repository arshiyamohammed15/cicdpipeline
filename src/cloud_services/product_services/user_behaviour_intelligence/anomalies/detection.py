"""
Anomaly Detection Engine for UBI Module (EPC-9).

What: Detects behavioural anomalies using z-score based thresholds
Why: Flag anomalies for downstream consumers per PRD FR-4
Reads/Writes: Anomaly detection (no storage)
Contracts: UBI PRD FR-4
Risks: False positives, threshold tuning
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from ..models import Severity, Dimension
from ..baselines.computation import BaselineComputation

logger = logging.getLogger(__name__)


class AnomalyDetectionEngine:
    """
    Anomaly detection engine using z-score thresholds.

    Per UBI PRD FR-4:
    - Z-score based anomaly detection
    - Configurable thresholds: WARN > 2.5, CRITICAL > 3.5
    - Severity classification: INFO, WARN, CRITICAL
    - False positive rate target: < 5%
    """

    def __init__(
        self,
        warn_threshold: float = 2.5,
        critical_threshold: float = 3.5
    ):
        """
        Initialize anomaly detection engine.

        Args:
            warn_threshold: WARN threshold (default: 2.5)
            critical_threshold: CRITICAL threshold (default: 3.5)
        """
        self.warn_threshold = warn_threshold
        self.critical_threshold = critical_threshold
        self.baseline_computation = BaselineComputation()

    def detect_anomaly(
        self,
        feature_value: float,
        baseline_mean: float,
        baseline_std_dev: float,
        dimension: Dimension,
        tenant_thresholds: Optional[Dict[str, float]] = None
    ) -> Tuple[bool, Optional[Severity], float]:
        """
        Detect anomaly from feature value vs baseline.

        Args:
            feature_value: Current feature value
            baseline_mean: Baseline mean
            baseline_std_dev: Baseline standard deviation
            dimension: Feature dimension
            tenant_thresholds: Tenant-specific thresholds (optional)

        Returns:
            Tuple of (is_anomaly, severity, z_score)
        """
        # Use tenant-specific thresholds if provided
        warn_threshold = tenant_thresholds.get("warn", self.warn_threshold) if tenant_thresholds else self.warn_threshold
        critical_threshold = tenant_thresholds.get("critical", self.critical_threshold) if tenant_thresholds else self.critical_threshold
        
        # Compute z-score
        z_score = abs(self.baseline_computation.compute_z_score(feature_value, baseline_mean, baseline_std_dev))
        
        # Determine severity
        if z_score >= critical_threshold:
            return True, Severity.CRITICAL, z_score
        elif z_score >= warn_threshold:
            return True, Severity.WARN, z_score
        else:
            return False, Severity.INFO, z_score

