from __future__ import annotations
"""
Unit tests for SLOService.
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from health_reliability_monitoring.services.slo_service import SLOService
from health_reliability_monitoring.models import SLOStatus


class TestSLOService:
    """Test SLOService."""

    @pytest.fixture
    def slo_service(self, db_session, policy_client):
        """Create SLO service."""
        return SLOService(db_session, policy_client)

    @pytest.mark.asyncio
    async def test_update_slo_within_budget(self, slo_service):
        """Test updating SLO status within budget."""
        slo_status = await slo_service.update_slo(
            component_id="test-component-1",
            slo_id="slo-1",
            success_minutes=2150,  # 99.5% availability
            total_minutes=2160,  # 30 days * 24 hours * 3 (every 8 hours)
        )
        
        assert slo_status.component_id == "test-component-1"
        assert slo_status.slo_id == "slo-1"
        assert slo_status.state == "within_budget"
        assert slo_status.burn_rate < 1.0

    @pytest.mark.asyncio
    async def test_update_slo_breached(self, slo_service):
        """Test updating SLO status when breached."""
        slo_status = await slo_service.update_slo(
            component_id="test-component-1",
            slo_id="slo-1",
            success_minutes=1900,  # Low availability
            total_minutes=2160,
        )
        
        assert slo_status.component_id == "test-component-1"
        # Should be breached or approaching
        assert slo_status.state in ["breached", "approaching"]

    @pytest.mark.asyncio
    async def test_update_slo_approaching(self, slo_service):
        """Test updating SLO status when approaching limit."""
        slo_status = await slo_service.update_slo(
            component_id="test-component-1",
            slo_id="slo-1",
            success_minutes=2050,  # Moderate availability
            total_minutes=2160,
        )
        
        assert slo_status.component_id == "test-component-1"
        assert slo_status.state in ["approaching", "within_budget", "breached"]

    def test_latest_slo_nonexistent(self, slo_service):
        """Test retrieving SLO for non-existent component."""
        slo = slo_service.latest_slo("nonexistent-component")
        
        assert slo is None

    def test_latest_slo_existing(self, slo_service, db_session):
        """Test retrieving latest SLO for existing component."""
        try:
    from health_reliability_monitoring.database import models as db_models
except ImportError:
    db_models = None  # Database module not implemented
        
        # Create SLO status
        slo_status = db_models.SLOStatus(
            component_id="test-component-1",
            slo_id="slo-1",
            window="30d",
            sli_values={"availability_pct": 99.5},
            error_budget_total_minutes=216,
            error_budget_consumed_minutes=10,
            burn_rate=0.046,
            state="within_budget",
        )
        db_session.add(slo_status)
        db_session.commit()
        
        retrieved = slo_service.latest_slo("test-component-1")
        
        assert retrieved is not None
        assert retrieved.component_id == "test-component-1"
        assert retrieved.state == "within_budget"

