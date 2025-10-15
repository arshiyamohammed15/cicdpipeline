#!/usr/bin/env python3
"""
Rule 10: Be Honest About AI Decisions - VIOLATION

What: Demonstrates violation of AI decision transparency
Why: Shows what NOT to do (black box decisions)
Reads: None
Writes: None
Contracts: None
Risks: No transparency, no audit trail, no confidence tracking
"""

# VIOLATION: No AI model information
# VIOLATION: No confidence tracking
# VIOLATION: No explanation system

def make_ai_decision(input_data):
    """Make AI decision without transparency (VIOLATION)"""
    
    # VIOLATION: No confidence level
    # VIOLATION: No explanation
    # VIOLATION: No model version
    # VIOLATION: No reasoning
    
    # Black box decision
    decision = "approve"  # No explanation why
    
    # VIOLATION: No logging of decision
    # VIOLATION: No audit trail
    
    return decision

def log_ai_decision(decision):
    """VIOLATION: No decision logging"""
    # VIOLATION: No logging system
    # VIOLATION: No audit trail
    pass

def get_ai_model_info():
    """VIOLATION: No model information"""
    # VIOLATION: No transparency about AI model
    # VIOLATION: No version tracking
    # VIOLATION: No bias metrics
    return None
