"""
Service layer for Budgeting, Rate-Limiting & Cost Observability (EPC-13).

Business logic for budget management, rate limiting, cost calculation, and quota management.
"""

from .budget_service import BudgetService
from .rate_limit_service import RateLimitService
from .cost_service import CostService
from .quota_service import QuotaService
from .receipt_service import ReceiptService
from .event_service import EventService
from .event_subscription_service import EventSubscriptionService
from ..utils.cache import CacheManager

__all__ = [
    'BudgetService',
    'RateLimitService',
    'CostService',
    'QuotaService',
    'ReceiptService',
    'EventService',
    'EventSubscriptionService',
]

# Service factory for dependency injection
class M35ServiceFactory:
    """Factory for creating M35 services with dependencies."""

    def __init__(
        self,
        db_session,
        evidence_ledger,
        key_management,
        notification_engine,
        data_plane,
        redis_client=None
    ):
        """
        Initialize service factory.

        Args:
            db_session: Database session
            evidence_ledger: PM-7 (ERIS) evidence ledger
            key_management: EPC-11 (Key & Trust Management) key management
            notification_engine: EPC-4 (Alerting & Notification Service) notification engine
            data_plane: CCP-6 (Data & Memory Plane) data plane
            redis_client: Redis client (optional)
        """
        # Create CacheManager with Redis client
        self.cache_manager = CacheManager(redis_client=redis_client)
        
        self.event_service = EventService(notification_engine)
        self.event_subscription_service = EventSubscriptionService(data_plane)
        self.budget_service = BudgetService(db_session, data_plane, self.event_service, self.cache_manager)
        self.rate_limit_service = RateLimitService(db_session, redis_client, data_plane, self.cache_manager)
        self.cost_service = CostService(db_session)
        self.quota_service = QuotaService(db_session)
        self.receipt_service = ReceiptService(evidence_ledger, key_management)

