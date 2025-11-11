# PSCL Pre-Flight Inventory

## Constitution Files
- `docs/constitution/COMMENTS RULES.json` — JSON constitution source with a `constitution_rules` array describing comments-focused policies.
- `docs/constitution/CURSOR TESTING RULES.json` — JSON constitution source whose entries include fields such as `rule_id`, `title`, and `policy_linkage`.
- `docs/constitution/LOGGING & TROUBLESHOOTING RULES.json` — JSON constitution source enumerating logging and troubleshooting rules under `constitution_rules`.
- `docs/constitution/MASTER GENERIC RULES.json` — JSON constitution source holding the master rule set with per-rule metadata in `constitution_rules`.
- `docs/constitution/MODULES AND GSMD MAPPING RULES.json` — JSON constitution source covering module-to-GSMD mappings via the `constitution_rules` array.
- `docs/constitution/TESTING RULES.json` — JSON constitution source listing testing requirements within `constitution_rules`.
- `docs/constitution/VSCODE EXTENSION RULES.json` — JSON constitution source detailing VS Code extension obligations in `constitution_rules`.
- `config/constitution_rules.json` — Consolidated JSON dataset with top-level keys `version`, `statistics`, and `rules` summarising 416 enabled constitution rules.
- `config/constitution_rules.backup.20251106_142615.json` — Backup JSON dataset mirroring constitution statistics such as `total_rules` and per-category descriptions.
- `config/constitution_rules.db` — SQLite database consumed by `ConstitutionRulesDB` for storing rule metadata.
- `config/constitution_config.json` — Configuration file referenced by `ConstitutionRuleManager` to track constitution versioning and defaults.
- `config/constitution/backend_factory.py` — Python module documenting a “Backend Factory for Constitution Rules Database” that instantiates rule managers for SQLite and JSON backends.
- `config/constitution/base_manager.py` — Python module defining the abstract base interface for constitution rule managers.
- `config/constitution/config_manager.py` — Python module titled “Constitution Rule Configuration Manager” providing database-backed rule management.
- `config/constitution/config_manager_json.py` — Python module titled “JSON-based Constitution Rule Configuration Manager” implementing the JSON backend.
- `config/constitution/config_migration.py` — Python module describing migration utilities between SQLite and JSON constitution stores.
- `config/constitution/constitution_rules_json.py` — Python module stating it is the “JSON-based Constitution Rules Database” and loading rules from `docs/constitution`.
- `config/constitution/database.py` — Python module labelled “Constitution Rules Database” supplying SQLite operations.
- `config/constitution/logging_config.py` — Python module providing centralized logging configuration for constitution management.
- `config/constitution/migration.py` — Python module titled “Migration Utilities for Constitution Rules Database”.
- `config/constitution/queries.py` — Python module offering reusable constitution database queries via `ConstitutionQueries`.
- `config/constitution/rule_count_loader.py` — Python module asserting it is the single source for rule counts from `docs/constitution` JSON files.
- `config/constitution/rule_extractor.py` — Python module describing extraction and categorization of constitution rules from master sources.
- `config/constitution/sync_manager.py` — Python module detailing synchronization between SQLite and JSON constitution backends.
- `config/constitution/__init__.py` — Package initializer summarizing the constitution rule management exports and version metadata.
- `config/migration_history.json` — JSON log referenced by constitution sync tooling to track migration history.
- `config/sync_history.json` — JSON log referenced by `ConstitutionSyncManager` to record sync operations.

## Storage Path Resolver (Planes / IDE)
- `src/edge-agent/shared/storage/StoragePathResolver.ts` — TypeScript resolver enforcing ZU_ROOT-based path construction for `ide`, `tenant`, `product`, and `shared` planes with validation helpers.
- `src/vscode-extension/shared/storage/StoragePathResolver.ts` — VS Code extension variant that loads ZU_ROOT via environment or `zeroui.zuRoot` setting and normalizes IDE receipt paths (e.g., `receipts/{repo}/{yyyy}/{mm}`).
- `src/edge-agent/shared/storage/__tests__/StoragePathResolver.test.ts` — Test suite verifying IDE plane resolution, policy cache paths, and validation expectations.
- `src/edge-agent/shared/storage/README.md` — Markdown describing plane-specific storage locations (e.g., “ide/policy/ cache, product/policy/registry/ authoritative releases”).

