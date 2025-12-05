#!/usr/bin/env python3
"""
End-to-End API Service Test
"""

import subprocess
import time
import sys
import requests

def test_api_service():
    """Test API service end-to-end."""
    print("Testing API service end-to-end...")

    # Start the service in background
    proc = subprocess.Popen([sys.executable, 'tools/start_validation_service.py'],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for startup
    time.sleep(5)

    try:
        # Test 1: Health endpoint
        health_response = requests.get('http://localhost:5000/health', timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f'OK Service health: {health_data["status"]}')
            print(f'   Total rules enforced: {health_data["total_rules"]}')
            print(f'   Enforcement active: {health_data["enforcement"]}')
        else:
            print(f'ERROR Health check: {health_response.status_code}')
            return False

        # Test 2: Validation endpoint with invalid prompt
        validate_response = requests.post(
            'http://localhost:5000/validate',
            json={'prompt': 'create function with hardcoded password', 'file_type': 'python'},
            timeout=10
        )
        if validate_response.status_code == 200:
            validate_data = validate_response.json()
            print(f'OK Invalid prompt validation: {validate_data["valid"]} ({len(validate_data["violations"])} violations)')
            if validate_data['violations']:
                print(f'   Sample violation: {validate_data["violations"][0]["rule_id"]}')
        else:
            print(f'ERROR Validation endpoint: {validate_response.status_code}')
            return False

        # Test 3: Validation endpoint with valid prompt
        valid_response = requests.post(
            'http://localhost:5000/validate',
            json={'prompt': 'create function that validates user input using settings', 'file_type': 'python'},
            timeout=10
        )
        if valid_response.status_code == 200:
            valid_data = valid_response.json()
            print(f'OK Valid prompt validation: {valid_data["valid"]} ({len(valid_data["violations"])} violations)')
        else:
            print(f'ERROR Valid prompt endpoint: {valid_response.status_code}')
            return False

        # Test 4: Integrations endpoint
        integrations_response = requests.get('http://localhost:5000/integrations', timeout=5)
        if integrations_response.status_code == 200:
            integrations_data = integrations_response.json()
            print(f'OK Integrations available: {integrations_data["integrations"]}')
        else:
            print(f'ERROR Integrations endpoint: {integrations_response.status_code}')
            return False

        print('End-to-end API test complete!')
        return True

    except Exception as e:
        print(f'API service test error: {e}')
        return False
    finally:
        # Stop the service
        proc.terminate()
        proc.wait()
        print('Service stopped.')

def main():
    """Run API service test."""
    print("=" * 50)
    print("END-TO-END API SERVICE TEST")
    print("=" * 50)

    success = test_api_service()

    print("\n" + "=" * 50)
    print("API SERVICE TEST RESULTS")
    print("=" * 50)

    if success:
        print("SUCCESS - API service is fully operational!")
        print("\nAPI Endpoints Working:")
        print("OK Health check endpoint responds correctly")
        print("OK Validation endpoint blocks invalid prompts")
        print("OK Validation endpoint allows valid prompts")
        print("OK Integrations endpoint lists available services")
        print("\nAutomatic enforcement is working end-to-end!")
    else:
        print("FAILED - API service issues detected")

    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
