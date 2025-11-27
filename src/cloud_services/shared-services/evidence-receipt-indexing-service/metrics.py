"""
Prometheus metrics for Evidence & Receipt Indexing Service (ERIS).

What: Prometheus metrics collection and export
Why: Observability per PRD NFR-5
Reads/Writes: Tracks service metrics, exports Prometheus format
Contracts: Prometheus metrics format
Risks: Performance impact if metrics collection is too frequent
"""

try:
    from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Fallback metrics storage if prometheus_client not available
    _metrics_store = {
        "eris_receipts_ingested_total": 0,
        "eris_receipts_validation_errors_total": 0,
        "eris_queries_total": 0,
        "eris_query_duration_seconds": [],
        "eris_ingestion_duration_seconds": [],
        "eris_dlq_entries_total": 0,
        "eris_export_jobs_total": 0,
    }

# Metrics definitions
if PROMETHEUS_AVAILABLE:
    receipts_ingested = Counter(
        'eris_receipts_ingested_total',
        'Total number of receipts ingested',
        ['tenant_id', 'status']
    )
    
    validation_errors = Counter(
        'eris_receipts_validation_errors_total',
        'Total number of receipt validation errors',
        ['error_type']
    )
    
    queries_total = Counter(
        'eris_queries_total',
        'Total number of queries',
        ['query_type', 'tenant_id']
    )
    
    query_duration = Histogram(
        'eris_query_duration_seconds',
        'Query duration in seconds',
        ['query_type'],
        buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
    )
    
    ingestion_duration = Histogram(
        'eris_ingestion_duration_seconds',
        'Ingestion duration in seconds',
        ['ingestion_type'],
        buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
    )
    
    dlq_entries = Counter(
        'eris_dlq_entries_total',
        'Total number of DLQ entries created',
        ['tenant_id']
    )
    
    export_jobs = Counter(
        'eris_export_jobs_total',
        'Total number of export jobs created',
        ['tenant_id', 'format']
    )
    
    integrity_checks_total = Counter(
        'eris_integrity_checks_total',
        'Total number of integrity checks performed',
        ['check_type', 'tenant_id', 'result']
    )
    
    integrity_check_duration = Histogram(
        'eris_integrity_check_duration_seconds',
        'Integrity check duration in seconds',
        ['check_type'],
        buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
    )
    
    rate_limit_exceeded = Counter(
        'eris_rate_limit_exceeded_total',
        'Total number of rate limit exceeded events',
        ['tenant_id', 'endpoint']
    )
else:
    # Fallback metrics objects
    class FallbackCounter:
        def __init__(self, name, description, labels=None):
            self.name = name
            self.description = description
            self.labels = labels or []
        
        def inc(self, **labels):
            _metrics_store[self.name] = _metrics_store.get(self.name, 0) + 1
    
    class FallbackHistogram:
        def __init__(self, name, description, labels=None, buckets=None):
            self.name = name
            self.description = description
            self.labels = labels or []
            self.buckets = buckets or []
        
        def observe(self, value, **labels):
            if self.name not in _metrics_store:
                _metrics_store[self.name] = []
            _metrics_store[self.name].append(value)
    
    receipts_ingested = FallbackCounter('eris_receipts_ingested_total', 'Total number of receipts ingested')
    validation_errors = FallbackCounter('eris_receipts_validation_errors_total', 'Total number of receipt validation errors')
    queries_total = FallbackCounter('eris_queries_total', 'Total number of queries')
    query_duration = FallbackHistogram('eris_query_duration_seconds', 'Query duration in seconds')
    ingestion_duration = FallbackHistogram('eris_ingestion_duration_seconds', 'Ingestion duration in seconds')
    dlq_entries = FallbackCounter('eris_dlq_entries_total', 'Total number of DLQ entries created')
    export_jobs = FallbackCounter('eris_export_jobs_total', 'Total number of export jobs created')
    integrity_checks_total = FallbackCounter('eris_integrity_checks_total', 'Total number of integrity checks performed')
    integrity_check_duration = FallbackHistogram('eris_integrity_check_duration_seconds', 'Integrity check duration in seconds')
    rate_limit_exceeded = FallbackCounter('eris_rate_limit_exceeded_total', 'Total number of rate limit exceeded events')