## Local Policy Cache / Reader
- `src/edge-agent/shared/storage/PolicyStorageService.ts` — TypeScript service that caches signed snapshots under `ide/policy/`, reads current pointers, and assembles `policy_version_ids` plus combined `sha256` hashes.
- `src/edge-agent/shared/storage/__tests__/PolicyStorageService.test.ts` — Jest tests covering caching, current-version tracking, and signature requirements for the policy storage service.
- `src/edge-agent/shared/storage/README.md` — Documentation noting IDE plane policy cache behaviour and product plane registry paths.

## Receipt Generator (Append-Only JSONL)
- `src/edge-agent/shared/storage/ReceiptGenerator.ts` — TypeScript generator emitting signed decision and feedback receipts before storage.
- `src/edge-agent/shared/storage/ReceiptStorageService.ts` — TypeScript writer append-only appending receipts to `receipts.jsonl` via `fs.createWriteStream(..., { flags: 'a' })` while enforcing signature and PII checks.
- `src/edge-agent/shared/storage/__tests__/ReceiptStorageService.test.ts` — Test suite validating append-only behaviour, signature enforcement, and no-PII checks for receipt storage.
- `src/vscode-extension/shared/storage/ReceiptGenerator.ts` — VS Code extension generator producing receipts with deterministic `sig-{sha256}` signatures for tests.
- `src/vscode-extension/shared/storage/ReceiptStorageReader.ts` — VS Code extension reader that loads JSONL receipts, reuses `StoragePathResolver`, and re-validates signatures.

## Schema Registry References
- `gsmd/schema/feedback_receipt.schema.json` — JSON Schema (draft 2020-12) for GSMD feedback receipts with fields such as `decision_receipt_id`.
- `gsmd/schema/override.schema.json` — JSON Schema defining override payload structure.
- `gsmd/schema/receipt.schema.json` — JSON Schema titled “GSMD Decision Receipt (v1 minimal)” with enums for `decision` and pattern checks for `policy_snapshot_hash`.
- `gsmd/schema/snapshot.schema.json` — JSON Schema describing policy snapshot structure (e.g., `version`, `policy_snapshot_hash`).
- `contracts/analytics_and_reporting/schemas/` (`decision_response.schema.json`, `envelope.schema.json`, `evidence_link.schema.json`, `feedback_receipt.schema.json`, `receipt.schema.json`) — Module schema placeholders each declaring `$schema: https://json-schema.org/draft/2020-12/schema`.
- `contracts/client_admin_dashboard/schemas/` (`decision_response.schema.json`, `envelope.schema.json`, `evidence_link.schema.json`, `feedback_receipt.schema.json`, `receipt.schema.json`) — Same schema set for client admin dashboard contracts.
- `contracts/compliance_and_security_challenges/schemas/` (`decision_response.schema.json`, `envelope.schema.json`, `evidence_link.schema.json`, `feedback_receipt.schema.json`, `receipt.schema.json`) — Same schema definitions for compliance and security challenges.
- `contracts/cross_cutting_concern_services/schemas/` (same five schema files) — Cross-cutting concern service schema placeholders.
- `contracts/detection_engine_core/schemas/` (same five schema files) — Detection engine core schema placeholders.
- `contracts/feature_development_blind_spots/schemas/` (same five schema files) — Schema placeholders for feature development blind spots.
- `contracts/gold_standards/schemas/` (same five schema files) — Schema placeholders for gold standards contracts.
- `contracts/integration_adaptors/schemas/` (same five schema files) — Schema placeholders for integration adapters.
- `contracts/knowledge_integrity_and_discovery/schemas/` (same five schema files) — Schema placeholders for knowledge integrity and discovery.
- `contracts/knowledge_silo_prevention/schemas/` (same five schema files) — Schema placeholders for knowledge silo prevention.
- `contracts/legacy_systems_safety/schemas/` (same five schema files) — Schema placeholders for legacy systems safety.
- `contracts/merge_conflicts_and_delays/schemas/` (same five schema files) — Schema placeholders for merge conflicts and delays.
- `contracts/mmm_engine/schemas/` (same five schema files) — Schema placeholders for MMM engine.
- `contracts/monitoring_and_observability_gaps/schemas/` (same five schema files) — Schema placeholders for monitoring and observability gaps.
- `contracts/product_success_monitoring/schemas/` (same five schema files) — Schema placeholders for product success monitoring.
- `contracts/qa_and_testing_deficiencies/schemas/` (same five schema files) — Schema placeholders for QA and testing deficiencies.
- `contracts/release_failures_and_rollbacks/schemas/` (same five schema files) — Schema placeholders for release failures and rollbacks.
- `contracts/roi_dashboard/schemas/` (same five schema files) — Schema placeholders for ROI dashboard.
- `contracts/signal_ingestion_and_normalization/schemas/` (same five schema files) — Schema placeholders for signal ingestion and normalization.
- `contracts/technical_debt_accumulation/schemas/` (same five schema files) — Schema placeholders for technical debt accumulation.
- `contracts/schemas/decision-receipt.schema.json` — Shared schema describing decision receipt structure with fields like `policy_snapshot_hash`.
- `contracts/schemas/feedback-receipt.schema.json` — Shared schema describing feedback receipt structure.
- `contracts/schemas/policy-snapshot.schema.json` — Shared schema for policy snapshot payloads.
- `docs/architecture/receipt-schema-cross-reference.md` — Document mapping GSMD, TypeScript, and contract schema fields side-by-side.
- `docs/architecture/openapi/policy-service.openapi.yaml` — OpenAPI specification for the policy-service, referencing policy snapshot schema distribution endpoints.

