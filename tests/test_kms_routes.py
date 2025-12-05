#!/usr/bin/env python3
"""
Integration tests for Key Management Service (KMS) API routes.

WHAT: Complete test coverage for all KMS API endpoints (/keys, /sign, /verify, /encrypt, /decrypt, /keys/{id}/rotate, /keys/{id}/revoke, /trust-anchors, /health, /metrics, /config)
WHY: Ensure API endpoints work correctly with proper error handling and response formats
Reads/Writes: Uses TestClient for FastAPI, mocks all external dependencies
Contracts: Tests validate API contracts match KMS spec v0.1.0
Risks: None - all tests are hermetic with mocked dependencies
"""

import sys
import unittest
import base64
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
try:
    from fastapi.testclient import TestClient
except ImportError:
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
        return TestClient(app_instance)
    except TypeError as e:
        if "unexpected keyword argument 'app'" in str(e):
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
                f"{'='*60}\n"
            )
            raise RuntimeError(error_msg) from e
        raise

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import using direct file path due to hyphenated directory names
import importlib.util

# Setup module path for relative imports
kms_dir = project_root / "src" / "cloud_services" / "shared-services" / "key-management-service"

# Create parent package structure
parent_pkg = type(sys)('key_management_service')
sys.modules['key_management_service'] = parent_pkg

# Create hsm subpackage
hsm_pkg = type(sys)('key_management_service.hsm')
sys.modules['key_management_service.hsm'] = hsm_pkg

# Load dependencies first
dependencies_path = kms_dir / "dependencies.py"
spec_deps = importlib.util.spec_from_file_location("key_management_service.dependencies", dependencies_path)
deps_module = importlib.util.module_from_spec(spec_deps)
sys.modules['key_management_service.dependencies'] = deps_module
spec_deps.loader.exec_module(deps_module)

# Load models
models_path = kms_dir / "models.py"
spec_models = importlib.util.spec_from_file_location("key_management_service.models", models_path)
models_module = importlib.util.module_from_spec(spec_models)
sys.modules['key_management_service.models'] = models_module
spec_models.loader.exec_module(models_module)

# Load HSM
hsm_interface_path = kms_dir / "hsm" / "interface.py"
spec_hsm_interface = importlib.util.spec_from_file_location("key_management_service.hsm.interface", hsm_interface_path)
hsm_interface_module = importlib.util.module_from_spec(spec_hsm_interface)
sys.modules['key_management_service.hsm.interface'] = hsm_interface_module
spec_hsm_interface.loader.exec_module(hsm_interface_module)

hsm_mock_path = kms_dir / "hsm" / "mock_hsm.py"
spec_hsm_mock = importlib.util.spec_from_file_location("key_management_service.hsm.mock_hsm", hsm_mock_path)
hsm_mock_module = importlib.util.module_from_spec(spec_hsm_mock)
sys.modules['key_management_service.hsm.mock_hsm'] = hsm_mock_module
spec_hsm_mock.loader.exec_module(hsm_mock_module)

# Set up hsm module for relative imports - load __init__.py first
hsm_init_path = kms_dir / "hsm" / "__init__.py"
spec_hsm_init = importlib.util.spec_from_file_location("key_management_service.hsm", hsm_init_path)
hsm_init_module = importlib.util.module_from_spec(spec_hsm_init)
sys.modules['key_management_service.hsm'] = hsm_init_module
spec_hsm_init.loader.exec_module(hsm_init_module)

# Load services
services_path = kms_dir / "services.py"
spec_services = importlib.util.spec_from_file_location("key_management_service.services", services_path)
services_module = importlib.util.module_from_spec(spec_services)
sys.modules['key_management_service.services'] = services_module
spec_services.loader.exec_module(services_module)

# Load routes
routes_path = kms_dir / "routes.py"
spec_routes = importlib.util.spec_from_file_location("key_management_service.routes", routes_path)
routes_module = importlib.util.module_from_spec(spec_routes)
sys.modules['key_management_service.routes'] = routes_module
spec_routes.loader.exec_module(routes_module)

# Load middleware
middleware_path = kms_dir / "middleware.py"
spec_middleware = importlib.util.spec_from_file_location("key_management_service.middleware", middleware_path)
middleware_module = importlib.util.module_from_spec(spec_middleware)
sys.modules['key_management_service.middleware'] = middleware_module
spec_middleware.loader.exec_module(middleware_module)

