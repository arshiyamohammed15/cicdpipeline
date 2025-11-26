from datetime import datetime

from ..services.routing_service import QuietHoursEvaluator


def test_quiet_hours_enforcement():
    evaluator = QuietHoursEvaluator({"Mon": "22:00-06:00"})
    quiet_time = datetime.strptime("2025-11-24 23:30", "%Y-%m-%d %H:%M")
    assert evaluator.is_quiet(quiet_time)
    active_time = datetime.strptime("2025-11-24 12:00", "%Y-%m-%d %H:%M")
    assert not evaluator.is_quiet(active_time)

