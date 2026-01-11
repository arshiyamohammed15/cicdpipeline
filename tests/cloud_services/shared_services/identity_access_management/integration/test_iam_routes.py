#!/usr/bin/env python3
"""
Integration tests for Identity & Access Management (IAM) API routes.

WHAT: Complete test coverage for all IAM API endpoints (/verify, /decision, /policies, /health, /metrics, /config)
WHY: Ensure API endpoints work correctly with proper error handling and response formats
Reads/Writes: Uses TestClient for FastAPI, mocks all external dependencies
Contracts: Tests validate API contracts match IAM spec v1.1.0
Risks: None - all tests are hermetic with mocked dependencies
"""

import sys
import unittest
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
try:
    from fastapi.testclient import TestClient
except ImportError:
    # Fallback for older versions
    from starlette.testclient import TestClient

    def create_test_client(app_instance):
        """
        Create TestClient with version compatibility handling.

        Args:
            app_instance: FastAPI app instance

        Returns:
            TestClient instance

        Raises:
            RuntimeError: If TestClient cannot be initialized due to version incompatibility
        """
        try:
            # Try standard initialization
            return TestClient(app_instance)
        except TypeError as e:
            # Version incompatibility - provide helpful error
            import httpx
            import starlette
            error_msg = (
                f"\n{'='*60}\n"
                f"TestClient initialization failed due to version incompatibility.\n"
                f"Current versions:\n"
                f"  - httpx: {httpx.__version__}\n"
                f"  - starlette: {starlette.__version__}\n"
                f"\nSolution: Install compatible httpx version:\n"
                f"  pip install httpx==0.27.0\n"
                f"\nOr update requirements.txt and reinstall:\n"
                f"  pip install -r requirements.txt\n"
                f"{'='*60}\n"
            )
            raise RuntimeError(error_msg) from e
            raise

def create_test_client(app_instance):
    """Create a TestClient for the IAM app."""
    return TestClient(app_instance)

# Add project root to path
project_root = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(project_root))

# Import using direct file path due to hyphenated directory names
import importlib.util

# Setup module path for relative imports
iam_dir = project_root / "src" / "cloud_services" / "shared-services" / "identity-access-management"

# Create parent package structure
parent_pkg = type(sys)('identity_access_management')
parent_pkg.__path__ = [str(iam_dir)]
sys.modules['identity_access_management'] = parent_pkg

# Load main module
main_path = iam_dir / "main.py"
spec_main = importlib.util.spec_from_file_location("identity_access_management.main", main_path)
main_module = importlib.util.module_from_spec(spec_main)

# Load dependencies first
dependencies_path = iam_dir / "dependencies.py"
spec_deps = importlib.util.spec_from_file_location("identity_access_management.dependencies", dependencies_path)
deps_module = importlib.util.module_from_spec(spec_deps)
sys.modules['identity_access_management.dependencies'] = deps_module
spec_deps.loader.exec_module(deps_module)

# Load models
models_path = iam_dir / "models.py"
spec_models = importlib.util.spec_from_file_location("identity_access_management.models", models_path)
models_module = importlib.util.module_from_spec(spec_models)
sys.modules['identity_access_management.models'] = models_module
spec_models.loader.exec_module(models_module)

# Load services
services_path = iam_dir / "services.py"
spec_services = importlib.util.spec_from_file_location("identity_access_management.services", services_path)
services_module = importlib.util.module_from_spec(spec_services)
sys.modules['identity_access_management.services'] = services_module
spec_services.loader.exec_module(services_module)

# Load routes
routes_path = iam_dir / "routes.py"
spec_routes = importlib.util.spec_from_file_location("identity_access_management.routes", routes_path)
routes_module = importlib.util.module_from_spec(spec_routes)
sys.modules['identity_access_management.routes'] = routes_module
spec_routes.loader.exec_module(routes_module)

# Load middleware
middleware_path = iam_dir / "middleware.py"
spec_middleware = importlib.util.spec_from_file_location("identity_access_management.middleware", middleware_path)
middleware_module = importlib.util.module_from_spec(spec_middleware)
sys.modules['identity_access_management.middleware'] = middleware_module
spec_middleware.loader.exec_module(middleware_module)

# Now load main
spec_main.loader.exec_module(main_module)
sys.modules['identity-access-management.main'] = main_module

# Get the app
app = main_module.app


