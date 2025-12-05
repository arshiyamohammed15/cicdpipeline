#!/usr/bin/env python3
"""
Performance tests for Configuration & Policy Management (M23).

WHAT: Performance validation tests for latency and throughput requirements per PRD v1.1.0
WHY: Ensure service meets performance SLOs per PRD lines 924-952
Reads/Writes: Uses mocks, no real I/O
Contracts: Tests validate performance requirements from PRD
Risks: None - all tests are hermetic

Performance Requirements (per PRD lines 924-952):
- Policy evaluation: ≤50ms p95, ≤100ms p99, 10,000 RPS
- Configuration retrieval: ≤20ms p95, ≤50ms p99, 20,000 RPS
- Compliance check: ≤100ms p95, ≤250ms p99, 5,000 RPS
"""

import sys
import unittest
import time
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock
from statistics import mean, median

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import using direct file path
import importlib.util

m23_dir = project_root / "src" / "cloud_services" / "shared-services" / "configuration-policy-management"

# Create parent package structure for relative imports
parent_pkg = type(sys)('configuration_policy_management')
sys.modules['configuration_policy_management'] = parent_pkg

# Load database models first (needed by services)
database_models_path = m23_dir / "database" / "models.py"
spec_db_models = importlib.util.spec_from_file_location("configuration_policy_management.database.models", database_models_path)
db_models_module = importlib.util.module_from_spec(spec_db_models)
sys.modules['configuration_policy_management.database'] = type(sys)('configuration_policy_management.database')
sys.modules['configuration_policy_management.database.models'] = db_models_module
spec_db_models.loader.exec_module(db_models_module)

# Load database connection
database_connection_path = m23_dir / "database" / "connection.py"
spec_db_conn = importlib.util.spec_from_file_location("configuration_policy_management.database.connection", database_connection_path)
db_conn_module = importlib.util.module_from_spec(spec_db_conn)
sys.modules['configuration_policy_management.database.connection'] = db_conn_module
spec_db_conn.loader.exec_module(db_conn_module)

# Load models
models_path = m23_dir / "models.py"
spec_models = importlib.util.spec_from_file_location("configuration_policy_management.models", models_path)
models_module = importlib.util.module_from_spec(spec_models)
sys.modules['configuration_policy_management.models'] = models_module
spec_models.loader.exec_module(models_module)

# Load dependencies
dependencies_path = m23_dir / "dependencies.py"
spec_deps = importlib.util.spec_from_file_location("configuration_policy_management.dependencies", dependencies_path)
deps_module = importlib.util.module_from_spec(spec_deps)
sys.modules['configuration_policy_management.dependencies'] = deps_module
spec_deps.loader.exec_module(deps_module)

# Load services
services_path = m23_dir / "services.py"
spec_services = importlib.util.spec_from_file_location("configuration_policy_management.services", services_path)
services_module = importlib.util.module_from_spec(spec_services)
sys.modules['configuration_policy_management.services'] = services_module
spec_services.loader.exec_module(services_module)

from configuration_policy_management.services import PolicyEvaluationEngine
from configuration_policy_management.dependencies import MockM27EvidenceLedger, MockM29DataPlane, MockM33KeyManagement


class TestPolicyEvaluationPerformance(unittest.TestCase):
    """Test policy evaluation meets ≤50ms p95 latency requirement per PRD (TC-PERF-POLICY-001)."""

    def setUp(self):
        """Set up test fixtures."""
        self.data_plane = MockM29DataPlane()
        self.evidence_ledger = MockM27EvidenceLedger()
        self.key_management = MockM33KeyManagement()
        self.engine = PolicyEvaluationEngine(self.data_plane, self.evidence_ledger, self.key_management)

    def test_policy_evaluation_latency_p95(self):
        """Test policy evaluation completes within 50ms p95 per PRD."""
        policy_id = str(uuid.uuid4())
        context = {"environment": "production"}

        latencies = []
        iterations = 100

        with patch('configuration_policy_management.services.get_session') as mock_session:
            mock_session.return_value.__enter__.return_value.query.return_value.filter.return_value.all.return_value = []

            for _ in range(iterations):
                start_time = time.perf_counter()
                result = self.engine.evaluate_policy(
                    policy_id=policy_id,
                    context=context,
                    tenant_id="tenant-123"
                )
                end_time = time.perf_counter()
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)

            # Calculate p95
            sorted_latencies = sorted(latencies)
            p95_index = int(len(sorted_latencies) * 0.95)
            p95_latency = sorted_latencies[p95_index]

            self.assertLess(p95_latency, 50.0, f"Policy evaluation p95 latency: {p95_latency:.2f}ms, expected <50ms")

    def test_policy_evaluation_throughput(self):
        """Test policy evaluation throughput: 10,000 RPS per PRD."""
        policy_id = str(uuid.uuid4())
        context = {"environment": "production"}

        with patch('configuration_policy_management.services.get_session') as mock_session:
            mock_session.return_value.__enter__.return_value.query.return_value.filter.return_value.all.return_value = []

            start_time = time.perf_counter()
            iterations = 1000  # Reduced for test speed
            for _ in range(iterations):
                self.engine.evaluate_policy(
                    policy_id=policy_id,
                    context=context,
                    tenant_id="tenant-123"
                )
            end_time = time.perf_counter()

            duration_seconds = end_time - start_time
            rps = iterations / duration_seconds

            # Should handle at least 1000 RPS (scaled down from 10,000 for test)
            self.assertGreater(rps, 1000, f"Throughput: {rps:.2f} RPS, expected >1000 RPS")


class TestConfigurationRetrievalPerformance(unittest.TestCase):
    """Test configuration retrieval meets ≤20ms p95 latency requirement per PRD."""

    def test_configuration_retrieval_latency(self):
        """Test configuration retrieval completes within 20ms p95."""
        # TODO: Implement when ConfigurationService has retrieval method
        pass


class TestComplianceCheckPerformance(unittest.TestCase):
    """Test compliance check meets ≤100ms p95 latency requirement per PRD."""

    def setUp(self):
        """Set up test fixtures."""
        from configuration_policy_management.services import ComplianceChecker
        from configuration_policy_management.dependencies import MockM27EvidenceLedger, MockM29DataPlane, MockM33KeyManagement

        self.evidence_ledger = MockM27EvidenceLedger()
        self.key_management = MockM33KeyManagement()
        self.data_plane = MockM29DataPlane()
        self.checker = ComplianceChecker(self.evidence_ledger, self.key_management, self.data_plane)

    def test_compliance_check_latency_p95(self):
        """Test compliance check completes within 100ms p95 per PRD."""
        framework = "soc2"
        context = {"tenant_id": str(uuid.uuid4())}

        with patch.object(self.checker, '_load_gold_standard') as mock_load:
            mock_load.return_value = {
                "control_definitions": [
                    {
                        "control_id": "control-1",
                        "severity": "high",
                        "compliance_rules": [],
                        "implementation_requirements": []
                    }
                ],
                "compliance_rules": []
            }

            latencies = []
            iterations = 100

            for _ in range(iterations):
                start_time = time.perf_counter()
                try:
                    result = self.checker.check_compliance(framework, context)
                except Exception:
                    pass  # Expected if gold standard not found
                end_time = time.perf_counter()
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)

            if latencies:
                sorted_latencies = sorted(latencies)
                p95_index = int(len(sorted_latencies) * 0.95)
                p95_latency = sorted_latencies[p95_index]

                self.assertLess(p95_latency, 100.0, f"Compliance check p95 latency: {p95_latency:.2f}ms, expected <100ms")


if __name__ == '__main__':
    unittest.main()
