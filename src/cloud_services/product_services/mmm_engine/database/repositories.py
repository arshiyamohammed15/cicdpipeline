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
    ActorPreferencesModel,
    TenantPolicyModel,
    DualChannelApprovalModel,
)
from ..models import (
    Playbook,
    MMMDecision,
    MMMAction,
    MMMOutcome,
    PlaybookStatus,
    ActorPreferences,
    TenantMMMPolicy,
    DualChannelApproval,
    DualChannelApprovalStatus,
)

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


class ActorPreferencesRepository:
    """Repository for actor preferences (FR-14)."""

    def __init__(self, session: Session):
        self.session = session

    def get_preferences(
        self, tenant_id: str, actor_id: str
    ) -> Optional[ActorPreferences]:
        model = (
            self.session.query(ActorPreferencesModel)
            .filter(
                ActorPreferencesModel.tenant_id == tenant_id,
                ActorPreferencesModel.actor_id == actor_id,
            )
            .first()
        )
        return self._to_schema(model) if model else None

    def save_preferences(self, preferences: ActorPreferences) -> ActorPreferences:
        model = ActorPreferencesModel(
            preference_id=preferences.preference_id,
            tenant_id=preferences.tenant_id,
            actor_id=preferences.actor_id,
            opt_out_categories=preferences.opt_out_categories,
            snooze_until=preferences.snooze_until,
            preferred_surfaces=preferences.preferred_surfaces,
        )
        self.session.merge(model)
        return self._to_schema(model)

    def update_preferences(
        self, tenant_id: str, actor_id: str, updates: dict
    ) -> Optional[ActorPreferences]:
        model = (
            self.session.query(ActorPreferencesModel)
            .filter(
                ActorPreferencesModel.tenant_id == tenant_id,
                ActorPreferencesModel.actor_id == actor_id,
            )
            .first()
        )
        if not model:
            return None
        for key, value in updates.items():
            if hasattr(model, key):
                setattr(model, key, value)
        return self._to_schema(model)

    @staticmethod
    def _to_schema(model: ActorPreferencesModel | None) -> Optional[ActorPreferences]:
        if not model:
            return None
        return ActorPreferences(
            preference_id=str(model.preference_id),
            tenant_id=model.tenant_id,
            actor_id=model.actor_id,
            opt_out_categories=model.opt_out_categories or [],
            snooze_until=model.snooze_until,
            preferred_surfaces=model.preferred_surfaces or [],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class TenantPolicyRepository:
    """Repository for tenant MMM policies (FR-13)."""

    def __init__(self, session: Session):
        self.session = session

    def get_policy(self, tenant_id: str) -> Optional[TenantMMMPolicy]:
        model = (
            self.session.query(TenantPolicyModel)
            .filter(TenantPolicyModel.tenant_id == tenant_id)
            .first()
        )
        return self._to_schema(model) if model else None

    def save_policy(self, policy: TenantMMMPolicy) -> TenantMMMPolicy:
        model = TenantPolicyModel(
            policy_id=policy.policy_id,
            tenant_id=policy.tenant_id,
            enabled_surfaces=policy.enabled_surfaces,
            quotas=policy.quotas,
            quiet_hours=policy.quiet_hours,
            enabled_action_types=policy.enabled_action_types,
        )
        self.session.merge(model)
        return self._to_schema(model)

    def update_policy(
        self, tenant_id: str, updates: dict
    ) -> Optional[TenantMMMPolicy]:
        model = (
            self.session.query(TenantPolicyModel)
            .filter(TenantPolicyModel.tenant_id == tenant_id)
            .first()
        )
        if not model:
            return None
        for key, value in updates.items():
            if hasattr(model, key):
                setattr(model, key, value)
        return self._to_schema(model)

    @staticmethod
    def _to_schema(model: TenantPolicyModel | None) -> Optional[TenantMMMPolicy]:
        if not model:
            return None
        return TenantMMMPolicy(
            policy_id=str(model.policy_id),
            tenant_id=model.tenant_id,
            enabled_surfaces=model.enabled_surfaces or ["ide", "ci", "alert"],
            quotas=model.quotas or {"max_actions_per_day": 10, "max_actions_per_hour": 3},
            quiet_hours=model.quiet_hours or {"start": 22, "end": 6},
            enabled_action_types=model.enabled_action_types
            or ["mirror", "mentor", "multiplier"],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class DualChannelApprovalRepository:
    """Repository for dual-channel approvals (FR-6)."""

    def __init__(self, session: Session):
        self.session = session

    def get_approval(self, action_id: str) -> Optional[DualChannelApproval]:
        import uuid
        model = (
            self.session.query(DualChannelApprovalModel)
            .filter(DualChannelApprovalModel.action_id == uuid.UUID(action_id))
            .first()
        )
        return self._to_schema(model) if model else None

    def create_approval(self, approval: DualChannelApproval) -> DualChannelApproval:
        import uuid
        model = DualChannelApprovalModel(
            approval_id=uuid.UUID(approval.approval_id),
            action_id=uuid.UUID(approval.action_id),
            decision_id=uuid.UUID(approval.decision_id),
            actor_id=approval.actor_id,
            approver_id=approval.approver_id,
            first_approval_at=approval.first_approval_at,
            second_approval_at=approval.second_approval_at,
            status=approval.status.value,
        )
        self.session.add(model)
        return self._to_schema(model)

    def record_first_approval(
        self, action_id: str, actor_id: str
    ) -> Optional[DualChannelApproval]:
        import uuid
        from datetime import datetime
        model = (
            self.session.query(DualChannelApprovalModel)
            .filter(DualChannelApprovalModel.action_id == uuid.UUID(action_id))
            .first()
        )
        if not model:
            return None
        model.first_approval_at = datetime.utcnow()
        model.status = DualChannelApprovalStatus.FIRST_APPROVED.value
        return self._to_schema(model)

    def record_second_approval(
        self, action_id: str, approver_id: str
    ) -> Optional[DualChannelApproval]:
        import uuid
        from datetime import datetime
        model = (
            self.session.query(DualChannelApprovalModel)
            .filter(DualChannelApprovalModel.action_id == uuid.UUID(action_id))
            .first()
        )
        if not model:
            return None
        model.approver_id = approver_id
        model.second_approval_at = datetime.utcnow()
        model.status = DualChannelApprovalStatus.FULLY_APPROVED.value
        return self._to_schema(model)

    def reject_approval(self, action_id: str) -> Optional[DualChannelApproval]:
        import uuid
        model = (
            self.session.query(DualChannelApprovalModel)
            .filter(DualChannelApprovalModel.action_id == uuid.UUID(action_id))
            .first()
        )
        if not model:
            return None
        model.status = DualChannelApprovalStatus.REJECTED.value
        return self._to_schema(model)

    @staticmethod
    def _to_schema(
        model: DualChannelApprovalModel | None,
    ) -> Optional[DualChannelApproval]:
        if not model:
            return None
        return DualChannelApproval(
            approval_id=str(model.approval_id),
            action_id=str(model.action_id),
            decision_id=str(model.decision_id),
            actor_id=model.actor_id,
            approver_id=model.approver_id,
            first_approval_at=model.first_approval_at,
            second_approval_at=model.second_approval_at,
            status=DualChannelApprovalStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class ExperimentRepository:
    """Repository for experiments (FR-13)."""

    def __init__(self, session: Session):
        self.session = session

    def list_experiments(
        self, tenant_id: str, status: Optional[str] = None
    ) -> List[dict]:
        query = self.session.query(ExperimentModel).filter(
            ExperimentModel.tenant_id == tenant_id
        )
        if status:
            query = query.filter(ExperimentModel.status == status)
        models = query.all()
        return [{"experiment_id": str(m.experiment_id), "name": m.name, "status": m.status, "config": m.config} for m in models]

    def get_experiment(
        self, tenant_id: str, experiment_id: str
    ) -> Optional[dict]:
        import uuid
        model = (
            self.session.query(ExperimentModel)
            .filter(
                ExperimentModel.tenant_id == tenant_id,
                ExperimentModel.experiment_id == uuid.UUID(experiment_id),
            )
            .first()
        )
        if not model:
            return None
        return {
            "experiment_id": str(model.experiment_id),
            "tenant_id": model.tenant_id,
            "name": model.name,
            "status": model.status,
            "config": model.config,
            "created_at": model.created_at,
        }

    def save_experiment(self, experiment: dict) -> dict:
        import uuid
        model = ExperimentModel(
            experiment_id=uuid.UUID(experiment.get("experiment_id", str(uuid.uuid4()))),
            tenant_id=experiment["tenant_id"],
            name=experiment["name"],
            status=experiment.get("status", "draft"),
            config=experiment.get("config", {}),
        )
        self.session.add(model)
        return {
            "experiment_id": str(model.experiment_id),
            "tenant_id": model.tenant_id,
            "name": model.name,
            "status": model.status,
            "config": model.config,
            "created_at": model.created_at,
        }

    def update_experiment(
        self, tenant_id: str, experiment_id: str, updates: dict
    ) -> Optional[dict]:
        import uuid
        model = (
            self.session.query(ExperimentModel)
            .filter(
                ExperimentModel.tenant_id == tenant_id,
                ExperimentModel.experiment_id == uuid.UUID(experiment_id),
            )
            .first()
        )
        if not model:
            return None
        for key, value in updates.items():
            if hasattr(model, key):
                setattr(model, key, value)
        return {
            "experiment_id": str(model.experiment_id),
            "tenant_id": model.tenant_id,
            "name": model.name,
            "status": model.status,
            "config": model.config,
            "created_at": model.created_at,
        }

    def activate_experiment(
        self, tenant_id: str, experiment_id: str
    ) -> Optional[dict]:
        return self.update_experiment(tenant_id, experiment_id, {"status": "active"})

    def deactivate_experiment(
        self, tenant_id: str, experiment_id: str
    ) -> Optional[dict]:
        return self.update_experiment(tenant_id, experiment_id, {"status": "inactive"})


