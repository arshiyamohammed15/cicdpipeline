from bdr.observability import MetricsRegistry, StructuredLogger


def test_metrics_registry_supports_counters_and_gauges():
    metrics = MetricsRegistry()
    metrics.increment("metric", "label")
    metrics.set_gauge("lag", "plan", 5.0)
    assert metrics.get_counter("metric", "label") == 1
    assert metrics.get_counter("missing", "label") == 0
    assert metrics.get_gauge("lag", "plan") == 5.0
    assert metrics.get_gauge("lag", "unknown") == 0.0


def test_structured_logger_records_entries():
    logger = StructuredLogger()
    logger.info("message", key="value")
    logger.error("error", code=500)
    assert len(logger.entries) == 2

