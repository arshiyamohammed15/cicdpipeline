"""
Integration test: Config Change Effect (IT-UBI-04).

Per PRD Section 13.2: Test configuration change and receipt emission.
"""

import pytest
from cloud_services.product_services.user_behaviour_intelligence.services import UBIService
from cloud_services.product_services.user_behaviour_intelligence.models import TenantConfigRequest, SignalType


class TestConfigChange:
    """Test configuration change effects."""

    def test_config_change_emits_receipt(self):
        """Test that configuration change emits receipt to ERIS."""
        service = UBIService()
        
        # Update tenant configuration
        request = TenantConfigRequest(
            enabled_signal_types=[SignalType.RISK, SignalType.OPPORTUNITY]  # Exclude informational
        )
        
        response = service.update_tenant_config(
            tenant_id="test-tenant",
            request=request,
            created_by="test-user"
        )
        
        assert response.receipt_id is not None
        assert response.config_version != "1.0.0"  # Version incremented
        assert SignalType.INFORMATIONAL not in response.config.enabled_signal_types

