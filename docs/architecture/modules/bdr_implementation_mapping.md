# BDR Backend Requirement Traceability

This document maps each requirement from `Backup_&_Disaster_Recovery_BDR_Module_PRD_v1_1.md` to concrete Python backend components planned for implementation. It ensures coverage across functionality, dependencies, and observability.

## Summary Table

| PRD Section | Requirement Focus | Python Component(s) | Notes |
|-------------|-------------------|---------------------|-------|
| F1 Dataset inventory & classification | Inventory, RPO/RTO references, eligibility flags | `bdr.models.Dataset`, `bdr.policy.InventoryLoader` | Consumes GSMD JSON definitions; enforces classification enums and RPO/RTO references without hard-coding values. |
| F2 Backup plan definition & policy integration | BackupPlan schema, redundancy profiles, validation | `bdr.models.BackupPlan`, `bdr.policy.PlanLoader`, `bdr.service.BDRService.validate_plans` | Plans flow from GSMD; validation cross-checks dataset inventory and emits receipts on errors. |
| F3 Backup execution & storage | Scheduling, execution, catalog, receipts | `bdr.scheduler.BackupScheduler`, `bdr.engine.BackupExecutor`, `bdr.catalog.BackupCatalog`, `bdr.receipts.DecisionReceiptEmitter` | Schedules via policy-driven cron-like expressions; catalog persists run metadata; receipts capture each run result. |
| F4 Restore & recovery workflows | Restore API, cross-dataset consistency, recovery receipts | `bdr.restore.RestoreService`, `bdr.models.RestoreRequest`, `bdr.engine.RestoreExecutor` | Supports in_place, side_by_side, export_only modes with checksum validation and composite restore timestamps. |
| F5 Disaster recovery scenarios & failover | Scenario catalogue, failover orchestration, failback | `bdr.dr.DRScenarioCatalog`, `bdr.dr.FailoverOrchestrator` | Captures scenario metadata, orchestrates failover/failback, records initiators and outcomes. |
| F6 Verification, DR drills, testing | Backup verification, restore tests, DR drills, plan maintenance | `bdr.verification.BackupVerifier`, `bdr.dr.DrillRunner`, `bdr.catalog.PlanMaintenanceTracker` | Verification uses recorded checksums; drills record RPO/RTO actuals and flag stale plans. |
| F7 Observability & reporting | Metrics, logs, receipts | `bdr.observability.MetricsRegistry`, `bdr.receipts.DecisionReceiptEmitter`, structured logging adapters | Metrics exported per plan/dataset; logs include correlation IDs; receipts align with DecisionReceipt schema. |
| F8 Governance & access control | IAM enforcement, approvals, audits | `bdr.security.IAMGuard`, `bdr.security.ApprovalPolicy`, `bdr.audit.AuditTrail` | Guards wrap sensitive operations and emit audit events; supports dual-control hooks. |

## Dependency Alignment

- **GSMD / Policy**: Inventory and plan loaders deserialize GSMD bundles via `bdr.policy`. Validation rejects missing datasets or conflicting RPO/RTO references.
- **Key & Trust Management**: `BackupPlan.encryption_key_ref` is treated as an opaque reference validated by `bdr.security.KeyResolver` without exposing key material.
- **IAM Module**: `bdr.security.IAMGuard` delegates to existing IAM services, ensuring role/scope checks for backup, restore, and DR actions.
- **Decision Receipts**: `bdr.receipts.DecisionReceiptEmitter` produces `backup_run_completed`, `restore_completed`, `dr_event_completed`, and `validation_error` receipts, forwarding to the shared receipts infrastructure.
- **Observability Module**: `bdr.observability.MetricsRegistry` uses the platform metrics exporter (Prometheus-compatible adapter provided by Observability module) and structured logging via the shared logger.

## Verification Approach

- Every PRD functional requirement has a corresponding automated test in `tests/bdr/`, covering success/failure paths, IAM rejections, receipt emission, and metric updates.
- Scenario drills simulate loss-of-service and region outage cases to ensure DR catalogue completeness.
- Coverage enforcement extends to the new `bdr` package via `pytest --cov=bdr --cov-report`.

This mapping is the authoritative traceability aid for the Python BDR backend implementation.

