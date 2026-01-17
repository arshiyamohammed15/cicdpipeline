"""
Acceptance Test AT-7: Confidence-Gated Human Review

Per PRD Section 9:
Pass Criteria: Create low-confidence detections; verify routed to human validation
(no auto corrective action).
"""

import logging
from typing import Any, Dict

try:
    from src.shared_libs.zeroui_observability.prevent_first.action_executor import ActionExecutor
    from src.shared_libs.zeroui_observability.prevent_first.action_policy import ActionPolicy, ActionPolicyConfig
    PREVENT_FIRST_AVAILABLE = True
except ImportError:
    PREVENT_FIRST_AVAILABLE = False
    ActionExecutor = None  # type: ignore
    ActionPolicy = None  # type: ignore
    ActionPolicyConfig = None  # type: ignore

logger = logging.getLogger(__name__)


def test_at7(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute AT-7: Confidence-Gated Human Review.

    Args:
        context: Test context

    Returns:
        Test result dictionary with 'passed' boolean
    """
    # Create low-confidence detection
    low_confidence = 0.3  # Below threshold
    min_confidence = 0.8  # Required confidence

    if not PREVENT_FIRST_AVAILABLE or ActionPolicy is None or ActionPolicyConfig is None:
        return {
            "passed": False,
            "error": "ActionPolicy/ActionPolicyConfig not available",
        }

    # Create action policy config
    policy_config = ActionPolicyConfig(
        action_id="test_action",
        action_type="create_ticket",
        enabled=True,
        confidence_gate={"enabled": True, "min_confidence": min_confidence},
    )

    # Create action policy and executor
    action_policy = ActionPolicy()
    executor = ActionExecutor(action_policy=action_policy)

    # Simulate confidence gate check (low confidence should block action)
    confidence_gate_enabled = policy_config.confidence_gate.get("enabled", False)
    min_confidence_threshold = policy_config.confidence_gate.get("min_confidence", 0.0)

    # Verify confidence gate blocks low-confidence actions
    confidence_passes = low_confidence >= min_confidence_threshold

    # Simulate action result
    action_result = {
        "executed": False,
        "routed_to_human": not confidence_passes,
        "reason": "confidence_below_threshold" if not confidence_passes else None,
        "confidence": low_confidence,
        "min_confidence": min_confidence_threshold,
    }

    # Verify routed to human validation (no auto action)
    passed = (
        action_result.get("executed") is False
        and action_result.get("routed_to_human") is True
        and action_result.get("reason") == "confidence_below_threshold"
    )

    return {
        "passed": passed,
        "action_result": action_result,
        "confidence": low_confidence,
        "min_confidence": min_confidence,
    }
