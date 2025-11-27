from datetime import datetime, timedelta

from cloud_services.product_services.mmm_engine.services import MMMService
from cloud_services.product_services.mmm_engine.models import Playbook, PlaybookStatus, MMMContext, ActorType


def build_context() -> MMMContext:
    return MMMContext(
        tenant_id="demo",
        actor_id="alice",
        actor_type=ActorType.HUMAN,
        actor_roles=["developer"],
        repo_id="repo",
        branch="main",
        file_path=None,
        policy_snapshot_id=None,
        quiet_hours=None,
        recent_signals=[{"severity": "high"}],
    )


def test_prioritisation_orders_higher_priority_first(monkeypatch):
    service = MMMService()
    context = build_context()

    high = Playbook(
        playbook_id="pb-high",
        tenant_id="demo",
        version="1",
        name="High Priority",
        status=PlaybookStatus.PUBLISHED,
        triggers=[],
        conditions=[],
        actions=[{"type": "mirror", "payload": {"title": "high"}}],
        limits={"priority": 10},
    )
    low = Playbook(
        playbook_id="pb-low",
        tenant_id="demo",
        version="1",
        name="Low Priority",
        status=PlaybookStatus.PUBLISHED,
        triggers=[],
        conditions=[],
        actions=[{"type": "mirror", "payload": {"title": "low"}}],
        limits={"priority": 1},
    )

    actions = service._evaluate_playbooks(context, [low, high])
    assert actions[0].payload["title"] == "high"


def test_fatigue_blocks_when_exceeding_limits(monkeypatch):
    service = MMMService()
    context = build_context()
    context.quiet_hours = None

    playbook = Playbook(
        playbook_id="pb-fatigue",
        tenant_id="demo",
        version="1",
        name="Fatigue",
        status=PlaybookStatus.PUBLISHED,
        triggers=[],
        conditions=[],
        actions=[{"type": "mirror", "payload": {"title": "fatigue"}}],
        limits={"max_per_actor_per_day": 1, "cooldown_minutes": 1440},
    )

    actions_first = service._evaluate_playbooks(context, [playbook])
    assert actions_first, "first evaluation should return an action"
    actions_second = service._evaluate_playbooks(context, [playbook])
    assert actions_second[0].payload["title"] == "Mirror insight"


def test_quiet_hours_prevents_actions(monkeypatch):
    service = MMMService()
    context = build_context()
    context.quiet_hours = {"start": 0, "end": 23}  # almost whole day

    playbook = Playbook(
        playbook_id="pb-quiet",
        tenant_id="demo",
        version="1",
        name="Quiet Mode",
        status=PlaybookStatus.PUBLISHED,
        triggers=[],
        conditions=[],
        actions=[{"type": "mirror", "payload": {"title": "quiet"}}],
        limits={},
    )

    actions = service._evaluate_playbooks(context, [playbook])
    assert actions[0].payload["title"] == "Mirror insight"


