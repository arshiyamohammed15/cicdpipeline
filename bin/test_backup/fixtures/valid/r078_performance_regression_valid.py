# R078: Performance Regression Valid
# This file demonstrates performance-critical code with proper measurement

import time
import metrics

def database_query():
    """Database query with performance measurement"""
    # Performance budget: 100ms
    start_time = time.time()
    result = db.query("SELECT * FROM large_table")
    latency = time.time() - start_time

    # Performance measurement and budget check
    assert latency < 0.1, f"Query exceeded 100ms budget: {latency:.3f}s"
    metrics.histogram('db.query.latency', latency)

    return result

def api_call():
    """API call with performance monitoring"""
    # Network call with latency measurement
    start_time = time.time()
    response = requests.get("https://api.example.com/data")
    latency = time.time() - start_time

    # Performance tracking
    metrics.histogram('api.call.latency', latency)
    if latency > 0.5:  # 500ms threshold
        metrics.increment('api.call.slow')

    return response.json()

def file_operation():
    """File operation with performance tracking"""
    # File I/O with measurement
    start_time = time.time()
    with open("large_file.txt", "r") as f:
        data = f.read()
    latency = time.time() - start_time

    # Performance monitoring
    metrics.histogram('file.read.latency', latency)

    return data
