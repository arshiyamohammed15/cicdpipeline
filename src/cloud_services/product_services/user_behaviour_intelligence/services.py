"""
Service layer for User Behaviour Intelligence (UBI) Module (EPC-9).

What: Main orchestration service for behavioural analytics
Why: Encapsulates business logic per UBI PRD
Reads/Writes: Event processing, feature computation, baseline management, signal generation
Contracts: UBI PRD all functional requirements
Risks: Service must handle errors gracefully, respect performance budgets, and maintain accuracy
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from .models import (
    ActorProfileResponse, QuerySignalsRequest, QuerySignalsResponse,
    TenantConfigRequest, TenantConfigResponse, TenantConfigUpdateResponse,
    BehaviouralSignal, BehaviouralFeature, BehaviouralBaseline,
    ActorScope, Dimension, SignalType, Severity, SignalStatus
)
from .config import ConfigurationManager
from .integrations.pm3_client import PM3Client
from .processors.event_mapper import EventMapper
from .processors.event_ingestion import EventIngestionPipeline
from .features.computation import FeatureComputationService
from .baselines.computation import BaselineComputation
from .anomalies.detection import AnomalyDetectionEngine
from .signals.generation import SignalGenerationService
from .streaming.publisher import EventStreamPublisher
from .receipts.generator import ReceiptGenerator
from .integrations.eris_client import ERISClient
from .observability.metrics import MetricsRegistry
from .reliability.degradation import DegradationService
from .database.repositories import (
    EventRepository, FeatureRepository, BaselineRepository,
    SignalRepository, ConfigRepository
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class UBIService:
    """
    Main UBI service orchestrating behavioural analytics.

    Per UBI PRD: Implements feature computation, baseline management, anomaly detection, signal generation.
    """

    def __init__(self):
        """Initialize UBI service."""
        self.config_manager = ConfigurationManager()
        self.event_mapper = EventMapper()
        self.event_ingestion = EventIngestionPipeline(self.config_manager)
        self.feature_computation = FeatureComputationService()
        self.baseline_computation = BaselineComputation()
        self.anomaly_detection = AnomalyDetectionEngine()
        self.signal_generation = SignalGenerationService()
        self.stream_publisher = EventStreamPublisher()
        self.receipt_generator = ReceiptGenerator()
        self.eris_client = ERISClient()
        self.metrics_registry = MetricsRegistry()
        self.degradation_service = DegradationService()
        
        # Initialize PM-3 client and subscribe
        self.pm3_client = PM3Client(routing_class="analytics_store")
        self.pm3_client.subscribe(self._handle_pm3_event)

    def get_actor_profile(
        self,
        actor_id: str,
        tenant_id: str,
        window: Optional[str] = None,
        db: Optional[Session] = None
    ) -> ActorProfileResponse:
        """
        Get actor behaviour profile per PRD Section 11.1.

        Args:
            actor_id: Actor identifier
            tenant_id: Tenant identifier
            window: Time window (default: last 7 days)
            db: Database session (optional, will create if not provided)

        Returns:
            ActorProfileResponse with signals, features, baselines
        """
        logger.info(f"Getting actor profile: actor_id={actor_id}, tenant_id={tenant_id}, window={window}")
        
        if db is None:
            from .database.connection import get_db
            db_gen = get_db()
            db = next(db_gen)
            try:
                return self._get_actor_profile_impl(actor_id, tenant_id, window, db)
            finally:
                db.close()
        else:
            return self._get_actor_profile_impl(actor_id, tenant_id, window, db)

    def _get_actor_profile_impl(
        self,
        actor_id: str,
        tenant_id: str,
        window: Optional[str],
        db: Session
    ) -> ActorProfileResponse:
        """Internal implementation of get_actor_profile."""
        signal_repo = SignalRepository(db)
        feature_repo = FeatureRepository(db)
        baseline_repo = BaselineRepository(db)
        
        # Query signals for actor
        signals = signal_repo.query(
            tenant_id=tenant_id,
            actor_scope="actor",
            actor_or_group_id=actor_id,
            limit=100
        )
        
        # Group signals by dimension
        signals_by_dimension = {}
        for signal in signals:
            dim = signal.dimension.value
            if dim not in signals_by_dimension:
                signals_by_dimension[dim] = []
            signals_by_dimension[dim].append(signal)
        
        # Get latest features
        features = []
        # In production, would query for latest features
        
        # Get baselines
        baselines = []
        # In production, would query for current baselines
        
        # Check if data is stale
        is_stale = self.degradation_service.is_data_stale(None)
        
        return ActorProfileResponse(
            actor_id=actor_id,
            tenant_id=tenant_id,
            actor_type="human",  # Would determine from database
            signals=signals_by_dimension,
            features=features,
            baselines=baselines,
            stale=is_stale
        )

    def query_signals(
        self,
        request: QuerySignalsRequest,
        db: Optional[Session] = None
    ) -> QuerySignalsResponse:
        """
        Query signals per PRD Section 11.2.

        Args:
            request: QuerySignalsRequest with filters
            db: Database session (optional)

        Returns:
            QuerySignalsResponse with matching signals
        """
        logger.info(f"Querying signals: tenant_id={request.tenant_id}, scope={request.scope}")
        
        if db is None:
            from .database.connection import get_db
            db_gen = get_db()
            db = next(db_gen)
            try:
                return self._query_signals_impl(request, db)
            finally:
                db.close()
        else:
            return self._query_signals_impl(request, db)

    def _query_signals_impl(
        self,
        request: QuerySignalsRequest,
        db: Session
    ) -> QuerySignalsResponse:
        """Internal implementation of query_signals."""
        signal_repo = SignalRepository(db)
        
        # Parse time range
        from datetime import datetime
        time_range = {}
        if "from" in request.time_range:
            time_range["from"] = datetime.fromisoformat(request.time_range["from"].replace('Z', '+00:00'))
        if "to" in request.time_range:
            time_range["to"] = datetime.fromisoformat(request.time_range["to"].replace('Z', '+00:00'))
        
        # Parse filters
        min_severity = None
        signal_types = None
        if request.filters:
            min_severity = request.filters.get("min_severity")
            signal_types = request.filters.get("signal_types")
        
        # Query signals
        signals = signal_repo.query(
            tenant_id=request.tenant_id,
            actor_scope=request.scope.value if hasattr(request.scope, 'value') else request.scope,
            dimensions=[d.value for d in request.dimensions] if request.dimensions else None,
            time_range=time_range if time_range else None,
            min_severity=min_severity,
            signal_types=signal_types,
            limit=1000
        )
        
        # Check if data is stale
        is_stale = self.degradation_service.is_data_stale(None)
        
        return QuerySignalsResponse(
            signals=signals,
            stale=is_stale
        )

    def get_tenant_config(
        self,
        tenant_id: str,
        db: Optional[Session] = None
    ) -> TenantConfigResponse:
        """
        Get tenant configuration per PRD Section 11.4.

        Args:
            tenant_id: Tenant identifier
            db: Database session (optional)

        Returns:
            TenantConfigResponse with current configuration
        """
        logger.info(f"Getting tenant config: tenant_id={tenant_id}")
        
        if db is None:
            from .database.connection import get_db
            db_gen = get_db()
            db = next(db_gen)
            try:
                return self._get_tenant_config_impl(tenant_id, db)
            finally:
                db.close()
        else:
            return self._get_tenant_config_impl(tenant_id, db)

    def _get_tenant_config_impl(
        self,
        tenant_id: str,
        db: Session
    ) -> TenantConfigResponse:
        """Internal implementation of get_tenant_config."""
        config_repo = ConfigRepository(db)
        db_config = config_repo.get(tenant_id)
        
        if db_config:
            return db_config
        else:
            # Return default config from config manager
            return self.config_manager.get_config(tenant_id)

    def update_tenant_config(
        self,
        tenant_id: str,
        request: TenantConfigRequest,
        created_by: Optional[str] = None,
        db: Optional[Session] = None
    ) -> TenantConfigUpdateResponse:
        """
        Update tenant configuration per PRD Section 11.4.

        Args:
            tenant_id: Tenant identifier
            request: TenantConfigRequest with updates
            created_by: User/service that made the change
            db: Database session (optional)

        Returns:
            TenantConfigUpdateResponse with updated configuration and receipt ID
        """
        logger.info(f"Updating tenant config: tenant_id={tenant_id}")
        
        if db is None:
            from .database.connection import get_db
            db_gen = get_db()
            db = next(db_gen)
            try:
                return self._update_tenant_config_impl(tenant_id, request, created_by, db)
            finally:
                db.commit()
                db.close()
        else:
            return self._update_tenant_config_impl(tenant_id, request, created_by, db)

    def _update_tenant_config_impl(
        self,
        tenant_id: str,
        request: TenantConfigRequest,
        created_by: Optional[str],
        db: Session
    ) -> TenantConfigUpdateResponse:
        """Internal implementation of update_tenant_config."""
        # Update configuration via config manager
        updated_config = self.config_manager.update_config(tenant_id, request, created_by)
        
        # Store in database
        config_repo = ConfigRepository(db)
        config_repo.create_or_update(updated_config)
        
        # Generate receipt for configuration change
        receipt = self.receipt_generator.generate_config_receipt(
            tenant_id=tenant_id,
            config_version=updated_config.config_version,
            actor_id=created_by or "unknown",
            actor_type="human",
            decision_status="pass",
            decision_rationale=f"Configuration updated to version {updated_config.config_version}",
            inputs={"config_version": updated_config.config_version},
            result={"config": updated_config.model_dump()}
        )
        
        # Emit receipt to ERIS (non-blocking, safe in running event loop)
        receipt_id = None
        try:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                loop.create_task(self.eris_client.emit_receipt(receipt))
            else:
                receipt_id = asyncio.run(self.eris_client.emit_receipt(receipt))
        except Exception as e:
            logger.error(f"Error emitting receipt to ERIS: {e}")
            receipt_id = receipt.get("receipt_id")
        
        return TenantConfigUpdateResponse(
            tenant_id=tenant_id,
            config_version=updated_config.config_version,
            config=updated_config,
            receipt_id=receipt_id
        )

    def _handle_pm3_event(self, signal_envelope: Dict[str, Any]) -> bool:
        """
        Handle PM-3 SignalEnvelope event.

        Args:
            signal_envelope: SignalEnvelope dictionary from PM-3

        Returns:
            True if processed successfully, False otherwise
        """
        try:
            # Map to BehaviouralEvent
            behavioural_event = self.event_mapper.map_signal_envelope(signal_envelope)
            if not behavioural_event:
                return False
            
            # Ingest event
            success = self.event_ingestion.ingest_event(behavioural_event)
            
            # Update metrics
            self.metrics_registry.increment_events_processed(
                behavioural_event.tenant_id,
                behavioural_event.event_type,
                "success" if success else "failure"
            )
            
            return success
        except Exception as e:
            logger.error(f"Error handling PM-3 event: {e}", exc_info=True)
            return False

