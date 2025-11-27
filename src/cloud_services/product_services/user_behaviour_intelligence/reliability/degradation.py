"""
Degradation Service for UBI Module (EPC-9).

What: Detects and handles service degradation
Why: Ensure graceful degradation per PRD NFR-6
Reads/Writes: Degradation state management
Contracts: UBI PRD NFR-6
Risks: Degradation detection failures
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DegradationService:
    """
    Degradation service for handling service degradation.

    Per UBI PRD NFR-6:
    - Stale data detection (data older than 1 hour, PM-3 unavailability)
    - stale: true flag in API responses
    - Graceful recovery (automatic resume when dependencies recover)
    - Baseline corruption prevention during outages
    """

    def __init__(self, stale_threshold_hours: float = 1.0):
        """
        Initialize degradation service.

        Args:
            stale_threshold_hours: Stale data threshold in hours (default: 1.0)
        """
        self.stale_threshold_hours = stale_threshold_hours
        self.pm3_available = True
        self.eris_available = True
        self.last_pm3_event: Optional[datetime] = None
        self.last_baseline_recompute: Optional[datetime] = None

    def is_data_stale(
        self,
        last_update: Optional[datetime],
        check_pm3: bool = True
    ) -> bool:
        """
        Check if data is stale.

        Args:
            last_update: Last update timestamp
            check_pm3: Whether to check PM-3 availability

        Returns:
            True if stale, False otherwise
        """
        if not last_update:
            return True
        
        # Check if data is older than threshold
        now = datetime.utcnow()
        age_hours = (now - last_update).total_seconds() / 3600.0
        
        if age_hours > self.stale_threshold_hours:
            return True
        
        # Check PM-3 availability if requested
        if check_pm3 and not self.pm3_available:
            return True
        
        return False

    def mark_pm3_unavailable(self) -> None:
        """Mark PM-3 as unavailable."""
        self.pm3_available = False
        logger.warning("PM-3 marked as unavailable")

    def mark_pm3_available(self) -> None:
        """Mark PM-3 as available."""
        self.pm3_available = True
        self.last_pm3_event = datetime.utcnow()
        logger.info("PM-3 marked as available")

    def mark_eris_unavailable(self) -> None:
        """Mark ERIS as unavailable."""
        self.eris_available = False
        logger.warning("ERIS marked as unavailable")

    def mark_eris_available(self) -> None:
        """Mark ERIS as available."""
        self.eris_available = True
        logger.info("ERIS marked as available")

    def update_last_pm3_event(self) -> None:
        """Update last PM-3 event timestamp."""
        self.last_pm3_event = datetime.utcnow()

    def update_last_baseline_recompute(self) -> None:
        """Update last baseline recompute timestamp."""
        self.last_baseline_recompute = datetime.utcnow()

    def get_degradation_status(self) -> Dict[str, Any]:
        """
        Get degradation status.

        Returns:
            Degradation status dictionary
        """
        return {
            "pm3_available": self.pm3_available,
            "eris_available": self.eris_available,
            "last_pm3_event": self.last_pm3_event.isoformat() if self.last_pm3_event else None,
            "last_baseline_recompute": self.last_baseline_recompute.isoformat() if self.last_baseline_recompute else None,
            "stale_threshold_hours": self.stale_threshold_hours
        }

