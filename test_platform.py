"""
Test file for platform rules (42, 43).
"""

# Rule 42 violations: Missing platform features
def process_data(data):
    # No logging
    # No monitoring
    # No configuration
    # No error tracking
    # No health reporting
    return data

def handle_request(request):
    # Missing platform features
    pass

def save_user_data(user_data):
    # No platform integration
    pass

# Rule 43 violations: Inefficient data processing
import time
import requests

def fetch_all_data():
    # Blocking operation
    time.sleep(5)
    response = requests.get('https://api.example.com/data')
    return response.json()

def process_large_dataset():
    # Inefficient processing without streaming
    data = load_all_data()  # Loads everything into memory
    for item in data:
        process_item(item)

def download_files(urls):
    # Blocking operations
    for url in urls:
        response = requests.get(url)
        save_file(response.content)

def validate_user_input():
    # No data quality checks during processing
    user_input = input("Enter data: ")
    return user_input

# Missing performance optimizations
def calculate_statistics(data):
    # No caching, streaming, or async processing
    result = []
    for item in data:
        result.append(complex_calculation(item))
    return result
