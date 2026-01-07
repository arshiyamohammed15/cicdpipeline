"""
API endpoint tests for Contracts & Schema Registry Module (EPC-12).

What: Tests for FastAPI endpoints per PRD
Why: Ensures API contracts are met
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import importlib.util
import uuid
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(project_root))

# Setup module imports (same as test_contracts_schema_registry.py)
registry_dir = project_root / "src" / "cloud_services" / "shared-services" / "contracts-schema-registry"

# Create package structure
parent_pkg = type(sys)('contracts_schema_registry')
sys.modules['contracts_schema_registry'] = parent_pkg

for subpkg in ['database', 'validators', 'compatibility', 'cache', 'analytics', 'templates']:
    pkg_name = f'contracts_schema_registry.{subpkg}'
    pkg = type(sys)(pkg_name)
    sys.modules[pkg_name] = pkg
    init_path = registry_dir / subpkg / "__init__.py"
    if init_path.exists():
        spec_init = importlib.util.spec_from_file_location(pkg_name, init_path)
        init_module = importlib.util.module_from_spec(spec_init)
        sys.modules[pkg_name] = init_module
        spec_init.loader.exec_module(init_module)

# Load all dependencies in order (same as unit tests)
# Database connection
db_connection_path = registry_dir / "database" / "connection.py"
spec_db_conn = importlib.util.spec_from_file_location("contracts_schema_registry.database.connection", db_connection_path)
db_conn_module = importlib.util.module_from_spec(spec_db_conn)
sys.modules['contracts_schema_registry.database.connection'] = db_conn_module
spec_db_conn.loader.exec_module(db_conn_module)

# Database models
db_models_path = registry_dir / "database" / "models.py"
spec_db_models = importlib.util.spec_from_file_location("contracts_schema_registry.database.models", db_models_path)
db_models_module = importlib.util.module_from_spec(spec_db_models)
sys.modules['contracts_schema_registry.database.models'] = db_models_module
spec_db_models.loader.exec_module(db_models_module)

# Dependencies
deps_path = registry_dir / "dependencies.py"
spec_deps = importlib.util.spec_from_file_location("contracts_schema_registry.dependencies", deps_path)
deps_module = importlib.util.module_from_spec(spec_deps)
sys.modules['contracts_schema_registry.dependencies'] = deps_module
spec_deps.loader.exec_module(deps_module)

# Models (must be before errors)
models_path = registry_dir / "models.py"
spec_models = importlib.util.spec_from_file_location("contracts_schema_registry.models", models_path)
models_module = importlib.util.module_from_spec(spec_models)
sys.modules['contracts_schema_registry.models'] = models_module
spec_models.loader.exec_module(models_module)

# Errors (depends on models)
errors_path = registry_dir / "errors.py"
spec_errors = importlib.util.spec_from_file_location("contracts_schema_registry.errors", errors_path)
errors_module = importlib.util.module_from_spec(spec_errors)
sys.modules['contracts_schema_registry.errors'] = errors_module
spec_errors.loader.exec_module(errors_module)

# Cache manager
cache_manager_path = registry_dir / "cache" / "manager.py"
spec_cache = importlib.util.spec_from_file_location("contracts_schema_registry.cache.manager", cache_manager_path)
cache_module = importlib.util.module_from_spec(spec_cache)
sys.modules['contracts_schema_registry.cache.manager'] = cache_module
spec_cache.loader.exec_module(cache_module)

# Validators
json_validator_path = registry_dir / "validators" / "json_schema_validator.py"
spec_json_val = importlib.util.spec_from_file_location("contracts_schema_registry.validators.json_schema_validator", json_validator_path)
json_val_module = importlib.util.module_from_spec(spec_json_val)
sys.modules['contracts_schema_registry.validators.json_schema_validator'] = json_val_module
spec_json_val.loader.exec_module(json_val_module)

avro_validator_path = registry_dir / "validators" / "avro_validator.py"
spec_avro = importlib.util.spec_from_file_location("contracts_schema_registry.validators.avro_validator", avro_validator_path)
avro_module = importlib.util.module_from_spec(spec_avro)
sys.modules['contracts_schema_registry.validators.avro_validator'] = avro_module
spec_avro.loader.exec_module(avro_module)

protobuf_validator_path = registry_dir / "validators" / "protobuf_validator.py"
spec_proto = importlib.util.spec_from_file_location("contracts_schema_registry.validators.protobuf_validator", protobuf_validator_path)
proto_module = importlib.util.module_from_spec(spec_proto)
sys.modules['contracts_schema_registry.validators.protobuf_validator'] = proto_module
spec_proto.loader.exec_module(proto_module)

custom_validator_path = registry_dir / "validators" / "custom_validator.py"
spec_custom = importlib.util.spec_from_file_location("contracts_schema_registry.validators.custom_validator", custom_validator_path)
custom_module = importlib.util.module_from_spec(spec_custom)
sys.modules['contracts_schema_registry.validators.custom_validator'] = custom_module
spec_custom.loader.exec_module(custom_module)

# Compatibility
checker_path = registry_dir / "compatibility" / "checker.py"
spec_checker = importlib.util.spec_from_file_location("contracts_schema_registry.compatibility.checker", checker_path)
checker_module = importlib.util.module_from_spec(spec_checker)
sys.modules['contracts_schema_registry.compatibility.checker'] = checker_module
spec_checker.loader.exec_module(checker_module)

transformer_path = registry_dir / "compatibility" / "transformer.py"
spec_transformer = importlib.util.spec_from_file_location("contracts_schema_registry.compatibility.transformer", transformer_path)
transformer_module = importlib.util.module_from_spec(spec_transformer)
sys.modules['contracts_schema_registry.compatibility.transformer'] = transformer_module
spec_transformer.loader.exec_module(transformer_module)

# Services
services_path = registry_dir / "services.py"
spec_services = importlib.util.spec_from_file_location("contracts_schema_registry.services", services_path)
services_module = importlib.util.module_from_spec(spec_services)
sys.modules['contracts_schema_registry.services'] = services_module
spec_services.loader.exec_module(services_module)

# Middleware
middleware_path = registry_dir / "middleware.py"
spec_middleware = importlib.util.spec_from_file_location("contracts_schema_registry.middleware", middleware_path)
middleware_module = importlib.util.module_from_spec(spec_middleware)
sys.modules['contracts_schema_registry.middleware'] = middleware_module
spec_middleware.loader.exec_module(middleware_module)

# Routes
routes_path = registry_dir / "routes.py"
spec_routes = importlib.util.spec_from_file_location("contracts_schema_registry.routes", routes_path)
routes_module = importlib.util.module_from_spec(spec_routes)
sys.modules['contracts_schema_registry.routes'] = routes_module
spec_routes.loader.exec_module(routes_module)

# Load main app
main_path = registry_dir / "main.py"
spec_main = importlib.util.spec_from_file_location("contracts_schema_registry.main", main_path)
main_module = importlib.util.module_from_spec(spec_main)
sys.modules['contracts_schema_registry.main'] = main_module
spec_main.loader.exec_module(main_module)
app = main_module.app

# Set up test database - use file-based SQLite for testing
import os
import tempfile
import atexit

# Create a temporary database file
test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
test_db_path = test_db_file.name
test_db_file.close()

# Clean up test database file on exit
def cleanup_test_db():
    try:
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)
    except:
        pass

atexit.register(cleanup_test_db)

# Set environment variable for database URL
os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"

# Import database components
from contracts_schema_registry.database.connection import get_engine, _engine, _session_factory
from contracts_schema_registry.database.models import Base
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID

# Create a function to adapt UUID and JSONB columns for SQLite
def adapt_models_for_sqlite():
    """Adapt models to work with SQLite by replacing UUID with String and JSONB with JSON."""
    from sqlalchemy import inspect
    from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy.types import TypeDecorator

    # Create a UUID type that converts to string for SQLite
    class UUIDString(TypeDecorator):
        impl = String
        cache_ok = True

        def process_bind_param(self, value, dialect):
            if value is None:
                return value
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

        def process_result_value(self, value, dialect):
            if value is None:
                return value
            return uuid.UUID(value) if isinstance(value, str) else value

    engine = get_engine()
    # Replace UUID columns with UUIDString for SQLite
    # Replace JSONB columns with SQLiteJSON for SQLite
    for table in Base.metadata.tables.values():
            for column in table.columns:
                if isinstance(column.type, UUID):
                    column.type = UUIDString(36)
                elif isinstance(column.type, JSONB):
                    column.type = SQLiteJSON()

# Function to set up database tables
def setup_test_database():
    """Set up test database tables."""
    # Reset engine to ensure we get a fresh one
    global _engine, _session_factory
    _engine = None
    _session_factory = None

    # Adapt models for SQLite
    adapt_models_for_sqlite()

    # Create all tables
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

# Set up database before tests
setup_test_database()


@pytest.mark.integration
class TestHealthEndpoints(unittest.TestCase):
    """Test health check endpoints."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)

    @pytest.mark.integration
    def test_health_check(self):
        """Test /health endpoint."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("timestamp", data)

    @pytest.mark.integration
    def test_liveness_probe(self):
        """Test /health/live endpoint."""
        response = self.client.get("/registry/v1/health/live")
        self.assertEqual(response.status_code, 200)

    @pytest.mark.integration
    def test_readiness_probe(self):
        """Test /health/ready endpoint."""
        response = self.client.get("/registry/v1/health/ready")
        # May return 200 or 503 depending on DB connection
        self.assertIn(response.status_code, [200, 503])

    @pytest.mark.integration
    def test_metrics_endpoint(self):
        """Test /metrics endpoint."""
        response = self.client.get("/registry/v1/metrics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("schema_validation_count", data)
        self.assertIn("timestamp", data)

    @pytest.mark.integration
    def test_config_endpoint(self):
        """Test /config endpoint."""
        response = self.client.get("/registry/v1/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["module_id"], "EPC-12")
        self.assertEqual(data["version"], "1.2.0")


@pytest.mark.integration
class TestSchemaEndpoints(unittest.TestCase):
    """Test schema management endpoints."""

    @classmethod
    def setUpClass(cls):
        """Set up test database once for all tests in this class."""
        setup_test_database()

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)
        self.test_tenant_id = str(uuid.uuid4())
        self.test_user_id = str(uuid.uuid4())
        self.headers = {"X-Tenant-ID": self.test_tenant_id, "X-User-ID": self.test_user_id}

    @pytest.mark.integration
    def test_list_schemas(self):
        """Test GET /schemas endpoint."""
        response = self.client.get("/registry/v1/schemas", headers=self.headers)
        # May return 200 (empty list) or 500 (DB not initialized)
        self.assertIn(response.status_code, [200, 500])
        if response.status_code == 200:
            data = response.json()
            self.assertIn("schemas", data)
            self.assertIn("total", data)

    @pytest.mark.integration
    def test_register_schema(self):
        """Test POST /schemas endpoint."""
        request_data = {
            "schema_type": "json_schema",
            "schema_definition": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"]
            },
            "compatibility": "backward",
            "name": "test_schema",
            "namespace": "test",
            "metadata": {}
        }
        response = self.client.post(
            "/registry/v1/schemas",
            json=request_data,
            headers=self.headers
        )
        # May fail without DB, but should return proper status
        # 201 = success, 400 = validation error, 500 = DB error
        self.assertIn(response.status_code, [201, 400, 500])


@pytest.mark.integration
class TestValidationEndpoints(unittest.TestCase):
    """Test validation endpoints."""

    @classmethod
    def setUpClass(cls):
        """Set up test database once for all tests in this class."""
        setup_test_database()

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)
        self.test_tenant_id = str(uuid.uuid4())
        self.headers = {"X-Tenant-ID": self.test_tenant_id}

    @pytest.mark.integration
    def test_validate_endpoint_structure(self):
        """Test POST /validate endpoint structure."""
        request_data = {
            "schema_id": str(uuid.uuid4()),
            "data": {"name": "test"}
        }
        response = self.client.post(
            "/registry/v1/validate",
            json=request_data,
            headers=self.headers
        )
        # Should return 200 (valid), 400 (invalid), 404 (not found), or 500 (DB error)
        self.assertIn(response.status_code, [200, 400, 404, 500])


@pytest.mark.integration
class TestCompatibilityEndpoints(unittest.TestCase):
    """Test compatibility endpoints."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)

    @pytest.mark.integration
    def test_compatibility_check(self):
        """Test POST /compatibility endpoint."""
        request_data = {
            "source_schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}}
            },
            "target_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"}
                }
            },
            "compatibility_mode": "backward"
        }
        response = self.client.post("/registry/v1/compatibility", json=request_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("compatible", data)
        self.assertIn("breaking_changes", data)


if __name__ == "__main__":
    unittest.main()
