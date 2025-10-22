"""
Configuration test data for validator tests.

Contains mock configurations for testing validators.
"""

MOCK_OPENAPI_SPEC = """
openapi: 3.1.0
info:
  title: Test API
  version: 1.0.0
paths:
  /v1/users:
    get:
      summary: Get users
      parameters:
        - name: Idempotency-Key
          in: header
          schema:
            type: string
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
              example:
                users: []
        '429':
          description: Rate limit exceeded
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
  schemas:
    ErrorResponse:
      type: object
      properties:
        code:
          type: string
        message:
          type: string
"""

INVALID_OPENAPI_SPEC = """
openapi: 2.0
info:
  title: Test API
  version: 1.0.0
paths:
  /users:
    get:
      summary: Get users
      responses:
        '200':
          description: Success
"""

MOCK_CONFIG = {
    "category": "test",
    "priority": "high",
    "rules": [1, 2, 3],
    "patterns": {
        "test_pattern": {
            "regex": r"test_\w+",
            "severity": "warning",
            "message": "Test pattern detected"
        }
    }
}

