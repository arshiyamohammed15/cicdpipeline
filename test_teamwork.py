"""
Test file for teamwork rules (58).
"""

# Rule 58 violations: Missing early issue detection
def process_user_data(data):
    # No early validation
    # No input validation
    # No fail-fast patterns
    # No precondition checks
    # No warnings
    # No boundary checks
    return data.upper()

def calculate_age(birth_year):
    # No early validation
    return 2024 - birth_year

def save_file(filename, content):
    # No early validation
    with open(filename, 'w') as f:
        f.write(content)

def process_request(request_data):
    # No early validation
    # No boundary condition checks
    # No fail-fast patterns
    return request_data

def handle_user_input(user_input):
    # No early validation
    # No precondition checks
    # No warning mechanisms
    return user_input

def validate_email(email):
    # No early validation patterns
    # No boundary checks
    return "@" in email

def process_payment(amount, currency):
    # No early validation
    # No boundary condition validation
    # No fail-fast patterns
    return f"Processed {amount} {currency}"
