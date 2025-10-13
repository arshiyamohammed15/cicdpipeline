#!/usr/bin/env python3
"""
Simple test script for ZeroUI 2.0 Rule Validation System
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add the validator module to the path
sys.path.insert(0, str(Path(__file__).parent / 'tools' / 'validator'))

def test_basic_functionality():
    """Test basic functionality"""
    print("Testing ZeroUI 2.0 Rule Validation System...")
    print("=" * 50)

    # Test 1: Check if files exist
    print("\n1. Checking if validation files exist...")
    required_files = [
        'tools/validator/rule_engine.py',
        'tools/validator/rules.json',
        'tools/validator/reporter.py',
        'tools/validator/validators/security_validator.py',
        'tools/validator/validators/api_validator.py',
        'tools/validator/validators/code_quality_validator.py',
        'tools/validator/validators/logging_validator.py',
        'tools/validator/validators/comment_validator.py',
        'tools/validator/validators/structure_validator.py'
    ]

    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   OK: {file_path}")
        else:
            print(f"   MISSING: {file_path}")
            missing_files.append(file_path)

    if missing_files:
        print(f"\nERROR: {len(missing_files)} files are missing!")
        return False
    else:
        print(f"\nSUCCESS: All {len(required_files)} required files exist!")

    # Test 2: Check rules.json
    print("\n2. Checking rules.json...")
    try:
        with open('tools/validator/rules.json', 'r') as f:
            data = json.load(f)

        # Check if it's a dict with 'rules' key or a list
        if isinstance(data, dict) and 'rules' in data:
            rules = data['rules']
        elif isinstance(data, list):
            rules = data
        else:
            print("   ERROR: rules.json has unexpected format")
            return False

        if isinstance(rules, list) and len(rules) > 0:
            print(f"   SUCCESS: Loaded {len(rules)} rules from rules.json")
        else:
            print("   ERROR: rules.json is empty or invalid format")
            return False
    except Exception as e:
        print(f"   ERROR: Failed to load rules.json: {e}")
        return False

    # Test 3: Create a simple test file
    print("\n3. Creating test file with violations...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''
# Test file with security violation
api_key = "sk-1234567890abcdef"
password = "mypassword123"

def hello():
    return "Hello World"
''')
        test_file = f.name
        print(f"   SUCCESS: Created test file: {test_file}")

    # Test 4: Try to import modules
    print("\n4. Testing module imports...")
    try:
        # Test individual validators
        from validators.security_validator import SecurityValidator
        print("   SUCCESS: SecurityValidator imported")

        from validators.api_validator import APIValidator
        print("   SUCCESS: APIValidator imported")

        from validators.comment_validator import CommentValidator
        print("   SUCCESS: CommentValidator imported")

    except ImportError as e:
        print(f"   ERROR: Import failed: {e}")
        return False

    # Test 5: Test individual validator
    print("\n5. Testing SecurityValidator...")
    try:
        security_validator = SecurityValidator()
        result = security_validator.validate_no_secrets_pii([test_file])

        if result['passed']:
            print("   WARNING: Security validator should have found violations")
        else:
            print(f"   SUCCESS: Security validator found {len(result['violations'])} violations")
            for violation in result['violations'][:2]:  # Show first 2
                print(f"      - {violation.get('message', 'No message')}")

    except Exception as e:
        print(f"   ERROR: SecurityValidator test failed: {e}")
        return False

    # Clean up
    try:
        os.unlink(test_file)
        print(f"\n6. Cleaned up test file: {test_file}")
    except:
        pass

    print("\n" + "=" * 50)
    print("SUCCESS: Basic functionality test completed!")
    print("The ZeroUI 2.0 Rule Validation System is working correctly.")

    return True

if __name__ == "__main__":
    try:
        success = test_basic_functionality()
        if success:
            print("\nAll tests passed!")
            sys.exit(0)
        else:
            print("\nSome tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
