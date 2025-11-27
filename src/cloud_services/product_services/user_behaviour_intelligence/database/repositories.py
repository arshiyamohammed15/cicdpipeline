"""
Database repositories for UBI Module (EPC-9).

What: Repository pattern for database operations
Why: Encapsulate database access logic, enable testing
Reads/Writes: Database CRUD operations
Contracts: Repository interfaces
Risks: Transaction management, connection leaks
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from .models import (
    BehaviouralEvent, BehaviouralFeature, BehaviouralBaseline,
    BehaviouralSignal, TenantConfiguration, ReceiptQueue, ReceiptDLQ
)

logger = logging.getLogger(__name__)


class EventRepository:
    """Repository for BehaviouralEvent operations."""

    def __init__(self, session: Session):
        """
        Initialize event repository.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def create(self, event: BehaviouralEvent) -> BehaviouralEvent:
        """
        Create behavioural event.

        Args:
            event: BehaviouralEvent to create

        Returns:
            Created BehaviouralEvent
        """
        db_event = BehaviouralEvent(
            event_id=event.event_id,
            tenant_id=event.tenant_id,
            actor_id=event.actor_id,
            actor_type=event.actor_type.value,
            source_system=event.source_system,
            event_type=event.event_type,
            timestamp_utc=datetime.fromisoformat(event.timestamp_utc.replace('Z', '+00:00')),
            ingested_at=datetime.fromisoformat(event.ingested_at.replace('Z', '+00:00')),
            properties=event.properties,
            privacy_tags=event.privacy_tags,
            schema_version=event.schema_version,
            trace_id=event.trace_id,
            span_id=event.span_id,
            correlation_id=event.correlation_id,
            resource=event.resource,
            dt=date.fromisoformat(event.timestamp_utc[:10])
        )
        self.session.add(db_event)
        return event

    def get_by_id(self, event_id: str, tenant_id: str) -> Optional[BehaviouralEvent]:
        """
        Get event by ID.

        Args:
            event_id: Event identifier
            tenant_id: Tenant identifier

        Returns:
            BehaviouralEvent or None
        """
        db_event = self.session.query(BehaviouralEvent).filter(
            and_(
                BehaviouralEvent.event_id == event_id,
                BehaviouralEvent.tenant_id == tenant_id
            )
        ).first()
        
        if not db_event:
            return None
        
        return self._to_model(db_event)

    def query_by_tenant_and_time_range(
        self,
        tenant_id: str,
        start_time: datetime,
        end_time: datetime,
        actor_id: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        limit: int = 1000
    ) -> List[BehaviouralEvent]:
        """
        Query events by tenant and time range.

        Args:
            tenant_id: Tenant identifier
            start_time: Start timestamp
            end_time: End timestamp
            actor_id: Optional actor filter
            event_types: Optional event type filter
            limit: Maximum results

        Returns:
            List of BehaviouralEvent
        """
        query = self.session.query(BehaviouralEvent).filter(
            and_(
                BehaviouralEvent.tenant_id == tenant_id,
                BehaviouralEvent.timestamp_utc >= start_time,
                BehaviouralEvent.timestamp_utc <= end_time
            )
        )
        
        if actor_id:
            query = query.filter(BehaviouralEvent.actor_id == actor_id)
        
        if event_types:
            query = query.filter(BehaviouralEvent.event_type.in_(event_types))
        
        query = query.order_by(desc(BehaviouralEvent.timestamp_utc)).limit(limit)
        
        db_events = query.all()
        return [self._to_model(e) for e in db_events]

    def _to_model(self, db_event: BehaviouralEvent) -> BehaviouralEvent:
        """Convert database model to Pydantic model."""
        from ..models import ActorType
        return BehaviouralEvent(
            event_id=str(db_event.event_id),
            tenant_id=db_event.tenant_id,
            actor_id=db_event.actor_id,
            actor_type=ActorType(db_event.actor_type),
            source_system=db_event.source_system,
            event_type=db_event.event_type,
            timestamp_utc=db_event.timestamp_utc.isoformat(),
            ingested_at=db_event.ingested_at.isoformat(),
            properties=db_event.properties,
            privacy_tags=db_event.privacy_tags,
            schema_version=db_event.schema_version,
            trace_id=db_event.trace_id,
            span_id=db_event.span_id,
            correlation_id=db_event.correlation_id,
            resource=db_event.resource
        )


