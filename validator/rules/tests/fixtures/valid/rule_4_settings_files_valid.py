#!/usr/bin/env python3
"""
Rule 4: Use Settings Files, Not Hardcoded Numbers - VALID

What: Demonstrates proper use of settings files
Why: Shows compliance with Rule 4
Reads: config/settings.json
Writes: None
Contracts: Settings API contract
Risks: None
"""

import json
from pathlib import Path

# Load settings from configuration file
def load_settings():
    """Load settings from configuration file (Rule 4 compliance)"""
    settings_path = Path(__file__).parent.parent.parent.parent / "config" / "settings.json"
    
    with open(settings_path, 'r') as f:
        return json.load(f)

# Use settings instead of hardcoded values
settings = load_settings()
MAX_RETRIES = settings.get("max_retries", 3)
TIMEOUT = settings.get("timeout", 30)
BATCH_SIZE = settings.get("batch_size", 100)

def process_data(data):
    """Process data using settings from configuration file"""
    # Use settings instead of hardcoded values
    for i in range(0, len(data), BATCH_SIZE):
        batch = data[i:i + BATCH_SIZE]
        # Process batch with timeout from settings
        process_batch(batch, TIMEOUT)

def process_batch(batch, timeout):
    """Process a batch of data with configurable timeout"""
    # Implementation here
    pass
