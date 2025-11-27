"""
Signal Generation Service for UBI Module (EPC-9).

What: Generates BehaviouralSignals from features and baselines
Why: Provide risk/opportunity signals for downstream consumers per PRD FR-5, FR-6, FR-7
Reads/Writes: Signal generation and storage
Contracts: UBI PRD FR-5, FR-6, FR-7, Section 10.4
Risks: Signal generation errors, evidence linking failures
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from ..models import (
    BehaviouralSignal, SignalType, Severity, SignalStatus,
    ActorScope, Dimension
)

logger = logging.getLogger(__name__)


class SignalGenerationService:
    """
    Signal generation service.

    Per UBI PRD FR-5, FR-6, FR-7:
    - Score computation (0-100 normalized) per dimension
    - Signal type classification: risk, opportunity, informational
    - Evidence linking (ERIS evidence handles or embedded summaries)
    """

    def generate_signal(
        self,
        tenant_id: str,
        actor_scope: ActorScope,
        actor_or_group_id: str,
        dimension: Dimension,
        signal_type: SignalType,
        score: float,
        severity: Severity,
        evidence_refs: List[Dict[str, Any]],
        feature_snapshot: Optional[Dict[str, Any]] = None
    ) -> BehaviouralSignal:
        """
        Generate behavioural signal.

        Args:
            tenant_id: Tenant identifier
            actor_scope: Actor scope
            actor_or_group_id: Actor or group identifier
            dimension: Dimension
            signal_type: Signal type
            score: Normalized score (0-100)
            severity: Severity level
            evidence_refs: Evidence references
            feature_snapshot: Snapshot of relevant features (optional)

        Returns:
            BehaviouralSignal
        """
        signal_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        # Add feature snapshot to evidence if provided
        if feature_snapshot and len(str(feature_snapshot)) < 1024:  # < 1KB
            evidence_refs.append({
                "type": "feature_snapshot",
                "data": feature_snapshot
            })
        
        return BehaviouralSignal(
            signal_id=signal_id,
            tenant_id=tenant_id,
            actor_scope=actor_scope,
            actor_or_group_id=actor_or_group_id,
            dimension=dimension,
            signal_type=signal_type,
            score=max(0.0, min(100.0, score)),  # Clamp to 0-100
            severity=severity,
            status=SignalStatus.ACTIVE,
            evidence_refs=evidence_refs,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            resolved_at=None
        )

