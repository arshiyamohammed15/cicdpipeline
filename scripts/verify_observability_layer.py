#!/usr/bin/env python3
"""
ZeroUI Observability Layer - Triple Verification Script

Systematically verifies all OBS-00 through OBS-18 tasks against requirements.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

VERIFICATION_RESULTS: Dict[str, Dict[str, any]] = {}


def verify_file_exists(file_path: Path, task_id: str, check_name: str) -> Tuple[bool, str]:
    """Verify file exists."""
    if file_path.exists():
        VERIFICATION_RESULTS.setdefault(task_id, {})[check_name] = "[PASS]"
        return True, f"[PASS] {check_name}: File exists"
    else:
        VERIFICATION_RESULTS.setdefault(task_id, {})[check_name] = "[FAIL]"
        return False, f"[FAIL] {check_name}: File missing: {file_path}"


def verify_json_schema(file_path: Path, task_id: str, check_name: str, required_fields: List[str]) -> Tuple[bool, str]:
    """Verify JSON schema has required fields."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        missing = []
        for field in required_fields:
            if field not in schema.get('required', []):
                missing.append(field)
        
        if missing:
            VERIFICATION_RESULTS.setdefault(task_id, {})[check_name] = f"[FAIL] Missing fields: {missing}"
            return False, f"[FAIL] {check_name}: Missing required fields: {missing}"
        else:
            VERIFICATION_RESULTS.setdefault(task_id, {})[check_name] = "[PASS]"
            return True, f"[PASS] {check_name}: All required fields present"
    except Exception as e:
        VERIFICATION_RESULTS.setdefault(task_id, {})[check_name] = f"[FAIL] {str(e)}"
        return False, f"[FAIL] {check_name}: Error reading file: {e}"