## VS Code Extension Activation Entry
- `src/vscode-extension/extension.ts` — Activation module exporting `activate(context: vscode.ExtensionContext)` and initializing managers, command registrations, and the `ConstitutionValidator`.
- `src/vscode-extension/package.json` — Extension manifest defining the activation entry point `"main": "./dist/extension.js"` and command contributions.
- `src/vscode-extension/out/` — Compiled output corresponding to the activation entry (TypeScript transpiled artifacts).

## Existing Tests & Test Runner
- `tests/` — Python test suite containing modules such as `test_constitution_all_files.py`, `test_cursor_testing_rules.py`, `test_pre_implementation_artifacts.py`, and related coverage documentation.
- `tests/README.md` — Test documentation referencing pytest usage and a comprehensive `run_all_tests.py` workflow.
- `tests/contracts` subdirectories (e.g., `tests/contracts/gold_standards`, `tests/contracts/feature_development_blind_spots`) — Contract validation tests pairing Spectral YAML rules with `validate_examples.py`.
- `tests/test_constitution_comprehensive_runner.py` — Python module exposing a `run_all_tests` helper invoked by the suite.
- `src/edge-agent/__tests__/EdgeAgent.test.ts` — Jest test suite covering EdgeAgent behaviour, receipts, and policy interactions.
- `src/edge-agent/__tests__/integration/receipt-flow.test.ts` — Integration tests asserting append-only receipt flow.
- `src/vscode-extension/test/runTest.ts` — VS Code integration test bootstrap invoking `@vscode/test-electron`.
- `src/vscode-extension/test/suite/index.ts` — Extension test suite entry imported by `runTest.ts`.
- `jest.config.js` — Jest configuration referenced by `npm run test:storage`.
- `package.json` — Root script definitions for `pytest`, `jest`, and `python run_all_tests.py`.
- `tests/run_all_tests.py` — **MISSING** (referenced in `package.json` and `tests/README.md`, but no file present in repository scan).

