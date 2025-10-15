# R078: Performance Regression Violation
# This file demonstrates performance-critical code without measurement

def database_query():
    """Database query without performance measurement"""
    # Performance-critical operation without budget/measurement
    result = db.query("SELECT * FROM large_table")
    return result

def api_call():
    """API call without performance monitoring"""
    # Network call without latency measurement
    response = requests.get("https://api.example.com/data")
    return response.json()

def file_operation():
    """File operation without performance tracking"""
    # File I/O without measurement
    with open("large_file.txt", "r") as f:
        data = f.read()
    return data
