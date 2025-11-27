"""
Feature Computation Service for UBI Module (EPC-9).

What: Computes behavioural features from events over configurable windows
Why: Generate features for baseline computation and anomaly detection per PRD FR-2
Reads/Writes: Feature computation and storage
Contracts: UBI PRD FR-2, NFR-2 (Performance SLOs)
Risks: Performance issues, computation errors
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..models import BehaviouralFeature, ActorScope, Dimension
from .definitions import get_feature_definitions

logger = logging.getLogger(__name__)


class FeatureComputationService:
    """
    Feature computation service.

    Per UBI PRD FR-2:
    - Compute features over configurable windows (24h, 7d, 28d)
    - Actor-level and team-level aggregation
    - Performance: p95 < 1 minute for 24-hour window features
    """

    def __init__(self):
        """Initialize feature computation service."""
        self.feature_definitions = get_feature_definitions()

    def compute_feature(
        self,
        tenant_id: str,
        actor_scope: ActorScope,
        actor_or_group_id: str,
        feature_name: str,
        window_start: datetime,
        window_end: datetime,
        events: List[Dict[str, Any]]
    ) -> Optional[BehaviouralFeature]:
        """
        Compute feature from events.

        Args:
            tenant_id: Tenant identifier
            actor_scope: Actor scope
            actor_or_group_id: Actor or group identifier
            feature_name: Feature name
            window_start: Window start timestamp
            window_end: Window end timestamp
            events: List of events in window

        Returns:
            BehaviouralFeature or None if computation fails
        """
        try:
            feature_def = self.feature_definitions.get(feature_name)
            if not feature_def:
                logger.error(f"Unknown feature: {feature_name}")
                return None
            
            # Compute feature value based on aggregation type
            value = self._compute_value(feature_name, feature_def, events)
            
            # Determine dimension from feature category
            dimension = self._get_dimension_from_category(feature_def["category"])
            
            # Create feature
            return BehaviouralFeature(
                feature_id=f"{tenant_id}:{actor_or_group_id}:{feature_name}:{window_end.isoformat()}",
                tenant_id=tenant_id,
                actor_scope=actor_scope,
                actor_or_group_id=actor_or_group_id,
                feature_name=feature_name,
                window_start=window_start.isoformat(),
                window_end=window_end.isoformat(),
                value=value,
                dimension=dimension,
                confidence=1.0,  # Placeholder - will be computed based on data quality
                metadata={"computation_method": feature_def["aggregation"]}
            )
        except Exception as e:
            logger.error(f"Error computing feature {feature_name}: {e}", exc_info=True)
            return None

    def _compute_value(
        self,
        feature_name: str,
        feature_def: Dict[str, Any],
        events: List[Dict[str, Any]]
    ) -> float:
        """
        Compute feature value.

        Args:
            feature_name: Feature name
            feature_def: Feature definition
            events: List of events

        Returns:
            Feature value
        """
        aggregation = feature_def["aggregation"]
        
        if aggregation == "sum":
            return float(len(events))
        elif aggregation == "count":
            return float(len(events))
        elif aggregation == "mean":
            # Placeholder - would compute mean of event values
            return float(len(events)) / max(1, len(events))
        elif aggregation == "count_distinct":
            # Placeholder - would count distinct values
            return float(len(set(str(e) for e in events)))
        else:
            return 0.0

    def _get_dimension_from_category(self, category: str) -> Dimension:
        """
        Map feature category to dimension.

        Args:
            category: Feature category

        Returns:
            Dimension enum value
        """
        category_map = {
            "activity": Dimension.ACTIVITY,
            "flow": Dimension.FLOW,
            "collaboration": Dimension.COLLABORATION,
            "agent_usage": Dimension.AGENT_SYNERGY
        }
        return category_map.get(category, Dimension.ACTIVITY)