def verify_enum_values(file_path: Path, task_id: str, check_name: str, field_path: List[str], expected_values: List[str]) -> Tuple[bool, str]:
    """Verify enum values in JSON schema."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        # Navigate to field
        current = schema
        for part in field_path:
            current = current.get('properties', {}).get(part, {})
        
        enum_values = current.get('enum', [])
        if set(enum_values) == set(expected_values):
            VERIFICATION_RESULTS.setdefault(task_id, {})[check_name] = "[PASS]"
            return True, f"[PASS] {check_name}: Enum values match"
        else:
            VERIFICATION_RESULTS.setdefault(task_id, {})[check_name] = f"[FAIL] Expected {expected_values}, got {enum_values}"
            return False, f"[FAIL] {check_name}: Enum mismatch. Expected {expected_values}, got {enum_values}"
    except Exception as e:
        VERIFICATION_RESULTS.setdefault(task_id, {})[check_name] = f"[FAIL] {str(e)}"
        return False, f"[FAIL] {check_name}: Error: {e}"


def verify_phase0():
    """Verify Phase 0 tasks (OBS-00 through OBS-03)."""
    print("\n=== Phase 0 Verification (OBS-00 through OBS-03) ===\n")
    
    obs_root = PROJECT_ROOT / "src/shared_libs/zeroui_observability"
    
    # OBS-00: Telemetry Envelope and 12 Event Types
    print("OBS-00: Telemetry Envelope and 12 Event Types")
    envelope_schema = obs_root / "contracts/envelope_schema.json"
    verify_file_exists(envelope_schema, "OBS-00", "envelope_schema_exists")
    
    verify_json_schema(
        envelope_schema, "OBS-00", "required_fields",
        ["event_id", "event_time", "event_type", "severity", "source", "correlation", "payload"]
    )
    
    verify_enum_values(
        envelope_schema, "OBS-00", "severity_enum",
        ["severity"], ["debug", "info", "warn", "error", "critical"]
    )
    
    verify_enum_values(
        envelope_schema, "OBS-00", "channel_enum",
        ["source", "channel"], ["ide", "edge_agent", "backend", "ci", "other"]
    )
    
    # Verify schema ID
    with open(envelope_schema, 'r') as f:
        schema = json.load(f)
        if schema.get('$id') == 'zero_ui.obsv.event.v1':
            VERIFICATION_RESULTS.setdefault("OBS-00", {})["schema_id"] = "[PASS]"
            print("  [PASS] Schema ID is zero_ui.obsv.event.v1")
        else:
            VERIFICATION_RESULTS.setdefault("OBS-00", {})["schema_id"] = "[FAIL]"
            print(f"  [FAIL] Schema ID mismatch: {schema.get('$id')}")
    
    # Verify event types
    event_types_file = obs_root / "contracts/event_types.py"
    verify_file_exists(event_types_file, "OBS-00", "event_types_file_exists")
    
    # Count event types (should be 12 required + 1 Phase 3 = 13)
    with open(event_types_file, 'r') as f:
        content = f.read()
        event_type_count = content.count('= "')
        if event_type_count >= 12:
            VERIFICATION_RESULTS.setdefault("OBS-00", {})["event_type_count"] = f"[PASS] ({event_type_count} found)"
            print(f"  [PASS] Event types: {event_type_count} found (12 required + Phase 3)")
        else:
            VERIFICATION_RESULTS.setdefault("OBS-00", {})["event_type_count"] = f"[FAIL] ({event_type_count} found)"
            print(f"  [FAIL] Event types: Only {event_type_count} found, need at least 12")
    
    # Verify versioning rules
    versioning_file = obs_root / "contracts/VERSIONING.md"
    verify_file_exists(versioning_file, "OBS-00", "versioning_rules_documented")
    
    # OBS-01: Payload JSON Schemas
    print("\nOBS-01: Payload JSON Schemas")
    payloads_dir = obs_root / "contracts/payloads"
    required_schemas = [
        "error_captured_v1.json",
        "prompt_validation_result_v1.json",
        "memory_access_v1.json",
        "memory_validation_v1.json",
        "evaluation_result_v1.json",
        "user_flag_v1.json",
        "bias_scan_result_v1.json",
        "retrieval_eval_v1.json",
        "failure_replay_bundle_v1.json",
        "perf_sample_v1.json",
        "privacy_audit_v1.json",
        "alert_noise_control_v1.json",
    ]
    
    found_schemas = []
    for schema_file in required_schemas:
        schema_path = payloads_dir / schema_file
        if schema_path.exists():
            found_schemas.append(schema_file)
            VERIFICATION_RESULTS.setdefault("OBS-01", {})[f"schema_{schema_file}"] = "[PASS]"
        else:
            VERIFICATION_RESULTS.setdefault("OBS-01", {})[f"schema_{schema_file}"] = "[FAIL]"
    
    if len(found_schemas) == 12:
        VERIFICATION_RESULTS.setdefault("OBS-01", {})["all_schemas_present"] = "[PASS]"
        print(f"  [PASS] All 12 payload schemas found")
    else:
        VERIFICATION_RESULTS.setdefault("OBS-01", {})["all_schemas_present"] = f"[FAIL] ({len(found_schemas)}/12)"
        print(f"  [FAIL] Only {len(found_schemas)}/12 schemas found")
    
    # Verify schema loader
    schema_loader = payloads_dir / "schema_loader.py"
    verify_file_exists(schema_loader, "OBS-01", "schema_loader_exists")
    
    # Verify fixtures
    fixtures_valid = payloads_dir / "fixtures/valid"
    fixtures_invalid = payloads_dir / "fixtures/invalid"
    verify_file_exists(fixtures_valid, "OBS-01", "valid_fixtures_exist")
    verify_file_exists(fixtures_invalid, "OBS-01", "invalid_fixtures_exist")
    
    # OBS-02: Redaction Policy
    print("\nOBS-02: Redaction Policy")
    redaction_policy = obs_root / "privacy/redaction_policy.md"
    verify_file_exists(redaction_policy, "OBS-02", "redaction_policy_doc")
    
    deny_patterns = obs_root / "privacy/deny_patterns.json"
    verify_file_exists(deny_patterns, "OBS-02", "deny_patterns_file")
    
    redaction_enforcer = obs_root / "privacy/redaction_enforcer.py"
    verify_file_exists(redaction_enforcer, "OBS-02", "redaction_enforcer_class")
    
    # OBS-03: Trace Context Propagation
    print("\nOBS-03: Trace Context Propagation")
    trace_propagation = obs_root / "correlation/trace_propagation.md"
    verify_file_exists(trace_propagation, "OBS-03", "trace_propagation_spec")
    
    trace_context_py = obs_root / "correlation/trace_context.py"
    verify_file_exists(trace_context_py, "OBS-03", "trace_context_python")
    
    trace_context_ts = obs_root / "correlation/trace_context.ts"
    verify_file_exists(trace_context_ts, "OBS-03", "trace_context_typescript")
    
    examples_dir = obs_root / "correlation/examples"
    verify_file_exists(examples_dir, "OBS-03", "trace_examples_exist")


def verify_phase1():
    """Verify Phase 1 tasks (OBS-04 through OBS-09)."""
    print("\n=== Phase 1 Verification (OBS-04 through OBS-09) ===\n")
    
    obs_root = PROJECT_ROOT / "src/shared_libs/zeroui_observability"
    
    # OBS-04: Collector Pipeline
    print("OBS-04: Collector Pipeline Blueprint")
    collector_config = obs_root / "collector/collector-config.yaml"
    verify_file_exists(collector_config, "OBS-04", "collector_config_exists")
    
    # Check for OTLP receiver configuration
    with open(collector_config, 'r') as f:
        content = f.read()
        if '4317' in content and '4318' in content:
            VERIFICATION_RESULTS.setdefault("OBS-04", {})["otlp_receiver_ports"] = "[PASS]"
            print("  [PASS] OTLP receiver configured (gRPC: 4317, HTTP: 4318)")
        else:
            VERIFICATION_RESULTS.setdefault("OBS-04", {})["otlp_receiver_ports"] = "[FAIL]"
            print("  [FAIL] OTLP receiver ports not found")
    
    deployment_notes = obs_root / "collector/DEPLOYMENT.md"
    verify_file_exists(deployment_notes, "OBS-04", "deployment_notes")
    
    # OBS-05: Schema Guard
    print("\nOBS-05: Schema Guard Service")
    schema_guard = obs_root / "collector/processors/schema_guard/schema_guard_processor.py"
    verify_file_exists(schema_guard, "OBS-05", "schema_guard_processor")
    
    # OBS-06: Privacy Guard
    print("\nOBS-06: Privacy Guard Enforcement")
    privacy_guard = obs_root / "collector/processors/privacy_guard/privacy_guard_processor.py"
    verify_file_exists(privacy_guard, "OBS-06", "privacy_guard_processor")
    
    # OBS-07: Baseline Telemetry Emission
    print("\nOBS-07: Baseline Telemetry Emission")
    python_instrumentation = obs_root / "instrumentation/python/instrumentation.py"
    verify_file_exists(python_instrumentation, "OBS-07", "python_instrumentation")
    
    typescript_instrumentation = obs_root / "instrumentation/typescript/instrumentation.ts"
    verify_file_exists(typescript_instrumentation, "OBS-07", "typescript_instrumentation")
    
    feature_flags = obs_root / "instrumentation/FEATURE_FLAGS.md"
    verify_file_exists(feature_flags, "OBS-07", "feature_flags_doc")
    
    # OBS-08: SLI Computation
    print("\nOBS-08: SLI Computation Library")
    sli_calculator = obs_root / "sli/sli_calculator.py"
    verify_file_exists(sli_calculator, "OBS-08", "sli_calculator")
    
    # Check for all 7 SLIs
    with open(sli_calculator, 'r') as f:
        content = f.read()
        sli_methods = ['compute_sli_a', 'compute_sli_b', 'compute_sli_c', 'compute_sli_d',
                       'compute_sli_e', 'compute_sli_f', 'compute_sli_g']
        found_slis = [m for m in sli_methods if f'def {m}' in content]
        if len(found_slis) == 7:
            VERIFICATION_RESULTS.setdefault("OBS-08", {})["all_slis_implemented"] = "[PASS]"
            print(f"  [PASS] All 7 SLIs implemented")
        else:
            VERIFICATION_RESULTS.setdefault("OBS-08", {})["all_slis_implemented"] = f"[FAIL] ({len(found_slis)}/7)"
            print(f"  [FAIL] Only {len(found_slis)}/7 SLIs found")
    
    sli_formulas = obs_root / "sli/SLI_FORMULAS.md"
    verify_file_exists(sli_formulas, "OBS-08", "sli_formulas_doc")
    
    # OBS-09: Dashboards
    print("\nOBS-09: Dashboards D1-D15")
    dashboards_dir = obs_root / "dashboards"
    required_dashboards = [f"d{i}_{name}.json" for i, name in [
        (1, "system_health"), (2, "error_analysis"), (3, "prompt_quality"),
        (4, "memory_health"), (5, "response_evaluation"), (6, "bias_monitoring"),
        (7, "emergent_interaction"), (8, "multi_agent_coordination"),
        (9, "retrieval_evaluation"), (10, "failure_analysis"),
        (11, "production_readiness"), (12, "performance_under_load"),
        (13, "privacy_compliance"), (14, "cross_channel_consistency"),
        (15, "false_positive_control")
    ]]
    
    found_dashboards = []
    for dashboard in required_dashboards:
        dashboard_path = dashboards_dir / dashboard
        if dashboard_path.exists():
            found_dashboards.append(dashboard)
            VERIFICATION_RESULTS.setdefault("OBS-09", {})[f"dashboard_{dashboard}"] = "[PASS]"
    
    if len(found_dashboards) == 15:
        VERIFICATION_RESULTS.setdefault("OBS-09", {})["all_dashboards_present"] = "[PASS]"
        print(f"  [PASS] All 15 dashboards found")
    else:
        VERIFICATION_RESULTS.setdefault("OBS-09", {})["all_dashboards_present"] = f"[FAIL] ({len(found_dashboards)}/15)"
        print(f"  [FAIL] Only {len(found_dashboards)}/15 dashboards found")
    
    dashboard_loader = dashboards_dir / "dashboard_loader.py"
    verify_file_exists(dashboard_loader, "OBS-09", "dashboard_loader")
    
    dashboard_mapping = dashboards_dir / "DASHBOARD_MAPPING.md"
    verify_file_exists(dashboard_mapping, "OBS-09", "dashboard_mapping")


def verify_phase2():
    """Verify Phase 2 tasks (OBS-10 through OBS-12)."""
    print("\n=== Phase 2 Verification (OBS-10 through OBS-12) ===\n")
    
    obs_root = PROJECT_ROOT / "src/shared_libs/zeroui_observability"
    
    # OBS-10: Alert Config Contract
    print("OBS-10: Alert Config Contract")
    alert_config = obs_root / "alerting/alert_config.py"
    verify_file_exists(alert_config, "OBS-10", "alert_config_loader")
    
    # OBS-11: Burn-rate Alert Engine
    print("\nOBS-11: Burn-rate Alert Engine")
    burn_rate_engine = obs_root / "alerting/burn_rate_engine.py"
    verify_file_exists(burn_rate_engine, "OBS-11", "burn_rate_engine")
    
    # OBS-12: Noise Control
    print("\nOBS-12: Noise Control")
    noise_control = obs_root / "alerting/noise_control.py"
    verify_file_exists(noise_control, "OBS-12", "noise_control_processor")


def verify_phase3():
    """Verify Phase 3 tasks (OBS-13 through OBS-14)."""
    print("\n=== Phase 3 Verification (OBS-13 through OBS-14) ===\n")
    
    obs_root = PROJECT_ROOT / "src/shared_libs/zeroui_observability"
    
    # OBS-13: Forecast Signals
    print("OBS-13: Forecast Signals")
    forecast_calculator = obs_root / "forecast/forecast_calculator.py"
    verify_file_exists(forecast_calculator, "OBS-13", "forecast_calculator")
    
    leading_indicators = obs_root / "forecast/leading_indicators.py"
    verify_file_exists(leading_indicators, "OBS-13", "leading_indicators")
    
    forecast_service = obs_root / "forecast/forecast_service.py"
    verify_file_exists(forecast_service, "OBS-13", "forecast_service")
    
    # Check for forecast.signal.v1 schema
    forecast_schema = obs_root / "forecast/contracts/forecast_signal_v1.json"
    verify_file_exists(forecast_schema, "OBS-13", "forecast_signal_schema")
    
    # OBS-14: Prevent-First Actions
    print("\nOBS-14: Prevent-First Actions")
    action_policy = obs_root / "prevent_first/action_policy.py"
    verify_file_exists(action_policy, "OBS-14", "action_policy")
    
    action_executor = obs_root / "prevent_first/action_executor.py"
    verify_file_exists(action_executor, "OBS-14", "action_executor")


def verify_phase4():
    """Verify Phase 4 tasks (OBS-15 through OBS-18)."""
    print("\n=== Phase 4 Verification (OBS-15 through OBS-18) ===\n")
    
    obs_root = PROJECT_ROOT / "src/shared_libs/zeroui_observability"
    
    # OBS-15: Failure Replay Bundle Builder
    print("OBS-15: Failure Replay Bundle Builder")
    replay_builder = obs_root / "replay/replay_bundle_builder.py"
    verify_file_exists(replay_builder, "OBS-15", "replay_bundle_builder")
    
    replay_storage = obs_root / "replay/replay_storage.py"
    verify_file_exists(replay_storage, "OBS-15", "replay_storage")
    
    # OBS-16: Runbooks RB-1..RB-5
    print("\nOBS-16: Runbooks RB-1..RB-5")
    runbooks_dir = obs_root / "runbooks"
    required_runbooks = [
        "runbook_rb1_error_spike.py",
        "runbook_rb2_latency_regression.py",
        "runbook_rb3_retrieval_quality.py",
        "runbook_rb4_bias_spike.py",
        "runbook_rb5_alert_flood.py",
    ]
    
    found_runbooks = []
    for runbook in required_runbooks:
        runbook_path = runbooks_dir / runbook
        if runbook_path.exists():
            found_runbooks.append(runbook)
            VERIFICATION_RESULTS.setdefault("OBS-16", {})[f"runbook_{runbook}"] = "[PASS]"
    
    if len(found_runbooks) == 5:
        VERIFICATION_RESULTS.setdefault("OBS-16", {})["all_runbooks_present"] = "[PASS]"
        print(f"  [PASS] All 5 runbooks found")
    else:
        VERIFICATION_RESULTS.setdefault("OBS-16", {})["all_runbooks_present"] = f"[FAIL] ({len(found_runbooks)}/5)"
        print(f"  [FAIL] Only {len(found_runbooks)}/5 runbooks found")
    
    runbook_executor = runbooks_dir / "runbook_executor.py"
    verify_file_exists(runbook_executor, "OBS-16", "runbook_executor")
    
    oncall_playbook = runbooks_dir / "oncall_playbook.py"
    verify_file_exists(oncall_playbook, "OBS-16", "oncall_playbook")
    
    # OBS-17: Acceptance Tests AT-1..AT-7
    print("\nOBS-17: Acceptance Tests AT-1..AT-7")
    acceptance_dir = PROJECT_ROOT / "tests/observability/acceptance"
    required_tests = [
        "acceptance_test_harness.py",
        "test_at1_contextual_error_logging.py",
        "test_at2_prompt_validation_telemetry.py",
        "test_at3_retrieval_threshold_telemetry.py",
        "test_at4_failure_replay_bundle.py",
        "test_at5_privacy_audit_event.py",
        "test_at6_alert_rate_limiting.py",
        "test_at7_confidence_gated_human_review.py",
    ]
    
    found_tests = []
    for test_file in required_tests:
        test_path = acceptance_dir / test_file
        if test_path.exists():
            found_tests.append(test_file)
            VERIFICATION_RESULTS.setdefault("OBS-17", {})[f"test_{test_file}"] = "[PASS]"
    
    if len(found_tests) == 8:
        VERIFICATION_RESULTS.setdefault("OBS-17", {})["all_acceptance_tests_present"] = "[PASS]"
        print(f"  [PASS] All 8 acceptance test files found (harness + 7 tests)")
    else:
        VERIFICATION_RESULTS.setdefault("OBS-17", {})["all_acceptance_tests_present"] = f"[FAIL] ({len(found_tests)}/8)"
        print(f"  [FAIL] Only {len(found_tests)}/8 acceptance test files found")
    
    # OBS-18: Challenge Traceability Gates
    print("\nOBS-18: Challenge Traceability Gates")
    traceability_matrix = obs_root / "governance/challenge_traceability_matrix.json"
    verify_file_exists(traceability_matrix, "OBS-18", "traceability_matrix")
    
    matrix_validator = obs_root / "governance/challenge_traceability_matrix.py"
    verify_file_exists(matrix_validator, "OBS-18", "matrix_validator")
    
    ci_validator = obs_root / "governance/ci_validator.py"
    verify_file_exists(ci_validator, "OBS-18", "ci_validator")
    
    # Verify all 20 challenges in matrix
    try:
        with open(traceability_matrix, 'r', encoding='utf-8') as f:
            matrix = json.load(f)
            challenges = matrix.get('challenges', [])
            if len(challenges) == 20:
                VERIFICATION_RESULTS.setdefault("OBS-18", {})["challenge_count"] = "[PASS]"
                print(f"  [PASS] All 20 challenges in matrix")
            else:
                VERIFICATION_RESULTS.setdefault("OBS-18", {})["challenge_count"] = f"[FAIL] ({len(challenges)}/20)"
                print(f"  [FAIL] Only {len(challenges)}/20 challenges in matrix")
    except Exception as e:
        VERIFICATION_RESULTS.setdefault("OBS-18", {})["challenge_count"] = f"[FAIL] Error: {e}"
        print(f"  [FAIL] Error reading matrix: {e}")


def print_summary():
    """Print verification summary."""
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    
    total_checks = 0
    passed_checks = 0
    
    for task_id, checks in sorted(VERIFICATION_RESULTS.items()):
        print(f"\n{task_id}:")
        for check_name, result in sorted(checks.items()):
            total_checks += 1
            if "[PASS]" in result:
                passed_checks += 1
            print(f"  {check_name}: {result}")
    
    print(f"\n{'='*80}")
    print(f"Total Checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {total_checks - passed_checks}")
    print(f"Pass Rate: {(passed_checks/total_checks*100):.1f}%")
    print("="*80)


if __name__ == "__main__":
    import sys
    # Set UTF-8 encoding for Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("ZeroUI Observability Layer - Triple Verification")
    print("="*80)
    
    verify_phase0()
    verify_phase1()
    verify_phase2()
    verify_phase3()
    verify_phase4()
    
    print_summary()
    
    # Save results to JSON
    results_file = PROJECT_ROOT / "docs/architecture/observability/verification_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(VERIFICATION_RESULTS, f, indent=2)
    print(f"\nResults saved to: {results_file}")
