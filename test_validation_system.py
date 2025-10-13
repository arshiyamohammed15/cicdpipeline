#!/usr/bin/env python3
"""
Test script for ZeroUI 2.0 Rule Validation System

This script tests the validation system with sample files to demonstrate
how it works and verify all components are functioning correctly.
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add the validator module to the path
sys.path.insert(0, str(Path(__file__).parent / 'tools' / 'validator'))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")

    try:
        from rule_engine import RuleEngine
        print("SUCCESS: RuleEngine imported successfully")
    except ImportError as e:
        print(f"FAILED: Failed to import RuleEngine: {e}")
        return False

    try:
        from reporter import Reporter
        print("SUCCESS: Reporter imported successfully")
    except ImportError as e:
        print(f"FAILED: Failed to import Reporter: {e}")
        return False

    try:
        from validators.security_validator import SecurityValidator
        print("SUCCESS: SecurityValidator imported successfully")
    except ImportError as e:
        print(f"FAILED: Failed to import SecurityValidator: {e}")
        return False

    return True

def test_rules_loading():
    """Test that rules can be loaded from JSON"""
    print("\n🧪 Testing rules loading...")

    try:
        from rule_engine import RuleEngine
        engine = RuleEngine()

        if hasattr(engine, 'rules') and len(engine.rules) > 0:
            print(f"✅ Loaded {len(engine.rules)} rules successfully")
            return True
        else:
            print("❌ No rules loaded")
            return False
    except Exception as e:
        print(f"❌ Failed to load rules: {e}")
        return False

def create_test_files():
    """Create test files with various violations"""
    print("\n🧪 Creating test files...")

    test_files = []

    # Test file 1: Security violation (hardcoded secret)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''
# Test file with security violation
api_key = "sk-1234567890abcdef"
password = "mypassword123"

def hello():
    return "Hello World"
''')
        test_files.append(f.name)
        print(f"✅ Created security test file: {f.name}")

    # Test file 2: API violation (invalid HTTP verb)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''
# Test file with API violation
from fastapi import FastAPI

app = FastAPI()

@app.invalid("/users")  # Invalid HTTP verb
def get_users():
    return {"users": []}
''')
        test_files.append(f.name)
        print(f"✅ Created API test file: {f.name}")

    # Test file 3: Comment violation (missing header)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''
# Missing file header
def hello():
    pass
''')
        test_files.append(f.name)
        print(f"✅ Created comment test file: {f.name}")

    # Test file 4: Logging violation (invalid JSONL)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('''
{"message": "test log entry"}
{"message": "another log entry"
''')  # Invalid JSON (missing closing brace)
        test_files.append(f.name)
        print(f"✅ Created logging test file: {f.name}")

    return test_files

def test_validation():
    """Test the validation system with test files"""
    print("\n🧪 Testing validation system...")

    try:
        from rule_engine import RuleEngine
        from reporter import Reporter

        # Create test files
        test_files = create_test_files()

        # Initialize engine and reporter
        engine = RuleEngine()
        reporter = Reporter()

        print(f"📁 Testing with {len(test_files)} files...")

        # Run validation
        results = engine.validate_files(test_files, validation_scope="changes")

        print(f"📊 Validation completed. Found {len(results)} rule results.")

        # Generate reports
        print("\n📄 Generating reports...")

        # JSON report
        json_report = reporter.generate_report(results, "json")
        print(f"✅ JSON report generated ({len(json_report)} characters)")

        # HTML report
        html_report = reporter.generate_report(results, "html")
        print(f"✅ HTML report generated ({len(html_report)} characters)")

        # Markdown report
        md_report = reporter.generate_report(results, "markdown")
        print(f"✅ Markdown report generated ({len(md_report)} characters)")

        # Show summary
        print("\n📈 Validation Summary:")
        passed_count = sum(1 for r in results if r.get('passed', False))
        failed_count = len(results) - passed_count
        print(f"   Passed: {passed_count}")
        print(f"   Failed: {failed_count}")

        # Show some violations
        violations = []
        for result in results:
            if not result.get('passed', False):
                violations.extend(result.get('violations', []))

        if violations:
            print(f"\n🚫 Found {len(violations)} violations:")
            for i, violation in enumerate(violations[:5]):  # Show first 5
                print(f"   {i+1}. {violation.get('message', 'No message')}")

        # Clean up test files
        for file_path in test_files:
            try:
                os.unlink(file_path)
            except:
                pass

        return True

    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_validators():
    """Test individual validators"""
    print("\n🧪 Testing individual validators...")

    try:
        from validators.security_validator import SecurityValidator
        from validators.api_validator import APIValidator
        from validators.comment_validator import CommentValidator

        # Test Security Validator
        security_validator = SecurityValidator()
        print("✅ SecurityValidator instantiated")

        # Test API Validator
        api_validator = APIValidator()
        print("✅ APIValidator instantiated")

        # Test Comment Validator
        comment_validator = CommentValidator()
        print("✅ CommentValidator instantiated")

        return True

    except Exception as e:
        print(f"❌ Individual validator test failed: {e}")
        return False

def main():
    """Main test function"""
    print("ZeroUI 2.0 Rule Validation System - Test Suite")
    print("=" * 60)

    tests = [
        ("Import Test", test_imports),
        ("Rules Loading Test", test_rules_loading),
        ("Individual Validators Test", test_individual_validators),
        ("Full Validation Test", test_validation),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")

    print(f"\n{'='*60}")
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The validation system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
