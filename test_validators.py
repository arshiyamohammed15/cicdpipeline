#!/usr/bin/env python3
"""
Test individual validators with sample files
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the validator module to the path
sys.path.insert(0, str(Path(__file__).parent / 'tools' / 'validator'))

def test_security_validator():
    """Test security validator with sample files"""
    print("Testing Security Validator...")

    try:
        from validators.security_validator import SecurityValidator
        validator = SecurityValidator()

        # Create test file with security violation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
# Test file with security violations
api_key = "sk-1234567890abcdef"
password = "mypassword123"
secret_token = "secret123"

def hello():
    return "Hello World"
''')
            test_file = f.name

        # Test the validator
        result = validator.validate_no_secrets_pii([test_file])

        print(f"   Security validation result: {'PASSED' if result['passed'] else 'FAILED'}")
        if not result['passed']:
            print(f"   Found {len(result['violations'])} violations:")
            for violation in result['violations'][:3]:  # Show first 3
                print(f"      - {violation.get('message', 'No message')}")

        # Clean up
        os.unlink(test_file)
        return True

    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_api_validator():
    """Test API validator with sample files"""
    print("Testing API Validator...")

    try:
        from validators.api_validator import APIValidator
        validator = APIValidator()

        # Create test file with API violation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
# Test file with API violations
from fastapi import FastAPI

app = FastAPI()

@app.invalid("/users")  # Invalid HTTP verb
def get_users():
    return {"users": []}

@app.get("/v1/user_profiles")  # Invalid URI (snake_case)
def get_user_profiles():
    return {"profiles": []}
''')
            test_file = f.name

        # Test the validator
        result = validator.validate_http_verbs([test_file])

        print(f"   HTTP verbs validation: {'PASSED' if result['passed'] else 'FAILED'}")
        if not result['passed']:
            print(f"   Found {len(result['violations'])} violations:")
            for violation in result['violations'][:3]:  # Show first 3
                print(f"      - {violation.get('message', 'No message')}")

        # Clean up
        os.unlink(test_file)
        return True

    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_comment_validator():
    """Test comment validator with sample files"""
    print("Testing Comment Validator...")

    try:
        from validators.comment_validator import CommentValidator
        validator = CommentValidator()

        # Create test file with comment violations
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
# Missing file header
def hello():
    # This is a very long comment that exceeds the twenty word limit and should be flagged by the validator
    return "Hello World"
''')
            test_file = f.name

        # Test the validator
        result = validator.validate_file_headers([test_file])

        print(f"   File headers validation: {'PASSED' if result['passed'] else 'FAILED'}")
        if not result['passed']:
            print(f"   Found {len(result['violations'])} violations:")
            for violation in result['violations'][:3]:  # Show first 3
                print(f"      - {violation.get('message', 'No message')}")

        # Clean up
        os.unlink(test_file)
        return True

    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def main():
    """Main test function"""
    print("Testing Individual Validators")
    print("=" * 40)

    tests = [
        test_security_validator,
        test_api_validator,
        test_comment_validator
    ]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
                print("   SUCCESS")
            else:
                print("   FAILED")
        except Exception as e:
            print(f"   ERROR: {e}")
        print()

    print(f"Results: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("All validator tests passed!")
        return 0
    else:
        print("Some validator tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
