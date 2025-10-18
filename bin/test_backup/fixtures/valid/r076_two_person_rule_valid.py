# R076: Two-Person Rule Valid
# This file demonstrates compliance with the two-person rule

# CODEOWNERS file should exist with:
# auth/ @user1 @user2
# policy/ @user3 @user4
# contracts/ @user5 @user6
# migrations/ @user7 @user8

def sensitive_auth_function():
    """This function handles authentication - requires two reviewers"""
    return "auth logic"

def policy_update():
    """This function updates policies - requires two reviewers"""
    return "policy update"