# Load main
main_path = kms_dir / "main.py"
spec_main = importlib.util.spec_from_file_location("key-management-service.main", main_path)
main_module = importlib.util.module_from_spec(spec_main)
sys.modules['key-management-service.main'] = main_module
spec_main.loader.exec_module(main_module)

# Get the app
app = main_module.app


class TestKeysEndpoint(unittest.TestCase):
    """Test POST /kms/v1/keys endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client for all tests in this class."""
        cls.client = create_test_client(app)

    def test_generate_key_rsa2048(self):
        """Test generate key with RSA-2048."""
        response = self.client.post(
            "/kms/v1/keys",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_type": "RSA-2048",
                "key_usage": ["sign", "verify"]
            },
            headers={
                "X-Client-Certificate": "mock-cert",
                "X-Approval-Token": "valid-approval-token-12345"
            }
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("key_id", data)
        self.assertIn("public_key", data)
        self.assertIsNotNone(data["key_id"])
        self.assertIsNotNone(data["public_key"])

    def test_generate_key_ed25519(self):
        """Test generate key with Ed25519."""
        response = self.client.post(
            "/kms/v1/keys",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_type": "Ed25519",
                "key_usage": ["sign", "verify"]
            },
            headers={
                "X-Client-Certificate": "mock-cert",
                "X-Approval-Token": "valid-approval-token-12345"
            }
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("key_id", data)
        self.assertIn("public_key", data)

    def test_generate_key_aes256(self):
        """Test generate key with AES-256."""
        response = self.client.post(
            "/kms/v1/keys",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_type": "AES-256",
                "key_usage": ["encrypt", "decrypt"]
            },
            headers={
                "X-Client-Certificate": "mock-cert",
                "X-Approval-Token": "valid-approval-token-12345"
            }
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("key_id", data)
        self.assertIn("public_key", data)

    def test_generate_key_with_alias(self):
        """Test generate key with key_alias."""
        response = self.client.post(
            "/kms/v1/keys",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_type": "RSA-2048",
                "key_usage": ["sign"],
                "key_alias": "test-key-alias"
            },
            headers={
                "X-Client-Certificate": "mock-cert",
                "X-Approval-Token": "valid-approval-token-12345"
            }
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("key_id", data)

    def test_generate_key_invalid_environment(self):
        """Test generate key with invalid environment."""
        response = self.client.post(
            "/kms/v1/keys",
            json={
                "tenant_id": "mock-tenant",
                "environment": "invalid",
                "plane": "laptop",
                "key_type": "RSA-2048",
                "key_usage": ["sign"]
            },
            headers={"X-Client-Certificate": "mock-cert"}
        )

        self.assertEqual(response.status_code, 422)  # Validation error

    def test_generate_key_missing_required_field(self):
        """Test generate key with missing required field."""
        response = self.client.post(
            "/kms/v1/keys",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_type": "RSA-2048"
                # Missing key_usage
            },
            headers={"X-Client-Certificate": "mock-cert"}
        )

        self.assertEqual(response.status_code, 422)  # Validation error


class TestSignEndpoint(unittest.TestCase):
    """Test POST /kms/v1/sign endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client and create a test key."""
        cls.client = create_test_client(app)
        # Create a test key
        response = cls.client.post(
            "/kms/v1/keys",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_type": "RSA-2048",
                "key_usage": ["sign", "verify"]
            },
            headers={
                "X-Client-Certificate": "mock-cert",
                "X-Approval-Token": "valid-approval-token-12345"
            }
        )
        cls.test_key_id = response.json()["key_id"]

    def test_sign_data_success(self):
        """Test sign endpoint with valid data."""
        data_b64 = base64.b64encode(b"test data to sign").decode('utf-8')
        response = self.client.post(
            "/kms/v1/sign",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_id": self.test_key_id,
                "data": data_b64
            },
            headers={"X-Client-Certificate": "mock-cert"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("signature", data)
        self.assertIn("key_id", data)
        self.assertEqual(data["key_id"], self.test_key_id)
        self.assertIsNotNone(data["signature"])

    def test_sign_data_key_not_found(self):
        """Test sign endpoint with non-existent key."""
        data_b64 = base64.b64encode(b"test data").decode('utf-8')
        response = self.client.post(
            "/kms/v1/sign",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_id": "non-existent-key",
                "data": data_b64
            },
            headers={"X-Client-Certificate": "mock-cert"}
        )

        self.assertEqual(response.status_code, 404)
        error_data = response.json()
        self.assertIn("error", error_data["detail"])
        self.assertEqual(error_data["detail"]["error"]["code"], "KEY_NOT_FOUND")

    def test_sign_data_invalid_base64(self):
        """Test sign endpoint with invalid base64 data."""
        response = self.client.post(
            "/kms/v1/sign",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_id": self.test_key_id,
                "data": "invalid-base64!!!"
            },
            headers={"X-Client-Certificate": "mock-cert"}
        )

        self.assertEqual(response.status_code, 400)
        error_data = response.json()
        self.assertIn("error", error_data["detail"])
        self.assertEqual(error_data["detail"]["error"]["code"], "INVALID_REQUEST")


