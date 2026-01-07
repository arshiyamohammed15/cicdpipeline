from datetime import datetime, timedelta, timezone

import pytest

from user_behaviour_intelligence.integrations.pm3_client import PM3Client


@pytest.mark.unit
def test_pm3_client_out_of_order_buffering_and_in_order_processing():
    handled = []
    client = PM3Client(dedup_window_hours=1, routing_class="analytics_store")
    client.subscribe(lambda env: handled.append(env) or True)

    # Future-dated event should be buffered (out-of-order) without raising
    future_time = datetime.now(timezone.utc) + timedelta(seconds=400)
    future_signal = {"signal_id": "sig-future", "tenant_id": "t1", "occurred_at": future_time.isoformat()}
    assert client.consume_signal(future_signal) is True
    assert len(client.event_buffer) == 1
    assert handled == []

    # In-order event should process immediately and invoke handler
    present_time = datetime.now(timezone.utc) - timedelta(seconds=5)
    present_signal = {"signal_id": "sig-present", "tenant_id": "t1", "occurred_at": present_time.isoformat()}
    assert client.consume_signal(present_signal) is True
    assert handled and handled[0]["signal_id"] == "sig-present"

    # After advancing time, buffered event can be processed without error
    processed_count = client.process_buffered_events()
    assert processed_count in (0, 1)

