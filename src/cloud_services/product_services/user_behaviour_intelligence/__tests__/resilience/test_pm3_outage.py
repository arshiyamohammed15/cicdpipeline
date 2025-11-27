"""
Resilience test: PM-3 Ingestion Outage (RF-UBI-01).

Per PRD Section 13.8: Test graceful degradation during PM-3 outage.
"""

import pytest
from datetime import datetime, timedelta
from cloud_services.product_services.user_behaviour_intelligence.reliability.degradation import DegradationService


class TestPM3Outage:
    """Test PM-3 outage handling."""

    def test_stale_data_detection(self):
        """Test that stale data is detected and marked."""
        degradation_service = DegradationService(stale_threshold_hours=1.0)
        
        # Mark PM-3 as unavailable
        degradation_service.mark_pm3_unavailable()
        
        # Check if data is stale
        last_update = datetime.utcnow() - timedelta(hours=2)
        is_stale = degradation_service.is_data_stale(last_update, check_pm3=True)
        
        assert is_stale is True

    def test_graceful_recovery(self):
        """Test that service recovers gracefully when PM-3 recovers."""
        degradation_service = DegradationService()
        
        # Simulate outage
        degradation_service.mark_pm3_unavailable()
        assert degradation_service.pm3_available is False
        
        # Simulate recovery
        degradation_service.mark_pm3_available()
        assert degradation_service.pm3_available is True

