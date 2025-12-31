#!/usr/bin/env python3
"""
Functional tests for Configuration & Policy Management (EPC-3).

WHAT: Functional validation tests for all acceptance criteria from PRD
WHY: Ensure all functional requirements are met
Reads/Writes: Uses mocks, no real I/O
Contracts: Tests validate functional requirements from PRD
Risks: None - all tests are hermetic

Functional Test Cases (per PRD):
- TC-FUNC-POLICY-001: Policy lifecycle management
- TC-FUNC-CONFIG-001: Configuration drift detection
- TC-FUNC-COMPLIANCE-001: Gold standards compliance
"""

import sys
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(project_root))

# Import using direct file path
import importlib.util

epc3_dir = project_root / "src" / "cloud_services" / "shared-services" / "configuration-policy-management"

# Create parent package structure for relative imports
parent_pkg = type(sys)('configuration_policy_management')
sys.modules['configuration_policy_management'] = parent_pkg

# Load database models first (needed by services)
database_models_path = epc3_dir / "database" / "models.py"
spec_db_models = importlib.util.spec_from_file_location("configuration_policy_management.database.models", database_models_path)
db_models_module = importlib.util.module_from_spec(spec_db_models)
sys.modules['configuration_policy_management.database'] = type(sys)('configuration_policy_management.database')
sys.modules['configuration_policy_management.database.models'] = db_models_module
spec_db_models.loader.exec_module(db_models_module)

# Load database connection
database_connection_path = epc3_dir / "database" / "connection.py"
spec_db_conn = importlib.util.spec_from_file_location("configuration_policy_management.database.connection", database_connection_path)
db_conn_module = importlib.util.module_from_spec(spec_db_conn)
sys.modules['configuration_policy_management.database.connection'] = db_conn_module
spec_db_conn.loader.exec_module(db_conn_module)

# Load models
models_path = epc3_dir / "models.py"
spec_models = importlib.util.spec_from_file_location("configuration_policy_management.models", models_path)
models_module = importlib.util.module_from_spec(spec_models)
sys.modules['configuration_policy_management.models'] = models_module
spec_models.loader.exec_module(models_module)

# Load dependencies
dependencies_path = epc3_dir / "dependencies.py"
spec_deps = importlib.util.spec_from_file_location("configuration_policy_management.dependencies", dependencies_path)
deps_module = importlib.util.module_from_spec(spec_deps)
sys.modules['configuration_policy_management.dependencies'] = deps_module
spec_deps.loader.exec_module(deps_module)

# Load services
services_path = epc3_dir / "services.py"
spec_services = importlib.util.spec_from_file_location("configuration_policy_management.services", services_path)
services_module = importlib.util.module_from_spec(spec_services)
sys.modules['configuration_policy_management.services'] = services_module
spec_services.loader.exec_module(services_module)

from configuration_policy_management.services import (
    PolicyService, ConfigurationService, ConfigurationDriftDetector, ComplianceChecker
)
from configuration_policy_management.dependencies import (
    MockM27EvidenceLedger, MockM29DataPlane, MockM33KeyManagement, MockM34SchemaRegistry
)


def reset_database_state():
    """Reset database connection global state for test isolation."""
    import configuration_policy_management.database.connection as db_conn
    from configuration_policy_management.database.models import Base
    from sqlalchemy.dialects.postgresql import UUID, JSONB
    from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
    from sqlalchemy import String

    # Use the reset function from the connection module
    if hasattr(db_conn, 'reset_connection_state'):
        db_conn.reset_connection_state()
    else:
        # Fallback: manual reset if function doesn't exist
        if db_conn._engine is not None:
            try:
                db_conn._engine.dispose()
            except Exception:
                pass
        db_conn._engine = None
        db_conn._session_factory = None
        db_conn._use_mock = False

    # Ensure DATABASE_URL is set to in-memory SQLite for tests
    import os
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    # If engine gets created, ensure tables exist
    def ensure_tables():
        if db_conn._engine is None or db_conn._engine.dialect.name != 'sqlite':
            return
        # For SQLite, we need to adapt models - but since tests use mocks, this shouldn't be called
        # If it is called, try to create tables with a simple approach
        try:
            # Try creating tables - if it fails due to UUID/JSONB, that's expected
            # The tests should be using mocks anyway
            Base.metadata.create_all(bind=db_conn._engine)
        except Exception:
            # Expected to fail if models aren't adapted - tests should use mocks
            pass

    # Store ensure_tables for later use if needed
    db_conn._ensure_tables = ensure_tables


