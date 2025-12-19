# IAM Module (EPC-1) Test Suite

## Test Files

- `test_iam_service.py`: Unit tests for IAMService and all supporting classes
- `test_iam_routes.py`: Integration tests for all API endpoints
- `test_iam_performance.py`: Performance tests for latency and throughput requirements

## Test Coverage

### Unit Tests (`test_iam_service.py`)
- TokenValidator: Token validation, revocation, jti denylist
- RBACEvaluator: Role mapping, permission evaluation
- ABACEvaluator: Context evaluation (risk, device posture, time)
- PolicyStore: Policy CRUD, versioning, snapshot_id generation
- ReceiptGenerator: Receipt creation, Ed25519 signing, ledger storage
- IAMService: Token verification, decision evaluation, policy management, JIT elevation, metrics

### Integration Tests (`test_iam_routes.py`)
- `/iam/v1/verify`: Token verification endpoint
- `/iam/v1/decision`: Access decision endpoint
- `/iam/v1/policies`: Policy management endpoint
- `/iam/v1/health`: Health check endpoint
- `/iam/v1/metrics`: Metrics endpoint
- `/iam/v1/config`: Configuration endpoint
- Error handling and correlation headers

### Performance Tests (`test_iam_performance.py`)
- Token validation: ≤10ms latency, 2000/s throughput
- Policy evaluation: ≤50ms latency, 1000/s throughput
- Access decision: ≤100ms latency, 500/s throughput
- Authentication: ≤200ms latency, 500/s throughput
- Traffic mix simulation: 70% verify, 25% decision, 5% policies

## Running Tests

```bash
# Run all IAM tests
python -m pytest tests/test_iam_service.py tests/test_iam_routes.py tests/test_iam_performance.py -v

# Run specific test file
python -m pytest tests/test_iam_service.py -v

# Run with coverage
python -m pytest tests/test_iam_service.py --cov=src/cloud-services/shared-services/identity-access-management --cov-report=html
```

## Test Utilities

- `update_snapshot_hashes.py`: Script to calculate and update SHA-256 hashes for GSMD snapshots
- `execute_all_tests.py`: Unified test runner for all IAM test suites
- `run_tests.ps1`: PowerShell script for running tests on Windows
- `run_tests.bat`: Batch script for running tests on Windows

## Notes

- All tests use mocks for external dependencies (PM-7, CCP-6, CCP-1)
- Tests are hermetic (no network, no file system)
- Tests follow deterministic principles (fixed seeds, controlled time)
- Performance tests use scaled-down iterations for test speed
