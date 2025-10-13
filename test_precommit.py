#!/usr/bin/env python3
"""
Test the pre-commit hook functionality
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

def test_precommit_hook():
    """Test pre-commit hook"""
    print("Testing Pre-commit Hook...")

    # Check if pre-commit hook exists
    hook_path = Path('.git/hooks/pre-commit')
    if not hook_path.exists():
        print("   INFO: Pre-commit hook not installed yet")
        print("   To install: python tools/hooks/install.py")
        return False

    print(f"   OK: Pre-commit hook exists at {hook_path}")

    # Check hook content
    with open(hook_path, 'r') as f:
        content = f.read()

    if 'pre-commit-validate.py' in content:
        print("   OK: Hook references validation script")
    else:
        print("   WARNING: Hook may not be properly configured")

    return True

def test_validation_script():
    """Test the validation script directly"""
    print("Testing Validation Script...")

    script_path = Path('tools/hooks/pre-commit-validate.py')
    if not script_path.exists():
        print("   ERROR: Pre-commit validation script not found")
        return False

    print(f"   OK: Validation script exists at {script_path}")

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

    return True

def main():
    """Main test function"""
    print("Testing Pre-commit Integration")
    print("=" * 40)

    tests = [
        test_precommit_hook,
        test_validation_script
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
        print("Pre-commit integration tests passed!")
        return 0
    else:
        print("Some pre-commit tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
