#!/usr/bin/env python3
"""
Rule 5: Keep Good Records + Keep Good Logs - VALID

What: Demonstrates proper logging and record keeping
Why: Shows compliance with Rule 5
Reads: config/logging.json
Writes: logs, receipts
Contracts: Logging API contract
Risks: None
"""

import json
import logging
from pathlib import Path
from datetime import datetime

# Setup structured logging
def setup_logger():
    """Setup structured logger (Rule 5 compliance)"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Create structured log handler
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"message": "%(message)s", "service": "example_service"}'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

logger = setup_logger()

def process_request(request_data):
    """Process request with proper logging"""
    # Log request start
    logger.info("Request processing started", extra={
        "request_id": request_data.get("id"),
        "action": "request.start"
    })
    
    try:
        # Process the request
        result = perform_work(request_data)
        
        # Log success
        logger.info("Request processing completed", extra={
            "request_id": request_data.get("id"),
            "action": "request.end",
            "status": "success"
        })
        
        return result
        
    except Exception as e:
        # Log error
        logger.error("Request processing failed", extra={
            "request_id": request_data.get("id"),
            "action": "request.error",
            "error": str(e)
        })
        raise

def perform_work(data):
    """Perform the actual work"""
    # Implementation here
    return {"status": "completed", "data": data}

def emit_receipt(action, status, data):
    """Emit receipt for audit trail"""
    receipt = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "status": status,
        "data_hash": hash(str(data))
    }
    
    # Log receipt
    logger.info("Receipt emitted", extra={
        "action": "receipt.emit",
        "receipt": receipt
    })
    
    return receipt
