"""
Acceptance Test AT-6: Alert Rate Limiting

Per PRD Section 9:
Pass Criteria: Repeat same alert condition; verify only one alert within rate limit window;
subsequent suppressed/deduped.
"""

import logging
from typing import Any, Dict

try:
    from src.shared_libs.zeroui_observability.alerting.noise_control import NoiseControlProcessor
except ImportError:
    # Fallback for testing
    NoiseControlProcessor = None

logger = logging.getLogger(__name__)


def test_at6(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute AT-6: Alert Rate Limiting.

    Args:
        context: Test context

    Returns:
        Test result dictionary with 'passed' boolean
    """
    # Create noise control processor
    if NoiseControlProcessor is None:
        return {
            "passed": False,
            "error": "NoiseControlProcessor not available",
        }
    
    processor = NoiseControlProcessor()

    # Generate same alert multiple times
    alert_id = "alert_001"
    alert_fingerprint = "fp_alert_001"

    # Process alerts through noise control (simulated - process_alert is async)
    import asyncio
    
    async def process_alerts():
        processed = []
        for i in range(5):
            alert_event = {
                "alert_id": alert_id,
                "component": "test",
                "channel": "backend",
            }
            decision, payload = await processor.process_alert(alert_event)
            processed.append({"decision": decision, "payload": payload})
        return processed
    
    # Run async function
    try:
        processed = asyncio.run(process_alerts())
    except Exception as e:
        return {
            "passed": False,
            "error": f"Failed to process alerts: {e}",
        }

    # Verify only first alert allowed, others suppressed/deduped
    allowed_count = sum(1 for p in processed if p.get("decision") == "allow")
    suppressed_count = sum(1 for p in processed if p.get("decision") in ["suppress", "dedup", "rate_limited"])

    passed = allowed_count == 1 and suppressed_count == 4

    return {
        "passed": passed,
        "allowed_count": allowed_count,
        "suppressed_count": suppressed_count,
        "processed": processed,
    }
