"""
Test file for advanced system design rules (22, 25, 29, 30).
"""

# Rule 22 violations: Inconsistent module patterns
class UserManager:  # PascalCase
    def get_user(self):
        pass

class user_service:  # snake_case - inconsistent
    def get_user(self):
        pass

class UserDataHandler:  # PascalCase
    def process_data(self):
        pass

# Rule 25 violations: Information overload
def process_user_data(name, email, phone, address, city, state, zip_code, country, age, gender, preferences, settings):
    # Too many parameters - information overload
    pass

def complex_calculation(data, options, filters, validators, processors, transformers, analyzers, reporters):
    # Too many parameters without defaults
    pass

# Rule 29 violations: Inconsistent registration
class DatabaseConnection:
    def setup_database(self):
        pass
    
    def configure_connection(self):
        pass
    
    def initialize_db(self):
        pass
    # Multiple setup methods - inconsistent

class APIClient:
    # No __init__ method - missing standard initialization
    def connect(self):
        pass

# Rule 30 violations: Inconsistent product experience
def get_user_data():
    pass

def fetchUserInfo():  # Inconsistent naming
    pass

def retrieve_user_information():  # Inconsistent naming
    pass

# Inconsistent error messages
def validate_input(data):
    if not data:
        raise ValueError("Invalid data")  # No period
    if len(data) > 100:
        raise ValueError("Data too long.")  # With period
    if not isinstance(data, str):
        raise ValueError("Data must be string")  # No period
