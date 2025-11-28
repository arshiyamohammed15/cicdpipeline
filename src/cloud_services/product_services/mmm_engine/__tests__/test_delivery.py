from dataclasses import dataclass
from typing import Dict, List

from cloud_services.product_services.mmm_engine.delivery import DeliveryOrchestrator
from cloud_services.product_services.mmm_engine.integrations.downstream_clients import (
    EdgeAgentClient,
    CIWorkflowClient,
    AlertingClient,
)
from cloud_services.product_services.mmm_engine.models import (
    MMMDecision,
    MMMAction,
    MMMContext,
    ActorType,
    ActionType,
    Surface,
)


@dataclass
class StubClient:
    name: str
    calls: List[Dict]

    def send_action(self, payload: Dict) -> bool:
        self.calls.append(payload)
        return True


def build_decision() -> MMMDecision:
    context = MMMContext(
        tenant_id="demo",
        actor_id="alice",
        actor_type=ActorType.HUMAN,
        actor_roles=["dev"],
        repo_id="repo",
        branch="main",
        file_path=None,
        policy_snapshot_id=None,
        quiet_hours=None,
        recent_signals=[],
    )
    action = MMMAction(
        action_id="a1",
        type=ActionType.MIRROR,
        surfaces=[Surface.IDE, Surface.CI, Surface.ALERT],
        payload={"title": "hello"},
    )
    return MMMDecision(
        decision_id="d1",
        tenant_id="demo",
        actor_id="alice",
        actor_type=ActorType.HUMAN,
        context=context,
        actions=[action],
        policy_snapshot_id="demo-snapshot-default",
    )


def test_delivery_orchestrator_routes_to_all_surfaces(monkeypatch):
    edge = StubClient("edge", [])
    ci = StubClient("ci", [])
    alert = StubClient("alert", [])

    orchestrator = DeliveryOrchestrator(edge, ci, alert)  # type: ignore[arg-type]
    decision = build_decision()

    results = orchestrator.deliver(decision)

    assert edge.calls and ci.calls and alert.calls
    assert results == {"ide": [True], "ci": [True], "alert": [True]}


def test_delivery_orchestrator_handles_partial_surfaces():
    edge = StubClient("edge", [])
    ci = StubClient("ci", [])
    alert = StubClient("alert", [])

    orchestrator = DeliveryOrchestrator(edge, ci, alert)  # type: ignore[arg-type]
    decision = build_decision()
    decision.actions[0].surfaces = [Surface.IDE]

    results = orchestrator.deliver(decision)

    assert len(edge.calls) == 1
    assert not ci.calls and not alert.calls
    assert results == {"ide": [True], "ci": [], "alert": []}


