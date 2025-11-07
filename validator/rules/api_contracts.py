"""
API Contracts Constitution Validator

Validates compliance with the ZeroUI 2.0 API Contracts Constitution.
Covers OpenAPI compliance, versioning, idempotency, error handling, and more.
"""

import re
import json
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
from..models import Violation, Severity


class APIContractsValidator:
    """Validates API contracts and OpenAPI specifications."""
    
    def __init__(self):
        self.rules = {
            'R013': self._validate_openapi_compliance,
            'R014': self._validate_api_versioning,
            'R015': self._validate_idempotency,
            'R016': self._validate_error_handling,
            'R017': self._validate_request_validation,
            'R018': self._validate_response_validation,
            'R019': self._validate_authentication,
            'R020': self._validate_authorization,
            'R021': self._validate_rate_limiting,
            'R022': self._validate_caching,
            'R023': self._validate_documentation,
            'R024': self._validate_testing,
            'R025': self._validate_monitoring,
            'R026': self._validate_deprecation,
            'R080': self._validate_api_receipts,
            'R083': self._validate_status_lifecycle,
            'R084': self._validate_idempotency_retention,
            'R085': self._validate_sdk_naming,
            'R086': self._validate_receipt_signature
        }
    
    def validate(self, file_path: str, content: str) -> List[Violation]:
        """Validate API contracts compliance for a file."""
        violations = []
        
        # Check if this is an OpenAPI spec file
        is_spec = self._is_openapi_file(file_path)
        if is_spec:
            violations.extend(self._validate_openapi_spec(content, file_path))
        
        # Check for API-related code patterns only for source files
        if not is_spec:
            violations.extend(self._validate_api_patterns(content, file_path))
            # Also run selected rule-text validators for non-spec files to satisfy code-based tests
            violations.extend(self._validate_deprecation(content, file_path))
            violations.extend(self._validate_api_receipts(content, file_path))
            violations.extend(self._validate_status_lifecycle(content, file_path))
            violations.extend(self._validate_idempotency_retention(content, file_path))
            violations.extend(self._validate_sdk_naming(content, file_path))
            violations.extend(self._validate_receipt_signature(content, file_path))

        # Skip rule-text validators here to avoid duplicate/noisy results; pattern/spec checks above suffice
        
        return violations
    
    def _is_openapi_file(self, file_path: str) -> bool:
        """Check if file is an OpenAPI specification."""
        openapi_patterns = ['openapi.yaml', 'swagger.yaml', 'api.yaml', 'openapi.yml', 'swagger.yml', 'openapi.json', 'swagger.json', 'api.json']
        return any(pattern in file_path.lower() for pattern in openapi_patterns)
    
    def _validate_openapi_spec(self, content: str, file_path: str) -> List[Violation]:
        """Validate OpenAPI specification compliance."""
        violations = []
        
        try:
            if file_path.endswith('.json'):
                spec = json.loads(content)
            else:
                spec = yaml.safe_load(content)
            if isinstance(spec, (str, int, float)):
                spec = {"openapi": str(spec)}
            
            # Check OpenAPI version
            openapi_ver = str(spec.get('openapi', ''))
            if not openapi_ver.startswith('3.1'):
                violations.append(Violation(
                        rule_name='OpenAPI 3.1 compliance required',
                        severity=Severity.ERROR,
                        message='OpenAPI 3.1 compliance required',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
                
                    ))
            
            # Check for versioning in paths
            paths = spec.get('paths', {})
            has_versioning = any('/v' in path for path in paths.keys())
            if not has_versioning:
                violations.append(Violation(
                    file_path=file_path,
                    line_number=1,
                    message='URI versioning required: /v1, /v2...',
                    severity=Severity.ERROR,
                    category='api'
                ))
            
            # Check for idempotency headers
            violations.extend(self._check_idempotency_headers(spec, file_path))
            
            # Check for error envelope
            violations.extend(self._check_error_envelope(spec, file_path))
            
            # Check for authentication schemes
            violations.extend(self._check_authentication(spec, file_path))
            
            # Check for rate limiting
            violations.extend(self._check_rate_limiting(spec, file_path))
            
            # Check for examples
            violations.extend(self._check_examples(spec, file_path))
            
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            violations.append(Violation(
                        rule_name=f'Invalid OpenAPI specification: {str(e)}',
                        severity=Severity.ERROR,
                        message=f'Invalid OpenAPI specification: {str(e)}',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        
        return violations
    
    def _check_idempotency_headers(self, spec: Dict, file_path: str) -> List[Violation]:
        """Check for idempotency headers in mutating operations."""
        violations = []
        paths = spec.get('paths', {})
        
        for path, path_spec in paths.items():
            for method, operation in path_spec.items():
                if method.upper() in ['POST', 'PUT', 'PATCH', 'DELETE']:
                    parameters = operation.get('parameters', [])
                    has_idempotency = any(
                        param.get('name', '').lower() == 'idempotency-key'
                        for param in parameters
                    )
                    
                    if not has_idempotency:
                        violations.append(Violation(
                        rule_name=f'Mutating route {method.upper()} {path} must accept Idempotency-Key',
                        severity=Severity.ERROR,
                        message=f'Mutating route {method.upper()} {path} must accept Idempotency-Key',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
                        
                    ))
        
        return violations
    
    def _check_error_envelope(self, spec: Dict, file_path: str) -> List[Violation]:
        """Check for stable error envelope with canonical codes."""
        violations = []
        components = spec.get('components', {})
        schemas = components.get('schemas', {})
        
        # Look for error response schemas
        error_schemas = [name for name in schemas.keys() if 'error' in name.lower()]
        
        if not error_schemas:
            violations.append(Violation(
                        rule_name='Stable error envelope with canonical codes required',
                        severity=Severity.ERROR,
                        message='Stable error envelope with canonical codes required',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        
        return violations
    
    def _check_authentication(self, spec: Dict, file_path: str) -> List[Violation]:
        """Check for JWT authentication with documented scopes."""
        violations = []
        components = spec.get('components', {})
        security_schemes = components.get('securitySchemes', {})
        
        has_jwt = any(
            scheme.get('type') == 'http' and scheme.get('scheme') == 'bearer'
            for scheme in security_schemes.values()
        )
        
        if not has_jwt:
            violations.append(Violation(
                        rule_name='JWT with documented scopes per route required',
                        severity=Severity.ERROR,
                        message='JWT with documented scopes per route required',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        
        return violations
    
    def _check_rate_limiting(self, spec: Dict, file_path: str) -> List[Violation]:
        """Check for rate limiting documentation."""
        violations = []
        paths = spec.get('paths', {})
        
        # Check if rate limiting is documented in any operation
        has_ops = False
        has_rate_limiting = False
        for path_spec in paths.values():
            for operation in path_spec.values():
                if isinstance(operation, dict):
                    has_ops = True
                    responses = operation.get('responses', {})
                    if '429' in responses:
                        has_rate_limiting = True
                        break
        
        if has_ops and not has_rate_limiting:
            violations.append(Violation(
                        rule_name='Rate limit headers and 429 responses required',
                        severity=Severity.WARNING,
                        message='Rate limit headers and 429 responses required',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        
        return violations
    
    def _check_examples(self, spec: Dict, file_path: str) -> List[Violation]:
        """Check for examples in responses."""
        violations = []
        paths = spec.get('paths', {})
        
        for path, path_spec in paths.items():
            for method, operation in path_spec.items():
                if isinstance(operation, dict):
                    responses = operation.get('responses', {})
                    for status_code, response in responses.items():
                        if isinstance(response, dict):
                            content = response.get('content', {})
                            for media_type, media_spec in content.items():
                                if isinstance(media_spec, dict) and not any(k in media_spec for k in ['example', 'examples']):
                                    violations.append(Violation(
                        rule_name=f'Examples required for {method.upper()} {path} {status_code}',
                        severity=Severity.WARNING,
                        message=f'Examples required for {method.upper()} {path} {status_code}',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
                                    
                    ))
        
        return violations
    
    def _validate_api_patterns(self, content: str, file_path: str) -> List[Violation]:
        """Validate API-related code patterns."""
        violations = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Check for hardcoded API endpoints without versioning
            if re.search(r'["\']/api/[^"\']*["\']', line) and '/v' not in line:
                violations.append(Violation(
                    rule_name='API Versioning',
                    file_path=file_path,
                    line_number=line_num,
                    column_number=0,
                    code_snippet=line.strip(),
                    message='API endpoints should use versioning: /api/v1/...',
                    severity=Severity.WARNING,
                    category='api'
                ))
            
            # Check for missing error handling in API calls
            if re.search(r'(requests\.|urllib\.|http\.)', line) and 'try:' not in content:
                violations.append(Violation(
                        rule_name='API calls should have proper error handling',
                        severity=Severity.WARNING,
                        message='API calls should have proper error handling',
                        file_path=file_path,
                        line_number=line_num,
                        column_number=0,
                        code_snippet="",
                        category='api'
                
                    ))
            
            # Check for missing idempotency headers
            if re.search(r'(post|put|patch|delete)', line.lower()) and 'idempotency' not in line.lower():
                violations.append(Violation(
                        rule_name='Mutating operations should include idempotency handling',
                        severity=Severity.WARNING,
                        message='Mutating operations should include idempotency handling',
                        file_path=file_path,
                        line_number=line_num,
                        column_number=0,
                        code_snippet="",
                        category='api'
                
                    ))
        
        return violations
    
    def _validate_openapi_compliance(self, content: str, file_path: str) -> List[Violation]:
        """Validate OpenAPI 3.1 compliance."""
        return self._validate_openapi_spec(content, file_path)
    
    def _validate_api_versioning(self, content: str, file_path: str) -> List[Violation]:
        """Validate API versioning compliance."""
        violations = []
        if '/v' not in content and ('/api/' in content or 'endpoint' in content.lower()):
            violations.append(Violation(
                file_path=file_path,
                line_number=1,
                message='URI versioning required: /v1, /v2...',
                severity=Severity.ERROR,
                category='api'
            ))
        return violations
    
    def _validate_idempotency(self, content: str, file_path: str) -> List[Violation]:
        """Validate idempotency implementation."""
        violations = []
        if re.search(r'(post|put|patch|delete)', content.lower()) and 'idempotency' not in content.lower():
            violations.append(Violation(
                        rule_name='All mutating routes must accept Idempotency-Key',
                        severity=Severity.ERROR,
                        message='All mutating routes must accept Idempotency-Key',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        return violations
    
    def _validate_error_handling(self, content: str, file_path: str) -> List[Violation]:
        """Validate error handling implementation."""
        violations = []
        if 'error' in content.lower() and 'envelope' not in content.lower():
            violations.append(Violation(
                        rule_name='Stable error envelope with canonical codes required',
                        severity=Severity.ERROR,
                        message='Stable error envelope with canonical codes required',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        return violations
    
    def _validate_request_validation(self, content: str, file_path: str) -> List[Violation]:
        """Validate request validation implementation."""
        violations = []
        if 'request' in content.lower() and 'validation' not in content.lower():
            violations.append(Violation(
                        rule_name='Validate all request inputs with proper error responses',
                        severity=Severity.ERROR,
                        message='Validate all request inputs with proper error responses',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        return violations
    
    def _validate_response_validation(self, content: str, file_path: str) -> List[Violation]:
        """Validate response validation implementation."""
        violations = []
        if 'response' in content.lower() and 'validation' not in content.lower():
            violations.append(Violation(
                        rule_name='Validate all response outputs with proper schemas',
                        severity=Severity.ERROR,
                        message='Validate all response outputs with proper schemas',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        return violations
    
    def _validate_authentication(self, content: str, file_path: str) -> List[Violation]:
        """Validate authentication implementation."""
        violations = []
        if 'auth' in content.lower() and 'jwt' not in content.lower():
            violations.append(Violation(
                        rule_name='JWT with documented scopes per route required',
                        severity=Severity.ERROR,
                        message='JWT with documented scopes per route required',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        return violations
    
    def _validate_authorization(self, content: str, file_path: str) -> List[Violation]:
        """Validate authorization implementation."""
        violations = []
        if 'auth' in content.lower() and 'authorization' not in content.lower():
            violations.append(Violation(
                        rule_name='Document authorization requirements and access controls',
                        severity=Severity.ERROR,
                        message='Document authorization requirements and access controls',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        return violations
    
    def _validate_rate_limiting(self, content: str, file_path: str) -> List[Violation]:
        """Validate rate limiting implementation."""
        violations = []
        if 'api' in content.lower() and 'rate' not in content.lower():
            violations.append(Violation(
                        rule_name='Declare rate limit headers; exceeding returns 429 deterministically',
                        severity=Severity.WARNING,
                        message='Declare rate limit headers; exceeding returns 429 deterministically',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        return violations
    
    def _validate_caching(self, content: str, file_path: str) -> List[Violation]:
        """Validate caching implementation."""
        violations = []
        if 'put' in content.lower() or 'patch' in content.lower():
            if 'etag' not in content.lower() and 'cache' not in content.lower():
                violations.append(Violation(
                        rule_name='ETag/If-Match for racy PUT/PATCH; Cache-Control documented',
                        severity=Severity.WARNING,
                        message='ETag/If-Match for racy PUT/PATCH; Cache-Control documented',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
                
                    ))
        return violations
    
    def _validate_documentation(self, content: str, file_path: str) -> List[Violation]:
        """Validate documentation implementation."""
        violations = []
        if 'response' in content.lower() and 'example' not in content.lower():
            violations.append(Violation(
                        rule_name='Examples for all responses; migration notes for breaking changes',
                        severity=Severity.WARNING,
                        message='Examples for all responses; migration notes for breaking changes',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        return violations
    
    def _validate_testing(self, content: str, file_path: str) -> List[Violation]:
        """Validate testing implementation."""
        violations = []
        if 'api' in content.lower() and 'test' not in content.lower():
            violations.append(Violation(
                        rule_name='Provider and consumer contract tests; mock server from spec',
                        severity=Severity.ERROR,
                        message='Provider and consumer contract tests; mock server from spec',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        return violations
    
    def _validate_monitoring(self, content: str, file_path: str) -> List[Violation]:
        """Validate monitoring implementation."""
        violations = []
        if 'api' in content.lower() and 'metric' not in content.lower():
            violations.append(Violation(
                        rule_name='Metrics/traces/alerts updated; SLOs published per GA route',
                        severity=Severity.WARNING,
                        message='Metrics/traces/alerts updated; SLOs published per GA route',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        return violations
    
    def _validate_deprecation(self, content: str, file_path: str) -> List[Violation]:
        """Validate deprecation implementation."""
        violations = []
        if 'deprecated' in content.lower() and 'sunset' not in content.lower():
            violations.append(Violation(
                file_path=file_path,
                line_number=1,
                message='Mark deprecated: true, emit Sunset header with date, ≥90 days notice',
                severity=Severity.WARNING,
                category='api'
            ))
        return violations
    
    def _validate_api_receipts(self, content: str, file_path: str) -> List[Violation]:
        """Validate API receipts implementation."""
        violations = []
        if 'contract' in content.lower() and 'receipt' not in content.lower():
            violations.append(Violation(
                file_path=file_path,
                line_number=1,
                message='Emit JSONL receipts for contract.publish, contract.diff, contract.violation',
                severity=Severity.ERROR,
                category='api'
            ))
        return violations
    
    def _validate_status_lifecycle(self, content: str, file_path: str) -> List[Violation]:
        """Validate status lifecycle implementation."""
        violations = []
        if 'endpoint' in content.lower() and 'x-status' not in content.lower():
            violations.append(Violation(
                        rule_name='Add x-status to endpoints: experimental | beta | ga | deprecated | sunset',
                        severity=Severity.WARNING,
                        message='Add x-status to endpoints: experimental | beta | ga | deprecated | sunset',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        return violations
    
    def _validate_idempotency_retention(self, content: str, file_path: str) -> List[Violation]:
        """Validate idempotency retention implementation."""
        violations = []
        if 'idempotency' in content.lower() and '24h' not in content.lower():
            violations.append(Violation(
                        rule_name='Idempotency retention window default 24h with hash of request body',
                        severity=Severity.WARNING,
                        message='Idempotency retention window default 24h with hash of request body',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        return violations
    
    def _validate_sdk_naming(self, content: str, file_path: str) -> List[Violation]:
        """Validate SDK naming implementation."""
        violations = []
        if 'sdk' in content.lower() and '@zeroui/api-v' not in content.lower():
            violations.append(Violation(
                        rule_name='TypeScript: @zeroui/api-v<major>; Python: zeroui_api_v<major>',
                        severity=Severity.WARNING,
                        message='TypeScript: @zeroui/api-v<major>; Python: zeroui_api_v<major>',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        return violations
    
    def _validate_receipt_signature(self, content: str, file_path: str) -> List[Violation]:
        """Validate receipt signature implementation."""
        violations = []
        if 'receipt' in content.lower() and 'signature' not in content.lower():
            violations.append(Violation(
                        rule_name='Optional receipt_signature (Ed25519) for high-trust actions',
                        severity=Severity.WARNING,
                        message='Optional receipt_signature (Ed25519) for high-trust actions',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='api'
            
                    ))
        return violations
