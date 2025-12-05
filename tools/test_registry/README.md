# Test Registry System

Fast, scalable test discovery and execution framework for ZeroUI 2.0.

## Problem Solved

- **Slow Collection**: Pytest collection takes hours for large test suites
- **Inconsistent Discovery**: Import errors and module conflicts cause failures
- **Poor Scalability**: Doesn't scale to 100s of test files and 1000s of tests
- **Import Issues**: Hyphenated directory names cause Python import failures

## Solution

Multi-tier test framework with:
1. **Test Manifest**: Pre-indexed JSON manifest of all tests
2. **Lazy Imports**: Defer heavy imports until execution
3. **Parallel Collection**: Use pytest-xdist for parallel discovery
4. **Fast Runner**: Use manifest for instant test selection
5. **Path Normalization**: Fix hyphenated directory import issues

## Quick Start

### 1. Generate Test Manifest

```bash
python tools/test_registry/generate_manifest.py
```

This creates `artifacts/test_manifest.json` with all test metadata.

### 2. Run Tests Using Manifest

```bash
# Run all security tests
python tools/test_registry/test_runner.py --marker security

# Run tests for specific module
python tools/test_registry/test_runner.py --module identity-access-management

# Run specific test file
python tools/test_registry/test_runner.py --file tests/test_iam_service.py

# Run in parallel
python tools/test_registry/test_runner.py --marker unit --parallel
```

### 3. Update Manifest (After Adding Tests)

```bash
python tools/test_registry/generate_manifest.py --update
```

## Performance

**Before**:
- Collection: 2-4 hours
- Execution: Variable
- Total: Hours

**After**:
- Manifest generation: 30-60 seconds (one-time, cached)
- Collection: 10-30 seconds (using manifest)
- Execution: Variable (parallelized)
- Total: Minutes

## Architecture

### Components

1. **generate_manifest.py**: Scans project and generates JSON manifest
2. **test_runner.py**: Fast test runner using manifest
3. **pytest_lazy_collection.py**: Pytest plugin for lazy imports
4. **path_normalizer.py**: Fixes hyphenated directory imports

### Manifest Format

```json
{
  "version": "1.0.0",
  "generated_at": "2025-01-27T12:00:00Z",
  "test_files": [
    {
      "path": "tests/test_iam_service.py",
      "test_classes": [
        {
          "name": "TestIAMService",
          "methods": [
            {"name": "test_verify_token", "markers": ["unit", "security"]}
          ],
          "markers": ["unit"]
        }
      ],
      "markers": ["unit", "security"],
      "dependencies": ["fastapi", "pydantic"]
    }
  ],
  "test_count": 1000,
  "markers": {
    "security": ["tests/test_iam_service.py"],
    "unit": ["tests/test_iam_service.py"]
  }
}
```

## Usage Examples

### Run All Security Tests

```bash
python tools/test_registry/test_runner.py --marker security --parallel
```

### Run Tests for Specific Module

```bash
python tools/test_registry/test_runner.py --module identity-access-management --verbose
```

### Run Tests Matching Pattern

```bash
python tools/test_registry/test_runner.py --file test_iam --test test_verify
```

### Update Manifest After Changes

```bash
python tools/test_registry/generate_manifest.py --update
```

## Integration with CI/CD

Add to `Jenkinsfile`:

```groovy
stage('Generate Test Manifest') {
    steps {
        sh 'python tools/test_registry/generate_manifest.py'
    }
}

stage('Run Tests') {
    steps {
        sh 'python tools/test_registry/test_runner.py --marker unit --parallel'
    }
}
```

## Future Enhancements

1. **Incremental Updates**: Only update changed files in manifest
2. **Test Caching**: Cache test results for faster re-runs
3. **Smart Partitioning**: Automatically partition tests for optimal parallel execution
4. **Dependency Analysis**: Track test dependencies for optimal ordering
5. **Performance Profiling**: Track test execution times for optimization

## Troubleshooting

### Manifest Not Found

```bash
# Generate manifest first
python tools/test_registry/generate_manifest.py
```

### Import Errors

The path normalizer should fix most import issues. If problems persist:

1. Check that `src/` is in `sys.path`
2. Verify hyphenated module names are handled
3. Check `conftest.py` files for import issues

### Slow Collection

1. Ensure manifest is up to date
2. Use `--parallel` flag for parallel execution
3. Filter tests using `--marker`, `--module`, or `--file`

## Contributing

When adding new tests:

1. Follow naming conventions (`test_*.py`)
2. Add appropriate pytest markers
3. Update manifest after adding tests
4. Test with `test_runner.py` to verify discovery

