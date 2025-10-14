# R076: Two-Person Rule Violation
# This file demonstrates a violation of the two-person rule

# Missing CODEOWNERS file or insufficient reviewers for sensitive areas
# Sensitive areas like auth/, policy/, contracts/, migrations/ require two reviewers

def sensitive_auth_function():
    """This function handles authentication - should require two reviewers"""
    return "auth logic"

def policy_update():
    """This function updates policies - should require two reviewers"""
    return "policy update"
