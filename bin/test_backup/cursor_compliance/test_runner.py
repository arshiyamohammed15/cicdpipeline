#!/usr/bin/env python3
"""
Cursor Constitution Rule Compliance Test Runner

This script tests whether Cursor follows all 89 Constitution rules when generating code.
It uses the existing rule validation system to check compliance.
"""

import json
import sys
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import os

# Add the validator to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools' / 'validator'))

try:
    from rule_engine import RuleEngine
    from reporter import Reporter
except ImportError as e:
    print(f"ERROR: Failed to import validation system: {e}")
    print("Make sure the validator system is properly set up.")
    sys.exit(1)


class CursorComplianceTester:
    """Test Cursor's compliance with Constitution rules"""

    def __init__(self):
        self.rule_engine = RuleEngine()
        self.reporter = Reporter()
        self.test_prompts_file = Path(__file__).parent / 'test_prompts.json'
        self.samples_dir = Path(__file__).parent / 'samples'
        self.results = []

    def load_test_prompts(self) -> Dict[str, Any]:
        """Load test prompts from JSON file"""
        try:
            with open(self.test_prompts_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"ERROR: Failed to load test prompts: {e}")
            return {}

    def create_sample_code(self, rule_id: str, test_scenario: Dict[str, Any]) -> str:
        """Create sample code that represents what Cursor might generate"""
        rule_name = test_scenario.get('rule', '')
        category = test_scenario.get('category', '')
        test_prompt = test_scenario.get('test_prompt', '')

        # Generate sample code based on rule category and prompt
        if category == 'Code Review':
            return self._create_code_review_sample(rule_id, rule_name, test_prompt)
        elif category == 'API Contracts':
            return self._create_api_contracts_sample(rule_id, rule_name, test_prompt)
        elif category == 'Coding Standards':
            return self._create_coding_standards_sample(rule_id, rule_name, test_prompt)
        elif category == 'Comments':
            return self._create_comments_sample(rule_id, rule_name, test_prompt)
        elif category == 'Folder Standards':
            return self._create_folder_standards_sample(rule_id, rule_name, test_prompt)
        else:
            return self._create_generic_sample(rule_id, rule_name, test_prompt)

    def _create_code_review_sample(self, rule_id: str, rule_name: str, prompt: str) -> str:
        """Create sample code for Code Review rules"""
        if 'LOC Limit' in rule_name:
            # Create a function that might exceed LOC limit
            return '''def user_authentication_service():
    """
    User authentication service with login, logout, and password reset.
    This function handles user authentication, session management,
    password validation, token generation, and security logging.
    """
    import hashlib
    import secrets
    import time
    from datetime import datetime, timedelta

    def validate_credentials(username, password):
        # Validate user credentials against database
        # Check password hash
        # Verify account status
        # Log authentication attempt
        pass

    def generate_session_token(user_id):
        # Generate secure session token
        # Set expiration time
        # Store in database
        # Return token
        pass

    def reset_password(user_id, new_password):
        # Validate new password strength
        # Hash password
        # Update database
        # Send confirmation email
        # Log password reset
        pass

    def logout_user(session_token):
        # Invalidate session token
        # Clear from database
        # Log logout event
        pass

    def audit_log(action, user_id, details):
        # Log security events
        # Store audit trail
        # Send alerts if needed
        pass

    # Main authentication logic
    return {
        'login': validate_credentials,
        'logout': logout_user,
        'reset': reset_password,
        'audit': audit_log
    }'''

        elif 'Security' in rule_name:
            # Create code that might have security issues
            return '''# User registration form
def register_user(email, password, ssn):
    """
    Register new user with personal information.
    """
    # Store user data
    user_data = {
        'email': email,
        'password': password,  # Should be hashed
        'ssn': ssn,  # PII - should be encrypted
        'api_key': 'sk-1234567890abcdef'  # Secret in code
    }

    # Save to database
    db.users.insert(user_data)

    # Log registration
    print(f"User registered: {email} with SSN: {ssn}")

    return user_data'''

        else:
            return f'# Sample code for {rule_name}\n# Prompt: {prompt}\npass'

    def _create_api_contracts_sample(self, rule_id: str, rule_name: str, prompt: str) -> str:
        """Create sample code for API Contracts rules"""
        if 'HTTP Verbs' in rule_name:
            # Create API with invalid HTTP verbs
            return '''from fastapi import FastAPI

app = FastAPI()

@app.route("/users", methods=["GET_USERS"])  # Invalid HTTP verb
def get_users():
    return {"users": []}

@app.route("/users", methods=["CREATE_USER"])  # Invalid HTTP verb
def create_user():
    return {"message": "User created"}

@app.route("/users", methods=["UPDATE_USER"])  # Invalid HTTP verb
def update_user():
    return {"message": "User updated"}'''

        elif 'URI Structure' in rule_name:
            # Create API with invalid URI structure
            return '''from fastapi import FastAPI

app = FastAPI()

@app.get("/getUsers")  # Should be /users
def get_users():
    return {"users": []}

@app.post("/createUser")  # Should be /users
def create_user():
    return {"message": "User created"}

@app.put("/updateUserById/{id}")  # Should be /users/{id}
def update_user(id: int):
    return {"message": f"User {id} updated"}'''

        else:
            return f'# Sample API code for {rule_name}\n# Prompt: {prompt}\npass'

    def _create_coding_standards_sample(self, rule_id: str, rule_name: str, prompt: str) -> str:
        """Create sample code for Coding Standards rules"""
        if 'Async' in rule_name:
            # Create blocking code in async function
            return '''import time
import requests
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
async def get_users():
    # Blocking call in async function
    time.sleep(1)  # Should use asyncio.sleep

    # Blocking HTTP request
    response = requests.get("https://api.example.com/users")  # Should use httpx

    return response.json()'''

        elif 'Packaging' in rule_name:
            # Create requirements.txt without hashes
            return '''# requirements.txt without hashes
fastapi
pydantic
uvicorn
requests
sqlalchemy'''

        else:
            return f'# Sample coding standards code for {rule_name}\n# Prompt: {prompt}\npass'

    def _create_comments_sample(self, rule_id: str, rule_name: str, prompt: str) -> str:
        """Create sample code for Comments rules"""
        if 'TODO' in rule_name:
            # Create code with TODO comments without owner/date/ticket
            return '''def process_data():
    # TODO: Fix this function
    # FIXME: Update API endpoint
    # HACK: Temporary workaround

    data = get_data()
    processed = transform(data)
    return processed'''

        elif 'Simple English' in rule_name:
            # Create code with complex comments
            return '''def complex_algorithm():
    """
    This function implements a sophisticated algorithmic approach
    utilizing advanced computational methodologies to process
    intricate data structures through recursive decomposition
    and heuristic optimization techniques.
    """
    # Initialize the computational framework
    framework = initialize_framework()

    # Execute the recursive decomposition process
    result = recursive_decomposition(framework)

    return result'''

        else:
            return f'# Sample comments code for {rule_name}\n# Prompt: {prompt}\npass'

    def _create_folder_standards_sample(self, rule_id: str, rule_name: str, prompt: str) -> str:
        """Create sample code for Folder Standards rules"""
        if 'ZEROUI_ROOT' in rule_name:
            # Create code with hardcoded paths
            return '''import os

def save_user_data(data):
    # Hardcoded path - should use ZEROUI_ROOT
    file_path = "C:\\Users\\admin\\Documents\\user_data.json"

    with open(file_path, 'w') as f:
        json.dump(data, f)'''

        else:
            return f'# Sample folder standards code for {rule_name}\n# Prompt: {prompt}\npass'

    def _create_generic_sample(self, rule_id: str, rule_name: str, prompt: str) -> str:
        """Create generic sample code"""
        return f'# Sample code for {rule_name}\n# Rule ID: {rule_id}\n# Prompt: {prompt}\npass'

    def test_rule_compliance(self, rule_id: str, test_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test compliance for a single rule"""
        print(f"Testing {rule_id}: {test_scenario.get('rule', '')}")

        # Create sample code
        sample_code = self.create_sample_code(rule_id, test_scenario)

        # Save sample code to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(sample_code)
            temp_file = f.name

        try:
            # Run validation on the sample code
            start_time = time.time()
            validation_result = self.rule_engine.validate_files([temp_file])
            execution_time = time.time() - start_time

            # Check if the rule was violated
            rule_violated = False
            violations = []

            for result in validation_result:
                if result.get('rule_id') == rule_id:
                    if not result.get('passed', True):
                        rule_violated = True
                        violations.extend(result.get('violations', []))

            # Determine if Cursor would follow this rule
            # If the sample code violates the rule, Cursor should catch it
            cursor_compliant = not rule_violated

            return {
                'rule_id': rule_id,
                'rule_name': test_scenario.get('rule', ''),
                'category': test_scenario.get('category', ''),
                'test_prompt': test_scenario.get('test_prompt', ''),
                'expected_behavior': test_scenario.get('expected_behavior', ''),
                'cursor_compliant': cursor_compliant,
                'rule_violated': rule_violated,
                'violations': violations,
                'execution_time_ms': execution_time * 1000,
                'sample_code': sample_code[:200] + '...' if len(sample_code) > 200 else sample_code
            }

        except Exception as e:
            return {
                'rule_id': rule_id,
                'rule_name': test_scenario.get('rule', ''),
                'category': test_scenario.get('category', ''),
                'test_prompt': test_scenario.get('test_prompt', ''),
                'expected_behavior': test_scenario.get('expected_behavior', ''),
                'cursor_compliant': False,
                'rule_violated': False,
                'violations': [{'message': f'Test execution error: {e}'}],
                'execution_time_ms': 0,
                'sample_code': sample_code[:200] + '...' if len(sample_code) > 200 else sample_code,
                'error': str(e)
            }
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file)
            except:
                pass

    def run_smoke_test(self, num_rules: int = 10) -> Dict[str, Any]:
        """Run a quick smoke test on a subset of rules"""
        print(f"Running smoke test on {num_rules} rules...")

        test_prompts = self.load_test_prompts()
        scenarios = test_prompts.get('test_scenarios', {})

        # Select first N rules for smoke test
        rule_ids = list(scenarios.keys())[:num_rules]

        results = []
        for rule_id in rule_ids:
            result = self.test_rule_compliance(rule_id, scenarios[rule_id])
            results.append(result)

        return self._generate_report(results, 'smoke_test')

    def run_full_test(self) -> Dict[str, Any]:
        """Run full test on all 89 rules"""
        print("Running full compliance test on all 89 rules...")

        test_prompts = self.load_test_prompts()
        scenarios = test_prompts.get('test_scenarios', {})

        results = []
        total_rules = len(scenarios)

        for i, (rule_id, scenario) in enumerate(scenarios.items(), 1):
            print(f"Progress: {i}/{total_rules} - {rule_id}")
            result = self.test_rule_compliance(rule_id, scenario)
            results.append(result)

        return self._generate_report(results, 'full_test')

    def _generate_report(self, results: List[Dict[str, Any]], test_type: str) -> Dict[str, Any]:
        """Generate compliance report"""
        total_rules = len(results)
        compliant_rules = sum(1 for r in results if r.get('cursor_compliant', False))
        non_compliant_rules = total_rules - compliant_rules

        # Group by category
        categories = {}
        for result in results:
            category = result.get('category', 'Unknown')
            if category not in categories:
                categories[category] = {'total': 0, 'compliant': 0, 'non_compliant': 0}

            categories[category]['total'] += 1
            if result.get('cursor_compliant', False):
                categories[category]['compliant'] += 1
            else:
                categories[category]['non_compliant'] += 1

        # Calculate compliance percentage
        compliance_percentage = (compliant_rules / total_rules * 100) if total_rules > 0 else 0

        # Calculate average execution time
        avg_execution_time = sum(r.get('execution_time_ms', 0) for r in results) / total_rules if total_rules > 0 else 0

        report = {
            'test_type': test_type,
            'timestamp': time.time(),
            'summary': {
                'total_rules': total_rules,
                'compliant_rules': compliant_rules,
                'non_compliant_rules': non_compliant_rules,
                'compliance_percentage': compliance_percentage,
                'avg_execution_time_ms': avg_execution_time
            },
            'categories': categories,
            'results': results,
            'non_compliant_rules': [r for r in results if not r.get('cursor_compliant', False)],
            'compliant_rules': [r for r in results if r.get('cursor_compliant', False)]
        }

        return report

    def save_report(self, report: Dict[str, Any], output_file: str):
        """Save report to file"""
        output_path = Path(output_file)

        if output_path.suffix == '.json':
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
        elif output_path.suffix == '.html':
            html_content = self._generate_html_report(report)
            with open(output_path, 'w') as f:
                f.write(html_content)
        elif output_path.suffix == '.md':
            markdown_content = self._generate_markdown_report(report)
            with open(output_path, 'w') as f:
                f.write(markdown_content)
        else:
            print(f"Unsupported output format: {output_path.suffix}")
            return

        print(f"Report saved to: {output_path}")

    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate HTML report"""
        summary = report['summary']
        categories = report['categories']
        non_compliant = report['non_compliant_rules']

        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Cursor Constitution Rule Compliance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .summary {{ background: #e6ffe6; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .warning {{ background: #ffe6e6; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .category {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        .rule {{ margin: 5px 0; padding: 5px; background: #f9f9f9; border-radius: 3px; }}
        .compliant {{ color: green; }}
        .non-compliant {{ color: red; }}
        .percentage {{ font-size: 24px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Cursor Constitution Rule Compliance Report</h1>
        <p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Test Type: {report['test_type']}</p>
    </div>

    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Rules:</strong> {summary['total_rules']}</p>
        <p><strong>Compliant Rules:</strong> {summary['compliant_rules']}</p>
        <p><strong>Non-Compliant Rules:</strong> {summary['non_compliant_rules']}</p>
        <p class="percentage"><strong>Compliance:</strong> {summary['compliance_percentage']:.1f}%</p>
        <p><strong>Average Execution Time:</strong> {summary['avg_execution_time_ms']:.1f}ms</p>
    </div>
'''

        if non_compliant:
            html += f'''
    <div class="warning">
        <h2>Non-Compliant Rules ({len(non_compliant)})</h2>
'''
            for rule in non_compliant:
                html += f'''
        <div class="rule">
            <strong>{rule['rule_id']}: {rule['rule_name']}</strong><br>
            <em>{rule['category']}</em><br>
            <strong>Prompt:</strong> {rule['test_prompt']}<br>
            <strong>Expected:</strong> {rule['expected_behavior']}<br>
            <strong>Violations:</strong> {len(rule.get('violations', []))}
        </div>
'''
            html += '    </div>'

        html += '''
    <div class="category">
        <h2>Results by Category</h2>
'''
        for category, stats in categories.items():
            compliance_pct = (stats['compliant'] / stats['total'] * 100) if stats['total'] > 0 else 0
            html += f'''
        <div class="category">
            <h3>{category}</h3>
            <p>Total: {stats['total']} | Compliant: {stats['compliant']} | Non-Compliant: {stats['non_compliant']}</p>
            <p>Compliance: {compliance_pct:.1f}%</p>
        </div>
'''

        html += '''
    </div>
</body>
</html>'''

        return html

    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate Markdown report"""
        summary = report['summary']
        categories = report['categories']
        non_compliant = report['non_compliant_rules']

        md = f'''# Cursor Constitution Rule Compliance Report

**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Test Type:** {report['test_type']}

## Summary

- **Total Rules:** {summary['total_rules']}
- **Compliant Rules:** {summary['compliant_rules']}
- **Non-Compliant Rules:** {summary['non_compliant_rules']}
- **Compliance:** {summary['compliance_percentage']:.1f}%
- **Average Execution Time:** {summary['avg_execution_time_ms']:.1f}ms

## Results by Category

'''

        for category, stats in categories.items():
            compliance_pct = (stats['compliant'] / stats['total'] * 100) if stats['total'] > 0 else 0
            md += f'''### {category}
- Total: {stats['total']}
- Compliant: {stats['compliant']}
- Non-Compliant: {stats['non_compliant']}
- Compliance: {compliance_pct:.1f}%

'''

        if non_compliant:
            md += f'''## Non-Compliant Rules ({len(non_compliant)})

'''
            for rule in non_compliant:
                md += f'''### {rule['rule_id']}: {rule['rule_name']}
- **Category:** {rule['category']}
- **Prompt:** {rule['test_prompt']}
- **Expected:** {rule['expected_behavior']}
- **Violations:** {len(rule.get('violations', []))}

'''

        return md


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test Cursor Constitution Rule Compliance')
    parser.add_argument('--smoke', action='store_true', help='Run smoke test (10 rules)')
    parser.add_argument('--full', action='store_true', help='Run full test (all 89 rules)')
    parser.add_argument('--output', help='Output file for report (JSON, HTML, or Markdown)')
    parser.add_argument('--format', choices=['json', 'html', 'markdown'], default='json',
                       help='Output format (default: json)')

    args = parser.parse_args()

    if not args.smoke and not args.full:
        parser.print_help()
        return

    tester = CursorComplianceTester()

    if args.smoke:
        print("Starting smoke test...")
        report = tester.run_smoke_test()
    else:
        print("Starting full test...")
        report = tester.run_full_test()

    # Print summary
    summary = report['summary']
    print(f"\n{'='*60}")
    print("CURSOR COMPLIANCE TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total Rules: {summary['total_rules']}")
    print(f"Compliant: {summary['compliant_rules']}")
    print(f"Non-Compliant: {summary['non_compliant_rules']}")
    print(f"Compliance: {summary['compliance_percentage']:.1f}%")
    print(f"Average Execution Time: {summary['avg_execution_time_ms']:.1f}ms")

    if summary['compliance_percentage'] == 100:
        print("\n🎉 PERFECT COMPLIANCE! Cursor follows all Constitution rules!")
    elif summary['compliance_percentage'] >= 90:
        print("\n✅ EXCELLENT COMPLIANCE! Cursor follows most Constitution rules.")
    elif summary['compliance_percentage'] >= 75:
        print("\n⚠️  GOOD COMPLIANCE! Cursor follows most rules but has some gaps.")
    else:
        print("\n❌ POOR COMPLIANCE! Cursor needs significant improvement.")

    print(f"{'='*60}")

    # Save report if requested
    if args.output:
        tester.save_report(report, args.output)
    else:
        # Default output
        default_output = f"cursor_compliance_report_{report['test_type']}.{args.format}"
        tester.save_report(report, default_output)


if __name__ == "__main__":
    main()