class FeatureRepository:
    """Repository for BehaviouralFeature operations."""

    def __init__(self, session: Session):
        """
        Initialize feature repository.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def create(self, feature: BehaviouralFeature) -> BehaviouralFeature:
        """
        Create behavioural feature.

        Args:
            feature: BehaviouralFeature to create

        Returns:
            Created BehaviouralFeature
        """
        db_feature = BehaviouralFeature(
            feature_id=feature.feature_id,
            tenant_id=feature.tenant_id,
            actor_scope=feature.actor_scope.value,
            actor_or_group_id=feature.actor_or_group_id,
            feature_name=feature.feature_name,
            window_start=datetime.fromisoformat(feature.window_start.replace('Z', '+00:00')),
            window_end=datetime.fromisoformat(feature.window_end.replace('Z', '+00:00')),
            value=float(feature.value),
            dimension=feature.dimension.value,
            confidence=float(feature.confidence),
            metadata_json=feature.metadata,
            dt=date.fromisoformat(feature.window_end[:10])
        )
        self.session.add(db_feature)
        return feature

    def get_latest(
        self,
        tenant_id: str,
        actor_scope: str,
        actor_or_group_id: str,
        feature_name: str
    ) -> Optional[BehaviouralFeature]:
        """
        Get latest feature value.

        Args:
            tenant_id: Tenant identifier
            actor_scope: Actor scope
            actor_or_group_id: Actor or group identifier
            feature_name: Feature name

        Returns:
            Latest BehaviouralFeature or None
        """
        db_feature = self.session.query(BehaviouralFeature).filter(
            and_(
                BehaviouralFeature.tenant_id == tenant_id,
                BehaviouralFeature.actor_scope == actor_scope,
                BehaviouralFeature.actor_or_group_id == actor_or_group_id,
                BehaviouralFeature.feature_name == feature_name
            )
        ).order_by(desc(BehaviouralFeature.window_end)).first()
        
        if not db_feature:
            return None
        
        return self._to_model(db_feature)

    def _to_model(self, db_feature: BehaviouralFeature) -> BehaviouralFeature:
        """Convert database model to Pydantic model."""
        from ..models import ActorScope, Dimension
        return BehaviouralFeature(
            feature_id=str(db_feature.feature_id),
            tenant_id=db_feature.tenant_id,
            actor_scope=ActorScope(db_feature.actor_scope),
            actor_or_group_id=db_feature.actor_or_group_id,
            feature_name=db_feature.feature_name,
            window_start=db_feature.window_start.isoformat(),
            window_end=db_feature.window_end.isoformat(),
            value=float(db_feature.value),
            dimension=Dimension(db_feature.dimension),
            confidence=float(db_feature.confidence),
            metadata=db_feature.metadata_json
        )


class BaselineRepository:
    """Repository for BehaviouralBaseline operations."""

    def __init__(self, session: Session):
        """
        Initialize baseline repository.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def create_or_update(self, baseline: BehaviouralBaseline) -> BehaviouralBaseline:
        """
        Create or update baseline.

        Args:
            baseline: BehaviouralBaseline to create/update

        Returns:
            Created/updated BehaviouralBaseline
        """
        # Check if baseline exists
        existing = self.session.query(BehaviouralBaseline).filter(
            and_(
                BehaviouralBaseline.tenant_id == baseline.tenant_id,
                BehaviouralBaseline.actor_scope == baseline.actor_scope.value,
                BehaviouralBaseline.actor_or_group_id == baseline.actor_or_group_id,
                BehaviouralBaseline.feature_name == baseline.feature_name
            )
        ).first()
        
        if existing:
            # Update existing
            existing.mean = float(baseline.mean)
            existing.std_dev = float(baseline.std_dev)
            existing.percentiles = baseline.percentiles
            existing.last_recomputed_at = datetime.fromisoformat(baseline.last_recomputed_at.replace('Z', '+00:00'))
            existing.confidence = float(baseline.confidence)
            existing.dt = date.fromisoformat(baseline.last_recomputed_at[:10])
            return baseline
        else:
            # Create new
            db_baseline = BehaviouralBaseline(
                baseline_id=baseline.baseline_id,
                tenant_id=baseline.tenant_id,
                actor_scope=baseline.actor_scope.value,
                actor_or_group_id=baseline.actor_or_group_id,
                feature_name=baseline.feature_name,
                window=baseline.window,
                mean=float(baseline.mean),
                std_dev=float(baseline.std_dev),
                percentiles=baseline.percentiles,
                last_recomputed_at=datetime.fromisoformat(baseline.last_recomputed_at.replace('Z', '+00:00')),
                confidence=float(baseline.confidence),
                dt=date.fromisoformat(baseline.last_recomputed_at[:10])
            )
            self.session.add(db_baseline)
            return baseline

    def get(
        self,
        tenant_id: str,
        actor_scope: str,
        actor_or_group_id: str,
        feature_name: str
    ) -> Optional[BehaviouralBaseline]:
        """
        Get baseline.

        Args:
            tenant_id: Tenant identifier
            actor_scope: Actor scope
            actor_or_group_id: Actor or group identifier
            feature_name: Feature name

        Returns:
            BehaviouralBaseline or None
        """
        db_baseline = self.session.query(BehaviouralBaseline).filter(
            and_(
                BehaviouralBaseline.tenant_id == tenant_id,
                BehaviouralBaseline.actor_scope == actor_scope,
                BehaviouralBaseline.actor_or_group_id == actor_or_group_id,
                BehaviouralBaseline.feature_name == feature_name
            )
        ).first()
        
        if not db_baseline:
            return None
        
        return self._to_model(db_baseline)

    def _to_model(self, db_baseline: BehaviouralBaseline) -> BehaviouralBaseline:
        """Convert database model to Pydantic model."""
        from ..models import ActorScope
        return BehaviouralBaseline(
            baseline_id=str(db_baseline.baseline_id),
            tenant_id=db_baseline.tenant_id,
            actor_scope=ActorScope(db_baseline.actor_scope),
            actor_or_group_id=db_baseline.actor_or_group_id,
            feature_name=db_baseline.feature_name,
            window=db_baseline.window,
            mean=float(db_baseline.mean),
            std_dev=float(db_baseline.std_dev),
            percentiles=db_baseline.percentiles,
            last_recomputed_at=db_baseline.last_recomputed_at.isoformat(),
            confidence=float(db_baseline.confidence)
        )


