# R009: Security & Privacy Violation
# This file demonstrates security issues that should be caught

def register_user(email, password, ssn):
    """
    Register new user with personal information.
    """
    # Store user data
    user_data = {
        'email': email,
        'password': password,  # Should be hashed
        'ssn': ssn,  # PII - should be encrypted
        'api_key': 'sk-1234567890abcdef'  # Secret in code
    }

    # Save to database
    db.users.insert(user_data)

    # Log registration
    print(f"User registered: {email} with SSN: {ssn}")

    return user_data
