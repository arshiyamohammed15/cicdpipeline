#!/usr/bin/env python3
"""
Test file for Basic Work Rules (4, 5, 10)

This file is designed to trigger violations of basic work rules:
- Rule 4: Use Settings Files, Not Hardcoded Numbers
- Rule 5: Keep Good Records + Keep Good Logs
- Rule 10: Be Honest About AI Decisions
"""

# Rule 4 violations - hardcoded values instead of settings
DATABASE_HOST = "localhost"  # Should be in settings
DATABASE_PORT = 5432  # Should be in settings
API_KEY = "sk-1234567890abcdef"  # Should be in environment variables
MAX_RETRIES = 5  # Should be configurable
TIMEOUT_SECONDS = 30  # Should be in settings

# Rule 5 violations - no logging or record keeping
def process_data(data):
    # No logging of what we're doing
    result = data.upper()
    # No audit trail
    return result

def calculate_total(items):
    # No logging of calculations
    total = sum(items)
    # No record of the operation
    return total

# Rule 10 violations - AI decisions without transparency
def ai_predict_outcome(input_data):
    # No confidence level reported
    prediction = "positive"
    # No explanation of reasoning
    return prediction

def ai_classify_text(text):
    # No version tracking
    classification = "spam"
    # No uncertainty handling
    return classification

def ai_recommend_action(user_data):
    # No transparency about decision process
    recommendation = "upgrade"
    # No confidence reporting
    return recommendation

# Missing patterns that should be present
def missing_settings_usage():
    # No config file usage
    # No environment variable usage
    pass

def missing_logging():
    # No structured logging
    # No audit trails
    # No log levels
    pass

def missing_ai_transparency():
    # No confidence levels
    # No explanations
    # No version tracking
    # No uncertainty handling
    pass
