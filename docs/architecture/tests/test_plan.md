# Test Plan

This document defines the test strategy for ZeroUI 2.0.

## Test Levels

### Unit Tests

**Scope**: Individual functions, classes, modules

**Coverage Target**: 80% code coverage

**Examples**:
- Receipt parser validation
- Gate decision logic
- Policy snapshot verification
- Data transformation functions

**Tools**:
- **TypeScript**: Jest, Vitest
- **Python**: pytest

### Integration Tests

**Scope**: Component interactions

**Coverage Target**: Critical paths covered

**Examples**:
- Edge Agent → Cloud Service communication
- VS Code Extension → Edge Agent communication
- Policy Registry → Client communication
- Receipt flow end-to-end

**Tools**:
- **TypeScript**: Jest with mocks
- **Python**: pytest with fixtures

### End-to-End (E2E) Tests

**Scope**: Complete user workflows

**Coverage Target**: All critical user journeys

**Examples**:
- Developer makes change → Gate evaluates → Receipt generated
- Policy update → Distribution → Client update
- Receipt generation → Storage → Retrieval

**Tools**:
- **VS Code Extension**: VS Code test framework
- **Services**: pytest with test containers

## Test Categories

### Functional Tests

**Purpose**: Verify functionality works as expected

**Examples**:
- Gate decisions are correct
- Receipts are generated correctly
- Policy verification works
- Data transformations are accurate

### Non-Functional Tests

**Purpose**: Verify performance, security, reliability

**Examples**:
- Performance: Response times meet SLOs
- Security: Authentication and authorization work
- Reliability: System handles failures gracefully
- Scalability: System handles load

### Regression Tests

**Purpose**: Prevent regressions

**Examples**:
- All existing functionality still works
- No breaking changes
- Backward compatibility maintained

## Test Data

### Golden Test Data

**Location**: `docs/architecture/tests/golden/`

**Purpose**: Reference test data for deterministic testing

**Contents**:
- Sample receipts (valid and invalid)
- Sample policy snapshots
- Sample gate table data
- Sample evidence packs

### Test Fixtures

**Location**: Per-test or shared fixtures

**Purpose**: Reusable test data

**Examples**:
- Mock receipts
- Mock policy snapshots
- Mock gate tables
- Mock user data

## Test Execution

### Local Execution

```bash
# Python tests
pytest

# TypeScript tests
npm test

# All tests
./scripts/run-all-tests.sh
```

### CI/CD Execution

```bash
# In Jenkinsfile
pytest --cov --cov-report=html
npm test -- --coverage
```

### Test Environments

- **Development**: Local development
- **CI**: Continuous integration
- **Staging**: Pre-production testing
- **Production**: Production smoke tests only

## Test Coverage

### Coverage Targets

- **Unit Tests**: 80% code coverage
- **Integration Tests**: Critical paths covered
- **E2E Tests**: All user journeys covered

### Coverage Reporting

- **HTML Reports**: Generated after test runs
- **CI Integration**: Coverage reported in CI
- **Thresholds**: Fail build if coverage below threshold

## Test Maintenance

### Regular Updates

- **Quarterly**: Review and update test plan
- **After Changes**: Update tests when code changes
- **After Bugs**: Add tests for fixed bugs

### Test Quality

- **Clear Names**: Test names describe what is tested
- **Isolated**: Tests don't depend on each other
- **Fast**: Tests run quickly
- **Deterministic**: Tests produce same results

## Test Strategy by Component

### VS Code Extension

- **Unit Tests**: UI components, receipt parser
- **Integration Tests**: Extension → Edge Agent
- **E2E Tests**: User workflows in VS Code

### Edge Agent

- **Unit Tests**: Delegation logic, validation
- **Integration Tests**: Edge Agent → Cloud Services
- **E2E Tests**: Receipt generation flow

### Cloud Services

- **Unit Tests**: Business logic, API handlers
- **Integration Tests**: Service → Service communication
- **E2E Tests**: API workflows

### Policy Registry

- **Unit Tests**: Policy management, verification
- **Integration Tests**: Policy distribution
- **E2E Tests**: Policy lifecycle

## Test Automation

### Continuous Testing

- **On Commit**: Run unit tests
- **On PR**: Run all tests
- **On Merge**: Run full test suite
- **Scheduled**: Run E2E tests nightly

### Test Reporting

- **Test Results**: Reported in CI
- **Coverage Reports**: Published as artifacts
- **Failure Notifications**: Alert on test failures

## Test Metrics

### Metrics Tracked

- **Test Count**: Number of tests
- **Coverage**: Code coverage percentage
- **Pass Rate**: Test pass rate
- **Execution Time**: Test execution time
- **Flakiness**: Test flakiness rate

### Goals

- **Coverage**: Maintain 80%+ coverage
- **Pass Rate**: 95%+ pass rate
- **Execution Time**: < 10 minutes for full suite
- **Flakiness**: < 1% flaky tests

