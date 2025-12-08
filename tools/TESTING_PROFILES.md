# ZeroUI Test Runner & Profiles

This document describes the ZeroUI pytest runner (`tools/run_tests.py`) and the named test profiles in `tools/test_profiles.yaml`. Tests remain standard pytest suites; the runner is a convenience layer for common selections and defaults.

## Usage
- Smoke profile: `python tools/run_tests.py smoke`
- Root validators: `python tools/run_tests.py root_validators`
- Module alerting: `python tools/run_tests.py module_alerting`
- Full suite: `python tools/run_tests.py full`
- Pass extra pytest flags: `python tools/run_tests.py full -- -vv`

## Profiles
- **smoke**: Fast local checks; runs core root-level validator tests plus documented root-level suites from `tests/ROOT_TESTS_ORGANIZATION.md`.
- **root_validators**: Constitution/validator-focused tests in root (e.g., `tests/test_constitution_*.py` and `tests/test_cursor_testing_rules.py`); good for validator-only iterations.
- **module_alerting**: Alerting Notification Service tests under `tests/cloud_services/shared_services/alerting_notification_service`; use for module-specific work.
- **full**: Entire pytest suite (CI-oriented).

## Notes
- The runner sets a fixed `PYTHONHASHSEED` for determinism and tags runs with `ZEROUI_TEST_PROFILE`.
- `ZEROUI_TEST_MODULE_FILTER` can be set to narrow module setup for optimizations; leaving it unset preserves the default behavior.