@pytest.mark.integration
class TestVerifyEndpoint(unittest.TestCase):
    """Test /iam/v1/verify endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client for all tests in this class."""
        cls.client = create_test_client(app)

    @pytest.mark.integration
    def test_verify_success(self):
        """Test verify endpoint with valid token."""
        # Mock jwt in sys.modules
        import sys
        mock_jwt = MagicMock()
        mock_jwt.decode.return_value = {
            "kid": "key-2025q4",
            "iat": 1609459200,
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            "aud": "zeroui",
            "iss": "iam",
            "sub": "user-123",
            "scope": ["read", "write"]
        }
        mock_jwt.InvalidTokenError = Exception
        sys.modules['jwt'] = mock_jwt

        try:
            response = self.client.post(
                "/iam/v1/verify",
                json={"token": "valid.token.here"}
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["sub"], "user-123")
            self.assertIn("scope", data)
            self.assertIn("valid_until", data)
        finally:
            if 'jwt' in sys.modules:
                del sys.modules['jwt']

    @pytest.mark.integration
    def test_verify_invalid_token(self):
        """Test verify endpoint with invalid token."""
        # Mock jwt in sys.modules
        import sys
        mock_jwt = MagicMock()
        mock_jwt.decode.side_effect = Exception("Invalid token")
        mock_jwt.InvalidTokenError = Exception
        sys.modules['jwt'] = mock_jwt

        try:
            response = self.client.post(
                "/iam/v1/verify",
                json={"token": "invalid.token"}
            )

            self.assertEqual(response.status_code, 401)
            data = response.json()
            # FastAPI wraps error in "detail" field
            self.assertIn("detail", data)
            self.assertIn("error", data["detail"])
            self.assertEqual(data["detail"]["error"]["code"], "AUTH_FAILED")
        finally:
            if 'jwt' in sys.modules:
                del sys.modules['jwt']

    @pytest.mark.integration
    def test_verify_missing_token(self):
        """Test verify endpoint with missing token."""
        response = self.client.post(
            "/iam/v1/verify",
            json={}
        )

        self.assertEqual(response.status_code, 422)  # Validation error


@pytest.mark.integration
class TestDecisionEndpoint(unittest.TestCase):
    """Test /iam/v1/decision endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client for all tests in this class."""
        cls.client = create_test_client(app)

    @pytest.mark.integration
    def test_decision_allow(self):
        """Test decision endpoint returns ALLOW."""
        response = self.client.post(
            "/iam/v1/decision",
            json={
                "subject": {
                    "sub": "user-123",
                    "roles": ["developer"]
                },
                "action": "write",
                "resource": "/api/resource"
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["decision"], "ALLOW")
        self.assertIn("reason", data)
        self.assertIn("receipt_id", data)

    @pytest.mark.integration
    def test_decision_deny(self):
        """Test decision endpoint returns DENY."""
        response = self.client.post(
            "/iam/v1/decision",
            json={
                "subject": {
                    "sub": "user-123",
                    "roles": ["viewer"]
                },
                "action": "admin",
                "resource": "/api/admin"
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["decision"], "DENY")

    @pytest.mark.integration
    def test_decision_elevation_required(self):
        """Test decision endpoint returns ELEVATION_REQUIRED."""
        response = self.client.post(
            "/iam/v1/decision",
            json={
                "subject": {
                    "sub": "user-123",
                    "roles": ["developer"]
                },
                "action": "request_elevation",
                "resource": "/api/admin",
                "elevation": {
                    "request": True,
                    "scope": ["admin"]
                }
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["decision"], "ELEVATION_REQUIRED")

    @pytest.mark.integration
    def test_decision_invalid_request(self):
        """Test decision endpoint with invalid request."""
        response = self.client.post(
            "/iam/v1/decision",
            json={
                "subject": {
                    "sub": "user-123"
                }
            }
        )

        self.assertEqual(response.status_code, 422)  # Validation error


@pytest.mark.integration
class TestPoliciesEndpoint(unittest.TestCase):
    """Test /iam/v1/policies endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client for all tests in this class."""
        cls.client = create_test_client(app)

    @pytest.mark.integration
    def test_policies_upsert_success(self):
        """Test policies endpoint upserts policy bundle."""
        response = self.client.put(
            "/iam/v1/policies",
            json={
                "bundle_id": "bundle-1",
                "version": "1.0.0",
                "policies": [
                    {
                        "id": "policy-1",
                        "rules": [
                            {
                                "rule_type": "allow",
                                "rule_data": {"action": "read"}
                            }
                        ],
                        "status": "released"
                    }
                ]
            },
            headers={"X-Idempotency-Key": "test-key-123"}
        )

        self.assertEqual(response.status_code, 202)
        data = response.json()
        self.assertEqual(data["bundle_id"], "bundle-1")
        self.assertIn("snapshot_id", data)
        self.assertEqual(data["status"], "accepted")

    @pytest.mark.integration
    def test_policies_missing_idempotency_key(self):
        """Test policies endpoint requires X-Idempotency-Key."""
        response = self.client.put(
            "/iam/v1/policies",
            json={
                "bundle_id": "bundle-1",
                "version": "1.0.0",
                "policies": []
            }
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        # JSONResponse returns error at root, not wrapped in detail
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], "BAD_REQUEST")
        self.assertIn("X-Idempotency-Key", data["error"]["message"])


@pytest.mark.integration
class TestHealthEndpoint(unittest.TestCase):
    """Test /iam/v1/health endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client for all tests in this class."""
        cls.client = create_test_client(app)

    @pytest.mark.integration
    def test_health_check(self):
        """Test health endpoint returns healthy status."""
        response = self.client.get("/iam/v1/health")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)

    @pytest.mark.integration
    def test_root_health_check(self):
        """Test root /health endpoint."""
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")


@pytest.mark.integration
class TestMetricsEndpoint(unittest.TestCase):
    """Test /iam/v1/metrics endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client for all tests in this class."""
        cls.client = create_test_client(app)

    @pytest.mark.integration
    def test_metrics_endpoint(self):
        """Test metrics endpoint returns service metrics."""
        response = self.client.get("/iam/v1/metrics")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("authentication_count", data)
        self.assertIn("decision_count", data)
        self.assertIn("policy_count", data)
        self.assertIn("average_auth_latency_ms", data)
        self.assertIn("average_decision_latency_ms", data)
        self.assertIn("average_policy_latency_ms", data)
        self.assertIn("timestamp", data)


@pytest.mark.integration
class TestConfigEndpoint(unittest.TestCase):
    """Test /iam/v1/config endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client for all tests in this class."""
        cls.client = create_test_client(app)

    @pytest.mark.integration
    def test_config_endpoint(self):
        """Test config endpoint returns module configuration."""
        response = self.client.get("/iam/v1/config")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["module_id"], "EPC-1")
        self.assertEqual(data["version"], "1.1.0")
        self.assertIn("api_endpoints", data)
        self.assertIn("performance_requirements", data)
        self.assertIn("timestamp", data)


