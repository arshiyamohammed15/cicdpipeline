#!/usr/bin/env python3
"""
Test the CI/CD validation script
"""

import os
import sys
import subprocess
from pathlib import Path

def test_cicd_script():
    """Test CI/CD script"""
    print("Testing CI/CD Script...")

    script_path = Path('tools/ci/validate-pr.py')
    if not script_path.exists():
        print("   ERROR: CI/CD validation script not found")
        return False

    print(f"   OK: CI/CD script exists at {script_path}")

    # Test script syntax
    try:
        result = subprocess.run([
            sys.executable, '-m', 'py_compile', str(script_path)
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("   OK: Script syntax is valid")
        else:
            print(f"   ERROR: Script syntax error: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ERROR: Failed to test script: {e}")
        return False

    # Test help output
    try:
        result = subprocess.run([
            sys.executable, str(script_path), '--help'
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print("   OK: Script help output works")
        else:
            print(f"   WARNING: Script help failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("   WARNING: Script help timed out")
    except Exception as e:
        print(f"   WARNING: Failed to test help: {e}")

    return True

def test_github_actions():
    """Test GitHub Actions workflow"""
    print("Testing GitHub Actions...")

    workflow_path = Path('.github/workflows/validate-75-rules.yml')
    if not workflow_path.exists():
        print("   ERROR: GitHub Actions workflow not found")
        return False

    print(f"   OK: GitHub Actions workflow exists at {workflow_path}")

    # Check workflow content
    with open(workflow_path, 'r') as f:
        content = f.read()

    if 'validate-pr.py' in content:
        print("   OK: Workflow references validation script")
    else:
        print("   WARNING: Workflow may not be properly configured")

    return True

def main():
    """Main test function"""
    print("Testing CI/CD Integration")
    print("=" * 40)

    tests = [
        test_cicd_script,
        test_github_actions
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
        print("CI/CD integration tests passed!")
        return 0
    else:
        print("Some CI/CD tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