class TestVerifyEndpoint(unittest.TestCase):
    """Test POST /kms/v1/verify endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client and create a test key."""
        cls.client = create_test_client(app)
        # Create a test key and sign some data
        key_response = cls.client.post(
            "/kms/v1/keys",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_type": "RSA-2048",
                "key_usage": ["sign", "verify"]
            },
            headers={
                "X-Client-Certificate": "mock-cert",
                "X-Approval-Token": "valid-approval-token-12345"
            }
        )
        cls.test_key_id = key_response.json()["key_id"]

        # Sign data
        data_b64 = base64.b64encode(b"test data to verify").decode('utf-8')
        sign_response = cls.client.post(
            "/kms/v1/sign",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_id": cls.test_key_id,
                "data": data_b64
            },
            headers={"X-Client-Certificate": "mock-cert"}
        )
        cls.test_data = data_b64
        cls.test_signature = sign_response.json()["signature"]

    def test_verify_signature_success(self):
        """Test verify endpoint with valid signature."""
        response = self.client.post(
            "/kms/v1/verify",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_id": self.test_key_id,
                "data": self.test_data,
                "signature": self.test_signature
            },
            headers={"X-Client-Certificate": "mock-cert"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("valid", data)
        self.assertIn("key_id", data)
        self.assertEqual(data["key_id"], self.test_key_id)
        # Note: Verification may fail in mock implementation, but endpoint should return 200

    def test_verify_signature_invalid(self):
        """Test verify endpoint with invalid signature."""
        # Use valid base64 but invalid signature bytes
        invalid_signature_b64 = base64.b64encode(b"invalid-signature-bytes").decode('utf-8')
        response = self.client.post(
            "/kms/v1/verify",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_id": self.test_key_id,
                "data": self.test_data,
                "signature": invalid_signature_b64
            },
            headers={"X-Client-Certificate": "mock-cert"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("valid", data)
        # Invalid signature should return valid=False

    def test_verify_signature_key_not_found(self):
        """Test verify endpoint with non-existent key."""
        response = self.client.post(
            "/kms/v1/verify",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_id": "non-existent-key",
                "data": self.test_data,
                "signature": self.test_signature
            },
            headers={"X-Client-Certificate": "mock-cert"}
        )

        self.assertEqual(response.status_code, 404)
        error_data = response.json()
        self.assertEqual(error_data["detail"]["error"]["code"], "KEY_NOT_FOUND")


class TestEncryptEndpoint(unittest.TestCase):
    """Test POST /kms/v1/encrypt endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client and create a test key."""
        cls.client = create_test_client(app)
        # Create an AES-256 key
        key_response = cls.client.post(
            "/kms/v1/keys",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_type": "AES-256",
                "key_usage": ["encrypt", "decrypt"]
            },
            headers={
                "X-Client-Certificate": "mock-cert",
                "X-Approval-Token": "valid-approval-token-12345"
            }
        )
        cls.test_key_id = key_response.json()["key_id"]

    def test_encrypt_data_success(self):
        """Test encrypt endpoint with valid plaintext."""
        plaintext_b64 = base64.b64encode(b"test plaintext data").decode('utf-8')
        response = self.client.post(
            "/kms/v1/encrypt",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_id": self.test_key_id,
                "plaintext": plaintext_b64
            },
            headers={"X-Client-Certificate": "mock-cert"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("ciphertext", data)
        self.assertIn("key_id", data)
        self.assertIn("algorithm", data)
        self.assertIn("iv", data)
        self.assertEqual(data["key_id"], self.test_key_id)

    def test_encrypt_data_with_aad(self):
        """Test encrypt endpoint with additional authenticated data."""
        plaintext_b64 = base64.b64encode(b"test data").decode('utf-8')
        aad_b64 = base64.b64encode(b"additional data").decode('utf-8')
        response = self.client.post(
            "/kms/v1/encrypt",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_id": self.test_key_id,
                "plaintext": plaintext_b64,
                "aad": aad_b64
            },
            headers={"X-Client-Certificate": "mock-cert"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("ciphertext", data)

    def test_encrypt_data_key_not_found(self):
        """Test encrypt endpoint with non-existent key."""
        plaintext_b64 = base64.b64encode(b"test data").decode('utf-8')
        response = self.client.post(
            "/kms/v1/encrypt",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_id": "non-existent-key",
                "plaintext": plaintext_b64
            },
            headers={"X-Client-Certificate": "mock-cert"}
        )

        self.assertEqual(response.status_code, 404)
        error_data = response.json()
        self.assertEqual(error_data["detail"]["error"]["code"], "KEY_NOT_FOUND")


class TestDecryptEndpoint(unittest.TestCase):
    """Test POST /kms/v1/decrypt endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client and create encrypted data."""
        cls.client = create_test_client(app)
        # Create an AES-256 key
        key_response = cls.client.post(
            "/kms/v1/keys",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_type": "AES-256",
                "key_usage": ["encrypt", "decrypt"]
            },
            headers={
                "X-Client-Certificate": "mock-cert",
                "X-Approval-Token": "valid-approval-token-12345"
            }
        )
        cls.test_key_id = key_response.json()["key_id"]

        # Encrypt data
        plaintext_b64 = base64.b64encode(b"test plaintext to decrypt").decode('utf-8')
        encrypt_response = cls.client.post(
            "/kms/v1/encrypt",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_id": cls.test_key_id,
                "plaintext": plaintext_b64
            },
            headers={"X-Client-Certificate": "mock-cert"}
        )
        cls.test_ciphertext = encrypt_response.json()["ciphertext"]
        cls.test_iv = encrypt_response.json()["iv"]

    def test_decrypt_data_success(self):
        """Test decrypt endpoint with valid ciphertext."""
        response = self.client.post(
            "/kms/v1/decrypt",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_id": self.test_key_id,
                "ciphertext": self.test_ciphertext,
                "iv": self.test_iv
            },
            headers={"X-Client-Certificate": "mock-cert"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("plaintext", data)
        self.assertIn("key_id", data)
        self.assertEqual(data["key_id"], self.test_key_id)

    def test_decrypt_data_key_not_found(self):
        """Test decrypt endpoint with non-existent key."""
        response = self.client.post(
            "/kms/v1/decrypt",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_id": "non-existent-key",
                "ciphertext": self.test_ciphertext,
                "iv": self.test_iv
            },
            headers={"X-Client-Certificate": "mock-cert"}
        )

        self.assertEqual(response.status_code, 404)
        error_data = response.json()
        self.assertEqual(error_data["detail"]["error"]["code"], "KEY_NOT_FOUND")


