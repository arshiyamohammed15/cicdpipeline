#!/usr/bin/env python3
"""
Rule 4: Use Settings Files, Not Hardcoded Numbers - VIOLATION

What: Demonstrates violation of settings files rule
Why: Shows what NOT to do (hardcoded values)
Reads: None
Writes: None
Contracts: None
Risks: Hard to maintain, not configurable
"""

# VIOLATION: Using hardcoded values instead of settings files
MAX_RETRIES = 3  # Should be in settings file
TIMEOUT = 30     # Should be in settings file
BATCH_SIZE = 100 # Should be in settings file

def process_data(data):
    """Process data with hardcoded values (VIOLATION)"""
    # VIOLATION: Using hardcoded batch size
    for i in range(0, len(data), 100):  # Hardcoded 100
        batch = data[i:i + 100]  # Hardcoded 100
        # VIOLATION: Using hardcoded timeout
        process_batch(batch, 30)  # Hardcoded 30

def process_batch(batch, timeout):
    """Process a batch of data with hardcoded timeout (VIOLATION)"""
    # VIOLATION: Hardcoded timeout value
    if timeout > 30:  # Hardcoded 30
        raise ValueError("Timeout too high")
    
    # Implementation here
    pass
