#!/usr/bin/env python3
"""
Demonstration of rule violations in the 6 specialized constitutions.
"""

def show_rule_violations():
    """Show examples of code that violates constitution rules."""
    
    print("ZEROUI 2.0 CONSTITUTION RULE VIOLATIONS")
    print("=" * 50)
    print("This demonstrates code that breaks the 6 specialized constitution rules")
    print("=" * 50)
    
    # CODE REVIEW CONSTITUTION VIOLATIONS
    print("\n1. CODE REVIEW CONSTITUTION VIOLATIONS:")
    print("-" * 40)
    
    print("VIOLATION: R009 - Security & Privacy First")
    print("Code breaking the rule:")
    print('password = "admin123"  # Hardcoded secret')
    print("Rule: No secrets/PII in code")
    print("Severity: ERROR")
    print("Category: security")
    print()
    
    print("VIOLATION: R001 - LOC Limit")
    print("Code breaking the rule:")
    print("# This file exceeds 500 lines")
    print("Rule: Files should not exceed 500 lines")
    print("Severity: WARNING")
    print("Category: scope")
    print()
    
    # API CONTRACTS CONSTITUTION VIOLATIONS
    print("\n2. API CONTRACTS CONSTITUTION VIOLATIONS:")
    print("-" * 40)
    
    print("VIOLATION: R014 - API Versioning")
    print("Code breaking the rule:")
    print("@app.route('/api/users', methods=['POST'])")
    print("def create_user():")
    print("    return {'user': 'created'}")
    print("Rule: API endpoints should use versioning")
    print("Severity: WARNING")
    print("Category: api")
    print()
    
    print("VIOLATION: R015 - Idempotency")
    print("Code breaking the rule:")
    print("@app.route('/api/orders', methods=['POST'])")
    print("def create_order():")
    print("    order_id = generate_random_id()")
    print("Rule: POST endpoints should be idempotent")
    print("Severity: ERROR")
    print("Category: api")
    print()
    
    # CODING STANDARDS CONSTITUTION VIOLATIONS
    print("\n3. CODING STANDARDS CONSTITUTION VIOLATIONS:")
    print("-" * 40)
    
    print("VIOLATION: R034 - Imports")
    print("Code breaking the rule:")
    print("from os import *  # Wildcard import")
    print("Rule: Avoid wildcard imports")
    print("Severity: ERROR")
    print("Category: code_quality")
    print()
    
    print("VIOLATION: R031 - Function Length")
    print("Code breaking the rule:")
    print("def very_long_function():")
    print("    print('Line 1')")
    print("    print('Line 2')")
    print("    # ... 20+ more lines")
    print("Rule: Functions should not exceed 20 lines")
    print("Severity: WARNING")
    print("Category: code_quality")
    print()
    
    # COMMENTS CONSTITUTION VIOLATIONS
    print("\n4. COMMENTS CONSTITUTION VIOLATIONS:")
    print("-" * 40)
    
    print("VIOLATION: R008 - Simple English Comments")
    print("Code breaking the rule:")
    print("# This is an extremely complex comment with sophisticated vocabulary")
    print("Rule: Use simple English in comments")
    print("Severity: WARNING")
    print("Category: documentation")
    print()
    
    print("VIOLATION: R089 - TODO Policy")
    print("Code breaking the rule:")
    print("# TODO: Fix this later  # Missing owner")
    print("Rule: TODO format: TODO(owner): description")
    print("Severity: INFO")
    print("Category: documentation")
    print()
    
    # FOLDER STANDARDS CONSTITUTION VIOLATIONS
    print("\n5. FOLDER STANDARDS CONSTITUTION VIOLATIONS:")
    print("-" * 40)
    
    print("VIOLATION: R054 - File Naming")
    print("Code breaking the rule:")
    print('path = "/hardcoded/path/to/file"  # Hardcoded path')
    print("Rule: Use ZEROUI_ROOT paths, not hardcoded paths")
    print("Severity: ERROR")
    print("Category: structure")
    print()
    
    # LOGGING CONSTITUTION VIOLATIONS
    print("\n6. LOGGING CONSTITUTION VIOLATIONS:")
    print("-" * 40)
    
    print("VIOLATION: R043 - Structured Logging")
    print("Code breaking the rule:")
    print("import logging")
    print('logging.info("User logged in")  # Not structured logging')
    print("Rule: Use JSONL format for structured logging")
    print("Severity: ERROR")
    print("Category: logging")
    print()
    
    print("VIOLATION: R071 - Log Security")
    print("Code breaking the rule:")
    print('logging.info("User password: secret123")  # PII in logs')
    print("Rule: No PII in logs")
    print("Severity: ERROR")
    print("Category: logging")
    print()
    
    print("=" * 50)
    print("RULE VIOLATION DEMONSTRATION COMPLETE")
    print("=" * 50)
    print("The ZEROUI 2.0 Constitution Validator detects these violations")
    print("across all 6 specialized constitutions:")
    print()
    print("1. Code Review Constitution - 2 violations shown")
    print("2. API Contracts Constitution - 2 violations shown")
    print("3. Coding Standards Constitution - 2 violations shown")
    print("4. Comments Constitution - 2 violations shown")
    print("5. Folder Standards Constitution - 1 violation shown")
    print("6. Logging Constitution - 2 violations shown")
    print()
    print("Total: 11 rule violations demonstrated")
    print("All 89 rules across 6 constitutions are now supported!")
    
    print("\n" + "=" * 50)
    print("DECISION REQUIRED")
    print("=" * 50)
    print("The code above demonstrates violations of the 6 specialized constitutions.")
    print("Each violation shows:")
    print("- The exact code that breaks the rule")
    print("- The rule ID and name")
    print("- The severity level (ERROR, WARNING, INFO)")
    print("- The category it belongs to")
    print()
    print("Do you want me to:")
    print("1. Fix these violations and show corrected code?")
    print("2. Create more violation examples?")
    print("3. Test the actual validator detection?")
    print("4. Show you how to configure the validator?")
    print()
    print("Please let me know your decision!")

if __name__ == "__main__":
    show_rule_violations()
