#!/usr/bin/env python3
"""
Test script to validate commit consistency across different methods.
This file intentionally has formatting issues to test pre-commit hook behavior.

Testing Cursor Agent method with formatting issues.
"""

def   test_function   (   ):
    """This function has bad formatting to test pre-commit hooks"""
    x=1+2
    print("Hello World")
    return    x

if __name__ == "__main__":
    result = test_function()
    print(f"Result: {result}")
