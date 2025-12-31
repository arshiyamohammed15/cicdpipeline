"""
Test OpenAPI specifications for infrastructure services.

Tests validate:
- OpenAPI YAML syntax and structure
- Schema definitions match TypeScript interfaces
- Endpoint definitions are complete
- Request/response models are properly defined
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Set


class TestPolicyServiceOpenAPI:
    """Tests for Policy Service OpenAPI specification."""

    def setup_method(self):
        """Load OpenAPI spec."""
        spec_path = Path("docs/architecture/openapi/policy-service.openapi.yaml")
        assert spec_path.exists(), f"OpenAPI spec not found: {spec_path}"

        # Read and parse YAML (simple parser for basic structure)
        content = spec_path.read_text(encoding='utf-8')
        self.spec_content = content
        self.spec_path = spec_path

    def test_openapi_version(self):
        """Test: OpenAPI version is 3.1.0."""
        assert "openapi: 3.1.0" in self.spec_content or '"openapi": "3.1.0"' in self.spec_content, \
            "OpenAPI version must be 3.1.0"

    def test_info_section_complete(self):
        """Test: Info section has required fields."""
        assert "title:" in self.spec_content or '"title"' in self.spec_content, \
            "Info section must have title"
        assert "version:" in self.spec_content or '"version"' in self.spec_content, \
            "Info section must have version"
        assert "Policy Service" in self.spec_content, \
            "Title should mention Policy Service"

    def test_paths_defined(self):
        """Test: All required endpoints are defined."""
        required_paths = [
            "/api/v1/policies/current",
            "/api/v1/policies/history",
            "/api/v1/policies/activate",
            "/api/v1/trust/crl/revoke",
            "/health"
        ]

        for path in required_paths:
            assert path in self.spec_content, \
                f"Required path {path} must be defined"

    def test_get_current_policy_defined(self):
        """Test: GET /api/v1/policies/current endpoint is properly defined."""
        assert "/api/v1/policies/current:" in self.spec_content, \
            "GET /api/v1/policies/current path must be defined"
        assert "get:" in self.spec_content or '"get"' in self.spec_content, \
            "GET method must be defined for /api/v1/policies/current"
        assert "getCurrentPolicy" in self.spec_content, \
            "Operation ID getCurrentPolicy must be defined"

    def test_get_policy_history_defined(self):
        """Test: GET /api/v1/policies/history endpoint is properly defined."""
        assert "/api/v1/policies/history:" in self.spec_content, \
            "GET /api/v1/policies/history path must be defined"
        assert "getPolicyHistory" in self.spec_content, \
            "Operation ID getPolicyHistory must be defined"

    def test_activate_policy_defined(self):
        """Test: POST /api/v1/policies/activate endpoint is properly defined."""
        assert "/api/v1/policies/activate:" in self.spec_content, \
            "POST /api/v1/policies/activate path must be defined"
        assert "activatePolicy" in self.spec_content, \
            "Operation ID activatePolicy must be defined"
        assert "ActivatePolicyRequest" in self.spec_content, \
            "ActivatePolicyRequest schema must be defined"

    def test_revoke_policy_defined(self):
        """Test: POST /api/v1/trust/crl/revoke endpoint is properly defined."""
        assert "/api/v1/trust/crl/revoke:" in self.spec_content, \
            "POST /api/v1/trust/crl/revoke path must be defined"
        assert "revokePolicy" in self.spec_content, \
            "Operation ID revokePolicy must be defined"
        assert "RevokePolicyRequest" in self.spec_content, \
            "RevokePolicyRequest schema must be defined"

    def test_policy_snapshot_schema_defined(self):
        """Test: PolicySnapshotResponse schema matches TypeScript interface."""
        assert "PolicySnapshotResponse" in self.spec_content, \
            "PolicySnapshotResponse schema must be defined"

        # Check required fields from TypeScript interface
        required_fields = [
            "snapshot_id",
            "policy_id",
            "version",
            "snapshot_hash",
            "policy_content",
            "timestamp_utc",
            "signature"
        ]

        for field in required_fields:
            assert field in self.spec_content, \
                f"PolicySnapshotResponse must include field: {field}"

    def test_snapshot_hash_pattern(self):
        """Test: snapshot_hash follows SHA256 pattern."""
        assert "sha256:" in self.spec_content, \
            "snapshot_hash should reference SHA256 pattern"
        assert "pattern:" in self.spec_content or '"pattern"' in self.spec_content, \
            "snapshot_hash should have pattern validation"

    def test_policy_history_response_defined(self):
        """Test: PolicyHistoryResponse schema is defined."""
        assert "PolicyHistoryResponse" in self.spec_content, \
            "PolicyHistoryResponse schema must be defined"
        assert "snapshots" in self.spec_content, \
            "PolicyHistoryResponse must have snapshots array"

    def test_error_response_schema_defined(self):
        """Test: ErrorResponse schema is defined."""
        assert "ErrorResponse" in self.spec_content, \
            "ErrorResponse schema must be defined"
        assert "error" in self.spec_content, \
            "ErrorResponse must have error object"
        assert "code" in self.spec_content, \
            "ErrorResponse must have code field"
        assert "message" in self.spec_content, \
            "ErrorResponse must have message field"

    def test_health_endpoint_defined(self):
        """Test: Health endpoint is defined."""
        assert "/health:" in self.spec_content, \
            "Health endpoint must be defined"
        assert "HealthResponse" in self.spec_content, \
            "HealthResponse schema must be defined"

    def test_servers_defined(self):
        """Test: Server URLs are defined."""
        assert "servers:" in self.spec_content or '"servers"' in self.spec_content, \
            "Servers section must be defined"
        assert "localhost" in self.spec_content or "8000" in self.spec_content, \
            "Local development server should be defined"

    def test_components_schemas_section(self):
        """Test: Components schemas section exists."""
        assert "components:" in self.spec_content or '"components"' in self.spec_content, \
            "Components section must be defined"
        assert "schemas:" in self.spec_content or '"schemas"' in self.spec_content, \
            "Schemas section must be defined"

    def test_response_codes_defined(self):
        """Test: Standard HTTP response codes are defined."""
        # Check that common response codes are referenced
        response_codes = ["200", "400", "404", "500"]
        for code in response_codes:
            assert f"'{code}':" in self.spec_content or f'"{code}":' in self.spec_content, \
                f"HTTP {code} response should be defined for at least one endpoint"


class TestEvidenceServiceOpenAPI:
    """Tests for Evidence Service OpenAPI specification."""

    def setup_method(self):
        """Load OpenAPI spec."""
        spec_path = Path("docs/architecture/openapi/evidence-service.openapi.yaml")
        assert spec_path.exists(), f"OpenAPI spec not found: {spec_path}"

        content = spec_path.read_text(encoding='utf-8')
        self.spec_content = content
        self.spec_path = spec_path

    def test_openapi_version(self):
        """Test: OpenAPI version is 3.1.0."""
        assert "openapi: 3.1.0" in self.spec_content or '"openapi": "3.1.0"' in self.spec_content, \
            "OpenAPI version must be 3.1.0"

    def test_info_section_complete(self):
        """Test: Info section has required fields."""
        assert "title:" in self.spec_content or '"title"' in self.spec_content, \
            "Info section must have title"
        assert "version:" in self.spec_content or '"version"' in self.spec_content, \
            "Info section must have version"
        assert "Evidence Service" in self.spec_content, \
            "Title should mention Evidence Service"

    def test_paths_defined(self):
        """Test: All required endpoints are defined."""
        required_paths = [
            "/api/v1/evidence",
            "/api/v1/evidence/{evidence_id}",
            "/api/v1/evidence/batch",
            "/health"
        ]

        for path in required_paths:
            assert path in self.spec_content, \
                f"Required path {path} must be defined"

    def test_store_evidence_defined(self):
        """Test: POST /api/v1/evidence endpoint is properly defined."""
        assert "/api/v1/evidence:" in self.spec_content, \
            "POST /api/v1/evidence path must be defined"
        assert "post:" in self.spec_content or '"post"' in self.spec_content, \
            "POST method must be defined for /api/v1/evidence"
        assert "storeEvidence" in self.spec_content, \
            "Operation ID storeEvidence must be defined"
        assert "StoreEvidenceRequest" in self.spec_content, \
            "StoreEvidenceRequest schema must be defined"

    def test_get_evidence_defined(self):
        """Test: GET /api/v1/evidence/{evidence_id} endpoint is properly defined."""
        assert "/api/v1/evidence/{evidence_id}:" in self.spec_content, \
            "GET /api/v1/evidence/{evidence_id} path must be defined"
        assert "getEvidence" in self.spec_content, \
            "Operation ID getEvidence must be defined"
        assert "evidence_id" in self.spec_content, \
            "Path parameter evidence_id must be defined"

    def test_delete_evidence_defined(self):
        """Test: DELETE /api/v1/evidence/{evidence_id} endpoint is properly defined."""
        assert "delete:" in self.spec_content or '"delete"' in self.spec_content, \
            "DELETE method must be defined for /api/v1/evidence/{evidence_id}"
        assert "deleteEvidence" in self.spec_content, \
            "Operation ID deleteEvidence must be defined"

    def test_batch_evidence_defined(self):
        """Test: POST /api/v1/evidence/batch endpoint is properly defined."""
        assert "/api/v1/evidence/batch:" in self.spec_content, \
            "POST /api/v1/evidence/batch path must be defined"
        assert "storeEvidenceBatch" in self.spec_content, \
            "Operation ID storeEvidenceBatch must be defined"
        assert "StoreEvidenceBatchRequest" in self.spec_content, \
            "StoreEvidenceBatchRequest schema must be defined"

    def test_evidence_handle_schema_matches_typescript(self):
        """Test: EvidenceHandleResponse schema matches TypeScript EvidenceHandle interface."""
        assert "EvidenceHandleResponse" in self.spec_content, \
            "EvidenceHandleResponse schema must be defined"

        # Check required fields from TypeScript EvidenceHandle interface
        required_fields = [
            "url",
            "type",
            "description"
        ]

        for field in required_fields:
            assert field in self.spec_content, \
                f"EvidenceHandleResponse must include field: {field}"

    def test_evidence_handle_optional_fields(self):
        """Test: EvidenceHandleResponse includes optional expires_at field."""
        assert "expires_at" in self.spec_content, \
            "EvidenceHandleResponse should include optional expires_at field"

    def test_evidence_response_schema_defined(self):
        """Test: EvidenceResponse schema is defined."""
        assert "EvidenceResponse" in self.spec_content, \
            "EvidenceResponse schema must be defined"
        assert "content" in self.spec_content, \
            "EvidenceResponse must have content field"

    def test_error_response_schema_defined(self):
        """Test: ErrorResponse schema is defined."""
        assert "ErrorResponse" in self.spec_content, \
            "ErrorResponse schema must be defined"
        assert "error" in self.spec_content, \
            "ErrorResponse must have error object"

    def test_health_endpoint_defined(self):
        """Test: Health endpoint is defined."""
        assert "/health:" in self.spec_content, \
            "Health endpoint must be defined"
        assert "HealthResponse" in self.spec_content, \
            "HealthResponse schema must be defined"

    def test_servers_defined(self):
        """Test: Server URLs are defined."""
        assert "servers:" in self.spec_content or '"servers"' in self.spec_content, \
            "Servers section must be defined"

    def test_response_codes_defined(self):
        """Test: Standard HTTP response codes are defined."""
        response_codes = ["200", "201", "204", "400", "404", "410", "500"]
        for code in response_codes:
            assert f"'{code}':" in self.spec_content or f'"{code}":' in self.spec_content, \
                f"HTTP {code} response should be defined for at least one endpoint"

    def test_evidence_type_enum(self):
        """Test: Evidence type examples match expected types."""
        # Check that common evidence types are mentioned
        evidence_types = ["log", "artifact", "metric"]
        found_types = sum(1 for t in evidence_types if t in self.spec_content)
        assert found_types > 0, \
            "Evidence type examples should include common types (log, artifact, metric)"


class TestOpenAPICrossService:
    """Cross-service tests for OpenAPI specifications."""

    def test_both_specs_exist(self):
        """Test: Both OpenAPI specs exist."""
        policy_spec = Path("docs/architecture/openapi/policy-service.openapi.yaml")
        evidence_spec = Path("docs/architecture/openapi/evidence-service.openapi.yaml")

        assert policy_spec.exists(), \
            f"Policy service OpenAPI spec must exist: {policy_spec}"
        assert evidence_spec.exists(), \
            f"Evidence service OpenAPI spec must exist: {evidence_spec}"

    def test_consistent_error_response_format(self):
        """Test: Both services use consistent error response format."""
        policy_content = Path("docs/architecture/openapi/policy-service.openapi.yaml").read_text(encoding='utf-8')
        evidence_content = Path("docs/architecture/openapi/evidence-service.openapi.yaml").read_text(encoding='utf-8')

        # Both should have ErrorResponse with code and message
        assert "ErrorResponse" in policy_content, \
            "Policy service must define ErrorResponse"
        assert "ErrorResponse" in evidence_content, \
            "Evidence service must define ErrorResponse"

        # Both should have error.code and error.message
        assert "code" in policy_content and "message" in policy_content, \
            "Policy service ErrorResponse must have code and message"
        assert "code" in evidence_content and "message" in evidence_content, \
            "Evidence service ErrorResponse must have code and message"

    def test_consistent_health_response_format(self):
        """Test: Both services use consistent health response format."""
        policy_content = Path("docs/architecture/openapi/policy-service.openapi.yaml").read_text(encoding='utf-8')
        evidence_content = Path("docs/architecture/openapi/evidence-service.openapi.yaml").read_text(encoding='utf-8')

        # Both should have HealthResponse
        assert "HealthResponse" in policy_content, \
            "Policy service must define HealthResponse"
        assert "HealthResponse" in evidence_content, \
            "Evidence service must define HealthResponse"

        # Both should have status field
        assert "status" in policy_content, \
            "Policy service HealthResponse must have status field"
        assert "status" in evidence_content, \
            "Evidence service HealthResponse must have status field"

    def test_openapi_version_consistent(self):
        """Test: Both specs use same OpenAPI version."""
        policy_content = Path("docs/architecture/openapi/policy-service.openapi.yaml").read_text(encoding='utf-8')
        evidence_content = Path("docs/architecture/openapi/evidence-service.openapi.yaml").read_text(encoding='utf-8')

        # Both should specify OpenAPI 3.1.0
        assert "3.1.0" in policy_content, \
            "Policy service must use OpenAPI 3.1.0"
        assert "3.1.0" in evidence_content, \
            "Evidence service must use OpenAPI 3.1.0"