class TestPolicyLifecycleFunctional(unittest.TestCase):
    """Test policy lifecycle functional requirements (TC-FUNC-POLICY-001)."""

    @classmethod
    def setUpClass(cls):
        """Set up class-level test fixtures."""
        reset_database_state()

    def setUp(self):
        """Set up test fixtures."""
        reset_database_state()
        # Apply patches before creating service
        self.mock_session_obj = MagicMock()
        self.mock_session_obj.add = MagicMock()
        self.mock_session_obj.commit = MagicMock()
        mock_session_context = MagicMock()
        mock_session_context.__enter__ = MagicMock(return_value=self.mock_session_obj)
        mock_session_context.__exit__ = MagicMock(return_value=None)
        self.mock_session = MagicMock(return_value=mock_session_context)

        # Start patches - patch get_engine and get_session_factory to prevent real engine creation
        self.patcher1 = patch('configuration_policy_management.services.get_session', self.mock_session)
        self.patcher2 = patch('configuration_policy_management.database.connection.get_session', self.mock_session)
        self.patcher3 = patch('configuration_policy_management.database.connection.get_engine', MagicMock())
        self.patcher4 = patch('configuration_policy_management.database.connection.get_session_factory', MagicMock())
        self.patcher1.start()
        self.patcher2.start()
        self.patcher3.start()
        self.patcher4.start()

        self.evidence_ledger = MockM27EvidenceLedger()
        self.key_management = MockM33KeyManagement()
        self.schema_registry = MockM34SchemaRegistry()
        self.service = PolicyService(self.evidence_ledger, self.key_management, self.schema_registry)

    def tearDown(self):
        """Clean up test state."""
        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()
        self.patcher4.stop()
        reset_database_state()

    def test_policy_lifecycle_create(self):
        """Test policy creation workflow."""
        from configuration_policy_management.models import CreatePolicyRequest

        request = CreatePolicyRequest(
            name="Test Policy",
            policy_type="security",
            policy_definition={"rules": []},
            scope={"users": ["*"]},
            enforcement_level="enforcement"
        )
        tenant_id = str(uuid.uuid4())
        created_by = str(uuid.uuid4())

        result = self.service.create_policy(request, tenant_id, created_by)

        self.assertIsNotNone(result)
        self.assertEqual(result.status, "draft")


class TestConfigurationDriftFunctional(unittest.TestCase):
    """Test configuration drift detection functional requirements (TC-FUNC-CONFIG-001)."""

    def setUp(self):
        """Set up test fixtures."""
        self.evidence_ledger = MockM27EvidenceLedger()
        self.key_management = MockM33KeyManagement()
        self.detector = ConfigurationDriftDetector(self.evidence_ledger, self.key_management)

    def test_configuration_drift_detection(self):
        """Test configuration drift detection workflow."""
        config_id = str(uuid.uuid4())
        baseline_config = {
            "config_definition": {
                "settings": {
                    "timeout": 30,
                    "encryption": "AES256"
                }
            }
        }
        current_config = {
            "config_definition": {
                "settings": {
                    "timeout": 30,
                    "encryption": "AES128"  # Critical drift
                }
            }
        }

        result = self.detector.detect_drift(config_id, baseline_config, current_config)

        self.assertTrue(result.drift_detected)
        self.assertEqual(result.drift_severity, "critical")
        self.assertTrue(result.remediation_required)


class TestComplianceFunctional(unittest.TestCase):
    """Test gold standards compliance functional requirements (TC-FUNC-COMPLIANCE-001)."""

    def setUp(self):
        """Set up test fixtures."""
        self.evidence_ledger = MockM27EvidenceLedger()
        self.key_management = MockM33KeyManagement()
        self.data_plane = MockM29DataPlane()
        self.checker = ComplianceChecker(self.evidence_ledger, self.key_management, self.data_plane)

    def test_compliance_check_soc2(self):
        """Test SOC2 compliance check workflow."""
        framework = "soc2"
        context = {"tenant_id": str(uuid.uuid4())}

        with patch.object(self.checker, '_load_gold_standard') as mock_load:
            mock_load.return_value = {
                "control_definitions": [
                    {
                        "control_id": "control-1",
                        "severity": "critical",
                        "compliance_rules": [],
                        "implementation_requirements": []
                    }
                ],
                "compliance_rules": []
            }

            result = self.checker.check_compliance(framework, context)

            self.assertIsNotNone(result)
            self.assertIsInstance(result.compliant, bool)
            self.assertGreaterEqual(result.score, 0.0)
            self.assertLessEqual(result.score, 100.0)


if __name__ == '__main__':
    unittest.main()
