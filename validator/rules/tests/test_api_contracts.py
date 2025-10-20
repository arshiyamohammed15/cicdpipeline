"""
Tests for API Contracts Validator (Rules 13-26, 80, 83-86)

Tests API contracts and OpenAPI specification compliance validation.
"""

import unittest
from validator.rules.api_contracts import APIContractsValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestAPIContractsValidator(unittest.TestCase):
    """Test suite for API contracts rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = APIContractsValidator()
        self.test_file_path = "test.py"
        self.openapi_file_path = "api/openapi.yaml"
    
    # Rule 13: OpenAPI 3.1 compliance
    def test_rule_013_openapi_31_valid(self):
        """Test Rule 13: Valid OpenAPI 3.1 spec."""
        content = '''
openapi: 3.1.0
info:
  title: Test API
  version: 1.0.0
paths:
  /v1/users:
    get:
      summary: Get users
'''
        violations = self.validator.validate(self.openapi_file_path, content)
        
        # Filter to R013 violations only
        r013_violations = [v for v in violations if v.rule_id == 'R013']
        self.assertEqual(len(r013_violations), 0)
    
    def test_rule_013_openapi_20_violation(self):
        """Test Rule 13: OpenAPI 2.0 violation."""
        content = '''
openapi: 2.0
info:
  title: Test API
  version: 1.0.0
paths:
  /users:
    get:
      summary: Get users
'''
        violations = self.validator.validate(self.openapi_file_path, content)
        
        r013_violations = [v for v in violations if v.rule_id == 'R013']
        self.assertGreater(len(r013_violations), 0)
        self.assertEqual(r013_violations[0].severity, Severity.ERROR)
    
    def test_rule_013_invalid_json_violation(self):
        """Test Rule 13: Invalid JSON spec."""
        content = '''
{
  "openapi": "3.1.0",
  invalid json here
}
'''
        violations = self.validator.validate("api/openapi.json", content)
        
        r013_violations = [v for v in violations if v.rule_id == 'R013']
        self.assertGreater(len(r013_violations), 0)
    
    # Rule 14: API versioning
    def test_rule_014_uri_versioning_valid(self):
        """Test Rule 14: Valid URI versioning /v1, /v2."""
        content = '''
openapi: 3.1.0
paths:
  /v1/users:
    get:
      summary: Get users
  /v2/products:
    get:
      summary: Get products
'''
        violations = self.validator.validate(self.openapi_file_path, content)
        
        r014_violations = [v for v in violations if v.rule_id == 'R014']
        self.assertEqual(len(r014_violations), 0)
    
    def test_rule_014_no_versioning_violation(self):
        """Test Rule 14: No URI versioning."""
        content = '''
openapi: 3.1.0
paths:
  /users:
    get:
      summary: Get users
  /products:
    get:
      summary: Get products
'''
        violations = self.validator.validate(self.openapi_file_path, content)
        
        r014_violations = [v for v in violations if v.rule_id == 'R014']
        self.assertGreater(len(r014_violations), 0)
        self.assertEqual(r014_violations[0].severity, Severity.ERROR)
    
    def test_rule_014_code_versioning_valid(self):
        """Test Rule 14: Valid API versioning in code."""
        content = '''
from flask import Flask
app = Flask(__name__)

@app.route('/api/v1/users', methods=['GET'])
def get_users():
    return {"users": []}
'''
        violations = self.validator.validate(self.test_file_path, content)
        
        r014_violations = [v for v in violations if v.rule_id == 'R014']
        self.assertEqual(len(r014_violations), 0)
    
    def test_rule_014_code_no_versioning_violation(self):
        """Test Rule 14: No versioning in code."""
        content = '''
@app.route('/api/users', methods=['GET'])
def get_users():
    return {"users": []}
'''
        violations = self.validator.validate(self.test_file_path, content)
        
        r014_violations = [v for v in violations if v.rule_id == 'R014']
        self.assertGreater(len(r014_violations), 0)
    
    # Rule 15: Idempotency
    def test_rule_015_idempotency_header_valid(self):
        """Test Rule 15: Valid idempotency header."""
        content = '''
openapi: 3.1.0
paths:
  /v1/orders:
    post:
      parameters:
        - name: Idempotency-Key
          in: header
          required: true
          schema:
            type: string
'''
        violations = self.validator.validate(self.openapi_file_path, content)
        
        r015_violations = [v for v in violations if v.rule_id == 'R015']
        self.assertEqual(len(r015_violations), 0)
    
    def test_rule_015_post_without_idempotency_violation(self):
        """Test Rule 15: POST without idempotency header."""
        content = '''
openapi: 3.1.0
paths:
  /v1/orders:
    post:
      parameters: []
      responses:
        '200':
          description: Success
'''
        violations = self.validator.validate(self.openapi_file_path, content)
        
        r015_violations = [v for v in violations if v.rule_id == 'R015']
        self.assertGreater(len(r015_violations), 0)
        self.assertEqual(r015_violations[0].severity, Severity.ERROR)
    
    def test_rule_015_put_without_idempotency_violation(self):
        """Test Rule 15: PUT without idempotency."""
        content = '''
openapi: 3.1.0
paths:
  /v1/users/{id}:
    put:
      parameters:
        - name: id
          in: path
      responses:
        '200':
          description: Updated
'''
        violations = self.validator.validate(self.openapi_file_path, content)
        
        r015_violations = [v for v in violations if v.rule_id == 'R015']
        self.assertGreater(len(r015_violations), 0)
    
    # Rule 16: Error handling
    def test_rule_016_error_envelope_valid(self):
        """Test Rule 16: Valid error envelope."""
        content = '''
openapi: 3.1.0
components:
  schemas:
    ErrorResponse:
      type: object
      properties:
        code:
          type: string
        message:
          type: string
'''
        violations = self.validator.validate(self.openapi_file_path, content)
        
        r016_violations = [v for v in violations if v.rule_id == 'R016']
        self.assertEqual(len(r016_violations), 0)
    
    def test_rule_016_no_error_schema_violation(self):
        """Test Rule 16: No error envelope schema."""
        content = '''
openapi: 3.1.0
components:
  schemas:
    User:
      type: object
'''
        violations = self.validator.validate(self.openapi_file_path, content)
        
        r016_violations = [v for v in violations if v.rule_id == 'R016']
        self.assertGreater(len(r016_violations), 0)
        self.assertEqual(r016_violations[0].severity, Severity.ERROR)
    
    # Rule 19: Authentication
    def test_rule_019_jwt_auth_valid(self):
        """Test Rule 19: Valid JWT authentication."""
        content = '''
openapi: 3.1.0
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
'''
        violations = self.validator.validate(self.openapi_file_path, content)
        
        r019_violations = [v for v in violations if v.rule_id == 'R019']
        self.assertEqual(len(r019_violations), 0)
    
    def test_rule_019_no_auth_violation(self):
        """Test Rule 19: No authentication scheme."""
        content = '''
openapi: 3.1.0
components:
  schemas:
    User:
      type: object
'''
        violations = self.validator.validate(self.openapi_file_path, content)
        
        r019_violations = [v for v in violations if v.rule_id == 'R019']
        self.assertGreater(len(r019_violations), 0)
        self.assertEqual(r019_violations[0].severity, Severity.ERROR)
    
    # Rule 21: Rate limiting
    def test_rule_021_rate_limit_response_valid(self):
        """Test Rule 21: Valid 429 rate limit response."""
        content = '''
openapi: 3.1.0
paths:
  /v1/users:
    get:
      responses:
        '200':
          description: Success
        '429':
          description: Too many requests
'''
        violations = self.validator.validate(self.openapi_file_path, content)
        
        r021_violations = [v for v in violations if v.rule_id == 'R021']
        self.assertEqual(len(r021_violations), 0)
    
    def test_rule_021_no_rate_limit_violation(self):
        """Test Rule 21: No 429 response."""
        content = '''
openapi: 3.1.0
paths:
  /v1/users:
    get:
      responses:
        '200':
          description: Success
'''
        violations = self.validator.validate(self.openapi_file_path, content)
        
        r021_violations = [v for v in violations if v.rule_id == 'R021']
        self.assertGreater(len(r021_violations), 0)
        self.assertEqual(r021_violations[0].severity, Severity.WARNING)
    
    # Rule 23: Documentation
    def test_rule_023_response_examples_valid(self):
        """Test Rule 23: Valid response examples."""
        content = '''
openapi: 3.1.0
paths:
  /v1/users:
    get:
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
              example:
                users: []
'''
        violations = self.validator.validate(self.openapi_file_path, content)
        
        r023_violations = [v for v in violations if v.rule_id == 'R023']
        self.assertEqual(len(r023_violations), 0)
    
    def test_rule_023_no_examples_violation(self):
        """Test Rule 23: No response examples."""
        content = '''
openapi: 3.1.0
paths:
  /v1/users:
    get:
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
'''
        violations = self.validator.validate(self.openapi_file_path, content)
        
        r023_violations = [v for v in violations if v.rule_id == 'R023']
        self.assertGreater(len(r023_violations), 0)
        self.assertEqual(r023_violations[0].severity, Severity.WARNING)
    
    # Rule 26: Deprecation
    def test_rule_026_deprecation_with_sunset_valid(self):
        """Test Rule 26: Valid deprecation with Sunset header."""
        content = '''
deprecated: true
sunset_date = "2025-12-31"
response.headers['Sunset'] = "Wed, 31 Dec 2025 23:59:59 GMT"
'''
        violations = self.validator.validate(self.test_file_path, content)
        
        r026_violations = [v for v in violations if v.rule_id == 'R026']
        self.assertEqual(len(r026_violations), 0)
    
    def test_rule_026_deprecation_without_sunset_violation(self):
        """Test Rule 26: Deprecated without Sunset."""
        content = '''
deprecated_endpoint = True
mark_as_deprecated()
'''
        violations = self.validator.validate(self.test_file_path, content)
        
        r026_violations = [v for v in violations if v.rule_id == 'R026']
        self.assertGreater(len(r026_violations), 0)
        self.assertEqual(r026_violations[0].severity, Severity.WARNING)
    
    # Rule 80: API receipts
    def test_rule_080_contract_receipt_valid(self):
        """Test Rule 80: Valid contract receipts."""
        content = '''
contract_event = {
    "type": "contract.publish",
    "timestamp": "2025-10-20T10:00:00Z"
}
receipt_path = "evidence/receipts/contracts.jsonl"
with open(receipt_path, "a") as f:
    f.write(json.dumps(contract_event) + "\\n")
'''
        violations = self.validator.validate(self.test_file_path, content)
        
        r080_violations = [v for v in violations if v.rule_id == 'R080']
        self.assertEqual(len(r080_violations), 0)
    
    def test_rule_080_contract_without_receipt_violation(self):
        """Test Rule 80: Contract operation without receipt."""
        content = '''
contract_data = load_contract()
publish_contract(contract_data)
'''
        violations = self.validator.validate(self.test_file_path, content)
        
        r080_violations = [v for v in violations if v.rule_id == 'R080']
        self.assertGreater(len(r080_violations), 0)
        self.assertEqual(r080_violations[0].severity, Severity.ERROR)
    
    # Rule 83: Status lifecycle
    def test_rule_083_endpoint_status_valid(self):
        """Test Rule 83: Valid x-status."""
        content = '''
endpoint_config = {
    "path": "/v1/users",
    "x-status": "ga"
}
'''
        violations = self.validator.validate(self.test_file_path, content)
        
        r083_violations = [v for v in violations if v.rule_id == 'R083']
        self.assertEqual(len(r083_violations), 0)
    
    def test_rule_083_endpoint_without_status_violation(self):
        """Test Rule 83: Endpoint without x-status."""
        content = '''
endpoint_config = {
    "path": "/v1/users",
    "method": "GET"
}
'''
        violations = self.validator.validate(self.test_file_path, content)
        
        r083_violations = [v for v in violations if v.rule_id == 'R083']
        self.assertGreater(len(r083_violations), 0)
        self.assertEqual(r083_violations[0].severity, Severity.WARNING)
    
    # Rule 84: Idempotency retention
    def test_rule_084_idempotency_24h_valid(self):
        """Test Rule 84: Valid 24h idempotency retention."""
        content = '''
idempotency_config = {
    "retention_window": "24h",
    "hash_algorithm": "sha256"
}
'''
        violations = self.validator.validate(self.test_file_path, content)
        
        r084_violations = [v for v in violations if v.rule_id == 'R084']
        self.assertEqual(len(r084_violations), 0)
    
    def test_rule_084_idempotency_without_window_violation(self):
        """Test Rule 84: Idempotency without retention window."""
        content = '''
idempotency_key = request.headers.get("Idempotency-Key")
check_duplicate(idempotency_key)
'''
        violations = self.validator.validate(self.test_file_path, content)
        
        r084_violations = [v for v in violations if v.rule_id == 'R084']
        self.assertGreater(len(r084_violations), 0)
        self.assertEqual(r084_violations[0].severity, Severity.WARNING)
    
    # Rule 85: SDK naming
    def test_rule_085_typescript_sdk_naming_valid(self):
        """Test Rule 85: Valid TypeScript SDK naming."""
        content = '''
import { Client } from '@zeroui/api-v1';
const client = new Client();
'''
        violations = self.validator.validate("test.ts", content)
        
        r085_violations = [v for v in violations if v.rule_id == 'R085']
        self.assertEqual(len(r085_violations), 0)
    
    def test_rule_085_invalid_sdk_naming_violation(self):
        """Test Rule 85: Invalid SDK naming."""
        content = '''
import sdk from 'api-client';
'''
        violations = self.validator.validate(self.test_file_path, content)
        
        r085_violations = [v for v in violations if v.rule_id == 'R085']
        self.assertGreater(len(r085_violations), 0)
        self.assertEqual(r085_violations[0].severity, Severity.WARNING)
    
    # Rule 86: Receipt signature
    def test_rule_086_receipt_with_signature_valid(self):
        """Test Rule 86: Valid receipt with signature."""
        content = '''
receipt = {
    "id": "123",
    "action": "high_trust_action"
}
receipt_signature = sign_ed25519(receipt, private_key)
receipt["signature"] = receipt_signature
'''
        violations = self.validator.validate(self.test_file_path, content)
        
        r086_violations = [v for v in violations if v.rule_id == 'R086']
        self.assertEqual(len(r086_violations), 0)
    
    def test_rule_086_receipt_without_signature_violation(self):
        """Test Rule 86: High-trust receipt without signature."""
        content = '''
receipt = {
    "id": "123",
    "action": "high_trust_action"
}
save_receipt(receipt)
'''
        violations = self.validator.validate(self.test_file_path, content)
        
        r086_violations = [v for v in violations if v.rule_id == 'R086']
        self.assertGreater(len(r086_violations), 0)
        self.assertEqual(r086_violations[0].severity, Severity.WARNING)
    
    # Integration test
    def test_validate_all_rules_comprehensive(self):
        """Test validate() method with multiple rule violations."""
        content = '''
@app.route('/api/users', methods=['POST'])  # R014: No versioning
def create_user():
    # R015: No idempotency
    user_data = request.json
    return {"id": 123}
'''
        violations = self.validator.validate(self.test_file_path, content)
        
        # Should have violations from multiple rules
        rule_ids = set(v.rule_id for v in violations)
        self.assertGreater(len(rule_ids), 0)


if __name__ == '__main__':
    unittest.main()