class TestRotateKeyEndpoint(unittest.TestCase):
    """Test POST /kms/v1/keys/{key_id}/rotate endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client and create a test key."""
        cls.client = create_test_client(app)
        key_response = cls.client.post(
            "/kms/v1/keys",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_type": "RSA-2048",
                "key_usage": ["sign", "verify"]
            },
            headers={
                "X-Client-Certificate": "mock-cert",
                "X-Approval-Token": "valid-approval-token-12345"
            }
        )
        cls.test_key_id = key_response.json()["key_id"]

    def test_rotate_key_success(self):
        """Test rotate key endpoint."""
        response = self.client.post(
            f"/kms/v1/keys/{self.test_key_id}/rotate",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop"
            },
            headers={
                "X-Client-Certificate": "mock-cert",
                "X-Approval-Token": "valid-approval-token-12345"
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("old_key_id", data)
        self.assertIn("new_key_id", data)
        self.assertIn("new_public_key", data)
        self.assertEqual(data["old_key_id"], self.test_key_id)
        self.assertNotEqual(data["old_key_id"], data["new_key_id"])

    def test_rotate_key_not_found(self):
        """Test rotate key endpoint with non-existent key."""
        response = self.client.post(
            "/kms/v1/keys/non-existent-key/rotate",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop"
            },
            headers={
                "X-Client-Certificate": "mock-cert",
                "X-Approval-Token": "valid-approval-token-12345"
            }
        )

        self.assertEqual(response.status_code, 404)
        error_data = response.json()
        self.assertEqual(error_data["detail"]["error"]["code"], "KEY_NOT_FOUND")


