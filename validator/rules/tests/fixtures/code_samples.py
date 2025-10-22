"""
Reusable code samples for validator tests.

Contains valid and invalid code patterns organized by category.
"""

CODE_SAMPLES = {
    # Valid patterns
    'valid_function_with_docstring': '''
def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two integers.
    
    Args:
        a: First integer
        b: Second integer
        
    Returns:
        Sum of a and b
    """
    return a + b
''',
    
    'valid_error_handling': '''
import os

def read_file(path: str) -> str:
    """Read file with proper error handling."""
    try:
        with open(path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {path}")
    except IOError as e:
        raise IOError(f"Error reading file {path}: {e}")
''',
    
    'valid_api_with_versioning': '''
from flask import Flask

app = Flask(__name__)

@app.route('/api/v1/users', methods=['GET'])
def get_users():
    """Get all users."""
    return {"users": []}
''',
    
    # Invalid patterns
    'hardcoded_credentials': '''
# Bad: Hardcoded credentials
password = "SecretPass123"
api_key = "sk-1234567890abcdef"
database_password = "admin123"
''',
    
    'missing_docstring': '''
def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    return total
''',
    
    'no_error_handling': '''
def read_file(path):
    f = open(path, 'r')
    content = f.read()
    f.close()
    return content
''',
    
    'api_without_versioning': '''
@app.route('/api/users', methods=['GET'])
def get_users():
    return {"users": []}
''',
    
    'pii_in_code': '''
user_email = "john.doe@example.com"
ssn = "123-45-6789"
credit_card = "4532-1234-5678-9010"
''',
    
    'long_function': '''
def process_data(data):
    result = []
    for item in data:
        if item['type'] == 'A':
            processed = item['value'] * 2
            result.append(processed)
        elif item['type'] == 'B':
            processed = item['value'] * 3
            result.append(processed)
        elif item['type'] == 'C':
            processed = item['value'] * 4
            result.append(processed)
        else:
            processed = item['value']
            result.append(processed)
    
    for i in range(len(result)):
        if result[i] > 100:
            result[i] = 100
        elif result[i] < 0:
            result[i] = 0
    
    final = []
    for r in result:
        if r % 2 == 0:
            final.append(r)
    
    return final
''',
    
    'storage_hardcoded_path': '''
storage_path = "D:\\\\ZeroUI\\\\tenant\\\\evidence"
data_file = open(storage_path + "\\\\data.json", "w")
''',
    
    'storage_uppercase_folder': '''
path = "storage/MyFolder/userData"
receipt_path = "evidence/Agent_Receipts"
''',
    
    'receipt_without_signature': '''
import json

receipt = {"id": 123, "action": "commit"}
with open("receipts/data.jsonl", "a") as f:
    f.write(json.dumps(receipt) + "\\n")
''',
    
    'no_timeout': '''
import requests

response = requests.get("https://api.example.com/data")
data = response.json()
''',
    
    'silent_exception': '''
try:
    risky_operation()
except Exception:
    pass
''',
    
    'no_input_validation': '''
def process_user_input(user_data):
    return user_data.upper()

user_input = input("Enter data: ")
result = process_user_input(user_input)
''',
}