class SignalRepository:
    """Repository for BehaviouralSignal operations."""

    def __init__(self, session: Session):
        """
        Initialize signal repository.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def create(self, signal: BehaviouralSignal) -> BehaviouralSignal:
        """
        Create behavioural signal.

        Args:
            signal: BehaviouralSignal to create

        Returns:
            Created BehaviouralSignal
        """
        db_signal = BehaviouralSignal(
            signal_id=signal.signal_id,
            tenant_id=signal.tenant_id,
            actor_scope=signal.actor_scope.value,
            actor_or_group_id=signal.actor_or_group_id,
            dimension=signal.dimension.value,
            signal_type=signal.signal_type.value,
            score=float(signal.score),
            severity=signal.severity.value,
            status=signal.status.value,
            evidence_refs=signal.evidence_refs,
            created_at=datetime.fromisoformat(signal.created_at.replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(signal.updated_at.replace('Z', '+00:00')),
            resolved_at=datetime.fromisoformat(signal.resolved_at.replace('Z', '+00:00')) if signal.resolved_at else None,
            dt=date.fromisoformat(signal.created_at[:10])
        )
        self.session.add(db_signal)
        return signal

    def query(
        self,
        tenant_id: str,
        actor_scope: Optional[str] = None,
        dimensions: Optional[List[str]] = None,
        time_range: Optional[Dict[str, datetime]] = None,
        min_severity: Optional[str] = None,
        signal_types: Optional[List[str]] = None,
        limit: int = 1000
    ) -> List[BehaviouralSignal]:
        """
        Query signals with filters.

        Args:
            tenant_id: Tenant identifier
            actor_scope: Optional actor scope filter
            dimensions: Optional dimensions filter
            time_range: Optional time range (from, to)
            min_severity: Optional minimum severity filter
            signal_types: Optional signal types filter
            limit: Maximum results

        Returns:
            List of BehaviouralSignal
        """
        query = self.session.query(BehaviouralSignal).filter(
            BehaviouralSignal.tenant_id == tenant_id
        )
        
        if actor_scope:
            query = query.filter(BehaviouralSignal.actor_scope == actor_scope)
        
        if dimensions:
            query = query.filter(BehaviouralSignal.dimension.in_(dimensions))
        
        if time_range:
            if "from" in time_range:
                query = query.filter(BehaviouralSignal.created_at >= time_range["from"])
            if "to" in time_range:
                query = query.filter(BehaviouralSignal.created_at <= time_range["to"])
        
        if min_severity:
            severity_order = {"INFO": 1, "WARN": 2, "CRITICAL": 3}
            min_level = severity_order.get(min_severity, 1)
            query = query.filter(
                BehaviouralSignal.severity.in_(
                    [s for s, level in severity_order.items() if level >= min_level]
                )
            )
        
        if signal_types:
            query = query.filter(BehaviouralSignal.signal_type.in_(signal_types))
        
        query = query.order_by(desc(BehaviouralSignal.created_at)).limit(limit)
        
        db_signals = query.all()
        return [self._to_model(s) for s in db_signals]

    def _to_model(self, db_signal: BehaviouralSignal) -> BehaviouralSignal:
        """Convert database model to Pydantic model."""
        from ..models import ActorScope, Dimension, SignalType, Severity, SignalStatus
        return BehaviouralSignal(
            signal_id=str(db_signal.signal_id),
            tenant_id=db_signal.tenant_id,
            actor_scope=ActorScope(db_signal.actor_scope),
            actor_or_group_id=db_signal.actor_or_group_id,
            dimension=Dimension(db_signal.dimension),
            signal_type=SignalType(db_signal.signal_type),
            score=float(db_signal.score),
            severity=Severity(db_signal.severity),
            status=SignalStatus(db_signal.status),
            evidence_refs=db_signal.evidence_refs,
            created_at=db_signal.created_at.isoformat(),
            updated_at=db_signal.updated_at.isoformat(),
            resolved_at=db_signal.resolved_at.isoformat() if db_signal.resolved_at else None
        )


class ConfigRepository:
    """Repository for TenantConfiguration operations."""

    def __init__(self, session: Session):
        """
        Initialize config repository.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def get(self, tenant_id: str) -> Optional[TenantConfiguration]:
        """
        Get tenant configuration.

        Args:
            tenant_id: Tenant identifier

        Returns:
            TenantConfiguration or None
        """
        db_config = self.session.query(TenantConfiguration).filter(
            TenantConfiguration.tenant_id == tenant_id
        ).first()
        
        if not db_config:
            return None
        
        return self._to_model(db_config)

    def create_or_update(self, config: TenantConfiguration) -> TenantConfiguration:
        """
        Create or update tenant configuration.

        Args:
            config: TenantConfiguration to create/update

        Returns:
            Created/updated TenantConfiguration
        """
        existing = self.session.query(TenantConfiguration).filter(
            TenantConfiguration.tenant_id == config.tenant_id
        ).first()
        
        if existing:
            # Update existing
            existing.config_version = config.config_version
            existing.enabled_event_categories = config.enabled_event_categories
            existing.feature_windows = config.feature_windows
            existing.aggregation_thresholds = config.aggregation_thresholds
            existing.enabled_signal_types = config.enabled_signal_types
            existing.privacy_settings = config.privacy_settings
            existing.anomaly_thresholds = config.anomaly_thresholds
            existing.baseline_algorithm = config.baseline_algorithm
            return config
        else:
            # Create new
            db_config = TenantConfiguration(
                tenant_id=config.tenant_id,
                config_version=config.config_version,
                enabled_event_categories=config.enabled_event_categories,
                feature_windows=config.feature_windows,
                aggregation_thresholds=config.aggregation_thresholds,
                enabled_signal_types=config.enabled_signal_types,
                privacy_settings=config.privacy_settings,
                anomaly_thresholds=config.anomaly_thresholds,
                baseline_algorithm=config.baseline_algorithm
            )
            self.session.add(db_config)
            return config

    def _to_model(self, db_config: TenantConfiguration) -> TenantConfiguration:
        """Convert database model to Pydantic model."""
        from ..models import SignalType
        return TenantConfiguration(
            tenant_id=db_config.tenant_id,
            config_version=db_config.config_version,
            enabled_event_categories=db_config.enabled_event_categories,
            feature_windows=db_config.feature_windows,
            aggregation_thresholds=db_config.aggregation_thresholds,
            enabled_signal_types=[SignalType(st) for st in db_config.enabled_signal_types],
            privacy_settings=db_config.privacy_settings,
            anomaly_thresholds=db_config.anomaly_thresholds,
            baseline_algorithm=db_config.baseline_algorithm
        )