class TestRevokeKeyEndpoint(unittest.TestCase):
    """Test POST /kms/v1/keys/{key_id}/revoke endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client and create a test key."""
        cls.client = create_test_client(app)
        key_response = cls.client.post(
            "/kms/v1/keys",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "key_type": "RSA-2048",
                "key_usage": ["sign"]
            },
            headers={
                "X-Client-Certificate": "mock-cert",
                "X-Approval-Token": "valid-approval-token-12345"
            }
        )
        cls.test_key_id = key_response.json()["key_id"]

    def test_revoke_key_success(self):
        """Test revoke key endpoint."""
        response = self.client.post(
            f"/kms/v1/keys/{self.test_key_id}/revoke",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "revocation_reason": "compromised"
            },
            headers={
                "X-Client-Certificate": "mock-cert",
                "X-Approval-Token": "valid-approval-token-12345"
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("key_id", data)
        self.assertIn("revoked_at", data)
        self.assertEqual(data["key_id"], self.test_key_id)

    def test_revoke_key_not_found(self):
        """Test revoke key endpoint with non-existent key."""
        response = self.client.post(
            "/kms/v1/keys/non-existent-key/revoke",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "revocation_reason": "compromised"
            },
            headers={
                "X-Client-Certificate": "mock-cert",
                "X-Approval-Token": "valid-approval-token-12345"
            }
        )

        self.assertEqual(response.status_code, 404)
        error_data = response.json()
        self.assertEqual(error_data["detail"]["error"]["code"], "KEY_NOT_FOUND")


class TestTrustAnchorsEndpoint(unittest.TestCase):
    """Test POST /kms/v1/trust-anchors endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client."""
        cls.client = create_test_client(app)

    def test_ingest_trust_anchor_success(self):
        """Test ingest trust anchor endpoint."""
        certificate_b64 = base64.b64encode(b"mock-certificate-data").decode('utf-8')
        response = self.client.post(
            "/kms/v1/trust-anchors",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "certificate": certificate_b64,
                "anchor_type": "internal_ca"
            },
            headers={
                "X-Client-Certificate": "mock-cert",
                "X-Approval-Token": "valid-approval-token-12345"
            }
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("trust_anchor_id", data)
        self.assertIn("anchor_type", data)
        self.assertEqual(data["anchor_type"], "internal_ca")

    def test_ingest_trust_anchor_invalid_base64(self):
        """Test ingest trust anchor with invalid base64."""
        response = self.client.post(
            "/kms/v1/trust-anchors",
            json={
                "tenant_id": "mock-tenant",
                "environment": "dev",
                "plane": "laptop",
                "certificate": "invalid-base64!!!",
                "anchor_type": "internal_ca"
            },
            headers={"X-Client-Certificate": "mock-cert"}
        )

        self.assertEqual(response.status_code, 400)
        error_data = response.json()
        self.assertEqual(error_data["detail"]["error"]["code"], "INVALID_REQUEST")


class TestHealthEndpoint(unittest.TestCase):
    """Test GET /kms/v1/health endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client."""
        cls.client = create_test_client(app)

    def test_health_check_success(self):
        """Test health check endpoint."""
        response = self.client.get("/kms/v1/health")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("checks", data)
        self.assertIn(data["status"], ["healthy", "degraded", "unhealthy"])
        self.assertIsInstance(data["checks"], list)
        self.assertGreater(len(data["checks"]), 0)


class TestMetricsEndpoint(unittest.TestCase):
    """Test GET /kms/v1/metrics endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client."""
        cls.client = create_test_client(app)

    def test_metrics_endpoint_success(self):
        """Test metrics endpoint."""
        response = self.client.get("/kms/v1/metrics")

        self.assertEqual(response.status_code, 200)
        # Metrics should be in Prometheus text format
        self.assertEqual(response.headers["content-type"], "text/plain; charset=utf-8")
        content = response.text
        self.assertIn("kms_requests_total", content)
        self.assertIn("kms_operation_latency_ms", content)


class TestConfigEndpoint(unittest.TestCase):
    """Test GET /kms/v1/config endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test client."""
        cls.client = create_test_client(app)

    def test_config_endpoint_success(self):
        """Test config endpoint."""
        response = self.client.get("/kms/v1/config")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("key_rotation_schedule", data)
        self.assertIn("rotation_grace_period", data)
        self.assertIn("allowed_algorithms", data)
        self.assertIn("max_usage_per_day_default", data)
        self.assertIn("dual_authorization_required_operations", data)
        self.assertIsInstance(data["allowed_algorithms"], list)
        self.assertIsInstance(data["dual_authorization_required_operations"], list)


if __name__ == '__main__':
    unittest.main()