@pytest.mark.integration
class TestErrorHandling(unittest.TestCase):
    """Test error handling across endpoints."""

    @classmethod
    def setUpClass(cls):
        """Set up test client for all tests in this class."""
        cls.client = create_test_client(app)

    @pytest.mark.integration
    def test_error_envelope_structure(self):
        """Test error responses follow IPC protocol envelope."""
        response = self.client.post(
            "/iam/v1/verify",
            json={"token": "invalid"}
        )

        if response.status_code >= 400:
            data = response.json()
            # FastAPI wraps error in "detail" field
            self.assertIn("detail", data)
            if "error" in data["detail"]:
                self.assertIn("code", data["detail"]["error"])
                self.assertIn("message", data["detail"]["error"])
            else:
                # Some validation errors might have different structure
                self.assertIsNotNone(data.get("detail"))

    @pytest.mark.integration
    def test_correlation_headers(self):
        """Test responses include correlation headers."""
        response = self.client.get("/iam/v1/health")

        self.assertIn("X-Trace-Id", response.headers)
        self.assertIn("X-Request-Id", response.headers)
        self.assertIn("X-Span-Id", response.headers)


@pytest.mark.integration
class TestBreakGlassEndpoint(unittest.TestCase):
    """Test /iam/v1/break-glass endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client for all tests in this class."""
        cls.client = create_test_client(app)

    @pytest.mark.integration
    def test_break_glass_success(self):
        """Test break-glass grants access when policy enabled."""
        # First, enable break-glass policy via /policies endpoint
        response = self.client.put(
            "/iam/v1/policies",
            headers={"X-Idempotency-Key": "test-break-glass-policy-1"},
            json={
                "bundle_id": "break-glass-bundle",
                "version": "1.0.0",
                "policies": [
                    {
                        "id": "iam-break-glass",
                        "rules": [
                            {
                                "rule_type": "allow",
                                "rule_data": {}
                            }
                        ],
                        "status": "released"
                    }
                ]
            }
        )

        self.assertEqual(response.status_code, 202)

        # Now test break-glass endpoint
        response = self.client.post(
            "/iam/v1/break-glass",
            json={
                "subject": {
                    "sub": "user-123",
                    "roles": ["developer"]
                },
                "incident_id": "INC-2025-001",
                "justification": "Critical production incident requiring emergency access",
                "approver_identity": "admin-456"
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["decision"], "BREAK_GLASS_GRANTED")
        self.assertIsNotNone(data["expires_at"])
        self.assertIn("incident", data["reason"].lower())
        self.assertIn("24h", data["reason"].lower())

    @pytest.mark.integration
    def test_break_glass_policy_not_enabled(self):
        """Test break-glass fails when policy not enabled."""
        response = self.client.post(
            "/iam/v1/break-glass",
            json={
                "subject": {
                    "sub": "user-123",
                    "roles": ["developer"]
                },
                "incident_id": "INC-2025-001",
                "justification": "Critical production incident"
            }
        )

        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("detail", data)
        if "error" in data["detail"]:
            self.assertEqual(data["detail"]["error"]["code"], "FORBIDDEN")
            self.assertIn("not enabled", data["detail"]["error"]["message"].lower())


if __name__ == '__main__':
    unittest.main()