def get_metrics_text() -> str:
    """
    Get Prometheus format metrics text.
    
    Returns:
        Prometheus format metrics string
    """
    if PROMETHEUS_AVAILABLE:
        return generate_latest(REGISTRY).decode('utf-8')
    else:
        # Fallback: generate simple Prometheus format
        lines = []
        lines.append("# HELP eris_receipts_ingested_total Total number of receipts ingested")
        lines.append("# TYPE eris_receipts_ingested_total counter")
        lines.append(f"eris_receipts_ingested_total {_metrics_store.get('eris_receipts_ingested_total', 0)}")
        
        lines.append("# HELP eris_receipts_validation_errors_total Total number of receipt validation errors")
        lines.append("# TYPE eris_receipts_validation_errors_total counter")
        lines.append(f"eris_receipts_validation_errors_total {_metrics_store.get('eris_receipts_validation_errors_total', 0)}")
        
        lines.append("# HELP eris_queries_total Total number of queries")
        lines.append("# TYPE eris_queries_total counter")
        lines.append(f"eris_queries_total {_metrics_store.get('eris_queries_total', 0)}")
        
        lines.append("# HELP eris_dlq_entries_total Total number of DLQ entries created")
        lines.append("# TYPE eris_dlq_entries_total counter")
        lines.append(f"eris_dlq_entries_total {_metrics_store.get('eris_dlq_entries_total', 0)}")
        
        lines.append("# HELP eris_export_jobs_total Total number of export jobs created")
        lines.append("# TYPE eris_export_jobs_total counter")
        lines.append(f"eris_export_jobs_total {_metrics_store.get('eris_export_jobs_total', 0)}")
        
        lines.append("# HELP eris_integrity_checks_total Total number of integrity checks performed")
        lines.append("# TYPE eris_integrity_checks_total counter")
        lines.append(f"eris_integrity_checks_total {_metrics_store.get('eris_integrity_checks_total', 0)}")
        
        lines.append("# HELP eris_rate_limit_exceeded_total Total number of rate limit exceeded events")
        lines.append("# TYPE eris_rate_limit_exceeded_total counter")
        lines.append(f"eris_rate_limit_exceeded_total {_metrics_store.get('eris_rate_limit_exceeded_total', 0)}")
        
        # Histograms - calculate summary statistics
        query_durations = _metrics_store.get('eris_query_duration_seconds', [])
        if query_durations:
            lines.append("# HELP eris_query_duration_seconds Query duration in seconds")
            lines.append("# TYPE eris_query_duration_seconds histogram")
            lines.append(f"eris_query_duration_seconds_count {len(query_durations)}")
            if query_durations:
                lines.append(f"eris_query_duration_seconds_sum {sum(query_durations)}")
        
        ingestion_durations = _metrics_store.get('eris_ingestion_duration_seconds', [])
        if ingestion_durations:
            lines.append("# HELP eris_ingestion_duration_seconds Ingestion duration in seconds")
            lines.append("# TYPE eris_ingestion_duration_seconds histogram")
            lines.append(f"eris_ingestion_duration_seconds_count {len(ingestion_durations)}")
            if ingestion_durations:
                lines.append(f"eris_ingestion_duration_seconds_sum {sum(ingestion_durations)}")
        
        integrity_check_durations = _metrics_store.get('eris_integrity_check_duration_seconds', [])
        if integrity_check_durations:
            lines.append("# HELP eris_integrity_check_duration_seconds Integrity check duration in seconds")
            lines.append("# TYPE eris_integrity_check_duration_seconds histogram")
            lines.append(f"eris_integrity_check_duration_seconds_count {len(integrity_check_durations)}")
            if integrity_check_durations:
                lines.append(f"eris_integrity_check_duration_seconds_sum {sum(integrity_check_durations)}")
        
        return '\n'.join(lines) + '\n'

