"""
Acceptance Test Harness for ZeroUI Observability Layer.

OBS-17: Automation harness for AT-1 through AT-7.

Orchestrates acceptance test execution and generates evidence packs.
"""

import json
import logging
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AcceptanceTestHarness:
    """
    Acceptance test harness orchestrator.

    Per OBS-17 requirements:
    - Executes AT-1 through AT-7
    - Generates evidence packs for test runs
    - Validates pass criteria from PRD Section 9
    - All tests must pass before enabling paging alerts
    """

    def __init__(
        self,
        evidence_output_dir: Optional[str] = None,
    ):
        """
        Initialize acceptance test harness.

        Args:
            evidence_output_dir: Directory for evidence pack output
        """
        self._evidence_dir = Path(evidence_output_dir or os.getenv("ZU_ROOT", "") + "/shared/eval/results/acceptance-tests")
        self._results: List[Dict[str, Any]] = []

    def run_all_tests(
        self,
        test_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run all acceptance tests (AT-1 through AT-7).

        Args:
            test_context: Optional test context (tenant_id, component, etc.)

        Returns:
            Test results summary
        """
        context = test_context or {}
        test_run_id = f"at_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Starting acceptance test run: {test_run_id}")

        results = {
            "test_run_id": test_run_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "tests": {},
            "summary": {
                "total": 7,
                "passed": 0,
                "failed": 0,
            },
        }

        # Import and run each acceptance test
        try:
            from .test_at1_contextual_error_logging import test_at1
            results["tests"]["AT-1"] = self._run_test("AT-1", test_at1, context)
        except Exception as e:
            logger.error(f"AT-1 failed: {e}")
            results["tests"]["AT-1"] = {"status": "failed", "error": str(e)}

        try:
            from .test_at2_prompt_validation_telemetry import test_at2
            results["tests"]["AT-2"] = self._run_test("AT-2", test_at2, context)
        except Exception as e:
            logger.error(f"AT-2 failed: {e}")
            results["tests"]["AT-2"] = {"status": "failed", "error": str(e)}

        try:
            from .test_at3_retrieval_threshold_telemetry import test_at3
            results["tests"]["AT-3"] = self._run_test("AT-3", test_at3, context)
        except Exception as e:
            logger.error(f"AT-3 failed: {e}")
            results["tests"]["AT-3"] = {"status": "failed", "error": str(e)}

        try:
            from .test_at4_failure_replay_bundle import test_at4
            results["tests"]["AT-4"] = self._run_test("AT-4", test_at4, context)
        except Exception as e:
            logger.error(f"AT-4 failed: {e}")
            results["tests"]["AT-4"] = {"status": "failed", "error": str(e)}

        try:
            from .test_at5_privacy_audit_event import test_at5
            results["tests"]["AT-5"] = self._run_test("AT-5", test_at5, context)
        except Exception as e:
            logger.error(f"AT-5 failed: {e}")
            results["tests"]["AT-5"] = {"status": "failed", "error": str(e)}

        try:
            from .test_at6_alert_rate_limiting import test_at6
            results["tests"]["AT-6"] = self._run_test("AT-6", test_at6, context)
        except Exception as e:
            logger.error(f"AT-6 failed: {e}")
            results["tests"]["AT-6"] = {"status": "failed", "error": str(e)}

        try:
            from .test_at7_confidence_gated_human_review import test_at7
            results["tests"]["AT-7"] = self._run_test("AT-7", test_at7, context)
        except Exception as e:
            logger.error(f"AT-7 failed: {e}")
            results["tests"]["AT-7"] = {"status": "failed", "error": str(e)}

        # Calculate summary
        for test_result in results["tests"].values():
            if test_result.get("status") == "passed":
                results["summary"]["passed"] += 1
            else:
                results["summary"]["failed"] += 1

        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        results["all_passed"] = results["summary"]["failed"] == 0

        # Generate evidence pack
        evidence_path = self._generate_evidence_pack(test_run_id, results)

        results["evidence_pack"] = str(evidence_path)

        logger.info(f"Acceptance test run completed: {test_run_id}, passed: {results['summary']['passed']}/{results['summary']['total']}")

        return results

    def _run_test(
        self,
        test_id: str,
        test_func: Any,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run a single acceptance test.

        Args:
            test_id: Test ID (AT-1 through AT-7)
            test_func: Test function
            context: Test context

        Returns:
            Test result dictionary
        """
        try:
            result = test_func(context)
            return {
                "status": "passed" if result.get("passed", False) else "failed",
                "result": result,
            }
        except Exception as e:
            logger.error(f"{test_id} execution failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
            }

    def _generate_evidence_pack(
        self,
        test_run_id: str,
        results: Dict[str, Any],
    ) -> Path:
        """
        Generate evidence pack ZIP file.

        Args:
            test_run_id: Test run ID
            results: Test results

        Returns:
            Path to evidence pack ZIP file
        """
        # Build storage path per folder-business-rules.md
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        evidence_dir = self._evidence_dir / f"dt={date_str}"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        # Create ZIP file
        zip_path = evidence_dir / f"{test_run_id}_evidence.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add test results JSON
            results_json = json.dumps(results, indent=2, sort_keys=True)
            zipf.writestr("test_results.json", results_json)

            # Add individual test outputs if available
            for test_id, test_result in results.get("tests", {}).items():
                if "output" in test_result:
                    zipf.writestr(f"{test_id}_output.json", json.dumps(test_result["output"], indent=2))

        logger.info(f"Generated evidence pack: {zip_path}")

        return zip_path


def run_acceptance_tests(
    test_context: Optional[Dict[str, Any]] = None,
    evidence_output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run all acceptance tests.

    Args:
        test_context: Optional test context
        evidence_output_dir: Optional evidence output directory

    Returns:
        Test results summary
    """
    harness = AcceptanceTestHarness(evidence_output_dir=evidence_output_dir)
    return harness.run_all_tests(test_context=test_context)
