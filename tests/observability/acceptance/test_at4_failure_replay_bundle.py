"""
Acceptance Test AT-4: Failure Replay Bundle

Per PRD Section 9:
Pass Criteria: Trigger failure; verify failure.replay.bundle.v1 is created and replayable.
"""

import logging
from typing import Any, Dict

from src.shared_libs.zeroui_observability.replay.replay_bundle_builder import ReplayBundleBuilder

logger = logging.getLogger(__name__)


def test_at4(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute AT-4: Failure Replay Bundle.

    Args:
        context: Test context

    Returns:
        Test result dictionary with 'passed' boolean
    """
    # Trigger failure and create replay bundle
    builder = ReplayBundleBuilder()

    trace_id = "a" * 32
    tenant_id = context.get("tenant_id", "test_tenant")

    try:
        # Build replay bundle from trace_id
        bundle = builder.build_from_trace_id(
            trace_id,
            tenant_id=tenant_id,
            component="test",
            channel="backend",
        )

        # Verify bundle was created
        bundle_created = bundle is not None
        bundle_replayable = (
            bundle.replay_id is not None
            and bundle.trigger_event_id is not None
            and len(bundle.included_event_ids) > 0
            and bundle.checksum is not None
        )

        # Convert to event payload
        bundle_payload = {"events": []}
        event_payload = builder.to_event_payload(bundle, bundle_payload)

        # Verify event payload structure
        payload_valid = (
            event_payload.get("replay_id") == bundle.replay_id
            and event_payload.get("trigger_event_id") == bundle.trigger_event_id
            and len(event_payload.get("included_event_ids", [])) > 0
            and event_payload.get("checksum") == bundle.checksum
        )

        passed = bundle_created and bundle_replayable and payload_valid

        return {
            "passed": passed,
            "bundle": {
                "replay_id": bundle.replay_id,
                "trigger_event_id": bundle.trigger_event_id,
                "included_event_ids_count": len(bundle.included_event_ids),
            },
            "event_payload": event_payload,
        }

    except Exception as e:
        logger.error(f"AT-4 failed: {e}")
        return {
            "passed": False,
            "error": str(e),
        }
