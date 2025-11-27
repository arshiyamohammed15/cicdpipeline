"""
Repository layer for MMM Engine database access.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from .models import (
    PlaybookModel,
    DecisionModel,
    ActionModel,
    OutcomeModel,
    ExperimentModel,
)
from ..models import Playbook, MMMDecision, MMMAction, MMMOutcome, PlaybookStatus

logger = logging.getLogger(__name__)


class PlaybookRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_playbooks(self, tenant_id: str) -> List[Playbook]:
        models = (
            self.session.query(PlaybookModel)
            .filter(PlaybookModel.tenant_id == tenant_id)
            .order_by(PlaybookModel.created_at.desc())
            .all()
        )
        return [self._to_schema(m) for m in models]

    def get(self, tenant_id: str, playbook_id: str) -> Optional[Playbook]:
        model = (
            self.session.query(PlaybookModel)
            .filter(
                PlaybookModel.tenant_id == tenant_id,
                PlaybookModel.playbook_id == playbook_id,
            )
            .first()
        )
        return self._to_schema(model) if model else None

    def save(self, playbook: Playbook) -> Playbook:
        db_model = PlaybookModel(
            playbook_id=playbook.playbook_id,
            tenant_id=playbook.tenant_id,
            version=playbook.version,
            name=playbook.name,
            status=playbook.status.value,
            description=None,
            triggers=playbook.triggers,
            conditions=playbook.conditions,
            actions=playbook.actions,
            limits=playbook.limits,
        )
        self.session.add(db_model)
        return self._to_schema(db_model)

    def publish(self, tenant_id: str, playbook_id: str) -> Optional[Playbook]:
        model = (
            self.session.query(PlaybookModel)
            .filter(
                PlaybookModel.tenant_id == tenant_id,
                PlaybookModel.playbook_id == playbook_id,
            )
            .first()
        )
        if not model:
            return None
        model.status = "published"
        return self._to_schema(model)

    @staticmethod
    def _to_schema(model: PlaybookModel | None) -> Optional[Playbook]:
        if not model:
            return None
        return Playbook(
            playbook_id=str(model.playbook_id),
            tenant_id=model.tenant_id,
            version=model.version,
            name=model.name,
            status=PlaybookStatus(model.status),
            triggers=model.triggers,
            conditions=model.conditions,
            actions=model.actions,
            limits=model.limits,
        )


class DecisionRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_decision(self, decision: MMMDecision) -> DecisionModel:
        db_decision = DecisionModel(
            decision_id=decision.decision_id,
            tenant_id=decision.tenant_id,
            actor_id=decision.actor_id,
            actor_type=decision.actor_type.value,
            context=decision.context.dict(),
            signal_reference={},  # placeholder
            policy_snapshot_id=decision.policy_snapshot_id,
        )
        self.session.add(db_decision)
        for action in decision.actions:
            db_action = ActionModel(
                action_id=action.action_id,
                decision=db_decision,
                type=action.type.value,
                surfaces=[s.value for s in action.surfaces],
                payload=action.payload,
                requires_consent=action.requires_consent,
                requires_dual_channel=action.requires_dual_channel,
            )
            self.session.add(db_action)
        return db_decision


class OutcomeRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_outcome(self, outcome: MMMOutcome) -> OutcomeModel:
        db_outcome = OutcomeModel(
            decision_id=outcome.decision_id,
            action_id=outcome.action_id,
            actor_id=outcome.actor_id,
            result=outcome.result,
            reason=outcome.reason,
            metadata_json={},
        )
        self.session.add(db_outcome)
        return db_outcome


