import pytest

from bdr.catalog import BackupCatalog
from bdr.dr import DRError, DRScenarioCatalog, FailoverOrchestrator
from bdr.models import DRRunbookStep, DRScenario, DRStrategy
from bdr.observability import MetricsRegistry, StructuredLogger
from bdr.receipts import DecisionReceiptEmitter


def _scenario():
    return DRScenario(
        scenario_id="sc1",
        name="Scenario",
        trigger="failure",
        strategy=DRStrategy.BACKUP_AND_RESTORE,
        rpo_target="PT1H",
        rto_target="PT2H",
        runbook=[DRRunbookStep(name="step", description="desc")],
    )


def test_dr_scenario_catalog_errors():
    catalog = DRScenarioCatalog()
    scenario = _scenario()
    catalog.register(scenario)
    with pytest.raises(DRError):
        catalog.register(scenario)
    assert catalog.get("sc1").name == "Scenario"
    assert catalog.list()[0].scenario_id == "sc1"
    with pytest.raises(DRError):
        catalog.get("unknown")


def test_failover_orchestrator_requires_known_scenario():
    scenario_catalog = DRScenarioCatalog()
    metrics = MetricsRegistry()
    logger = StructuredLogger()
    receipts = DecisionReceiptEmitter()
    orchestrator = FailoverOrchestrator(scenario_catalog, metrics, logger, receipts)
    with pytest.raises(DRError):
        orchestrator.execute("missing", initiator="actor", target_env="env")
    with pytest.raises(DRError):
        orchestrator._require_scenario("missing")

