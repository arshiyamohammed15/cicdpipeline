#!/usr/bin/env python3
"""
Rule 5: Keep Good Records + Keep Good Logs - VIOLATION

What: Demonstrates violation of logging and record keeping
Why: Shows what NOT to do (no logging, no records)
Reads: None
Writes: None
Contracts: None
Risks: No audit trail, hard to debug
"""

# VIOLATION: No logging setup
# VIOLATION: No structured logging
# VIOLATION: No receipt system

def process_request(request_data):
    """Process request without proper logging (VIOLATION)"""
    # VIOLATION: No logging of request start
    # VIOLATION: No request ID tracking
    
    try:
        # Process the request
        result = perform_work(request_data)
        
        # VIOLATION: No logging of success
        # VIOLATION: No audit trail
        
        return result
        
    except Exception as e:
        # VIOLATION: No error logging
        # VIOLATION: No error tracking
        raise

def perform_work(data):
    """Perform work without logging (VIOLATION)"""
    # VIOLATION: No logging of work performed
    # VIOLATION: No performance tracking
    return {"status": "completed", "data": data}

def emit_receipt(action, status, data):
    """VIOLATION: No receipt system"""
    # VIOLATION: No receipt emission
    # VIOLATION: No audit trail
    pass
