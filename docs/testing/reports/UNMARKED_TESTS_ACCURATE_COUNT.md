# Unmarked Test Cases - Accurate Count

## Verification Methodology

After thorough analysis, the count of unmarked test cases is:

**343 unmarked test functions out of 2,542 total test functions (13.5%)**

## Verification Steps Performed

1. **Direct Source Code Analysis**: Scanned all Python test files in `tests/` directory
2. **Marker Detection**: Checked for:
   - Function-level markers: `@pytest.mark.*` decorators before test functions
   - Class-level markers: `@pytest.mark.*` decorators on test classes
   - Module-level markers: `pytestmark = pytest.mark.*` (only categorization markers, not filterwarnings)
3. **Manual Verification**: Verified sample files to confirm detection logic
4. **No Global Markers**: Confirmed that conftest.py files do not apply global markers to all tests

## Breakdown

- **Total Test Functions**: 2,542
- **Marked Test Functions**: 2,199 (86.5%)
- **Unmarked Test Functions**: 343 (13.5%)

## Files Verified

Sample files manually checked:
- `tests/system/validators/test_pre_implementation_artifacts.py` - 69 tests, 0 markers
- `tests/bdr/test_models.py` - 10 tests, 0 markers  
- `tests/cccs/test_runtime.py` - 10 tests, 0 markers

These files contain test functions in classes without any `@pytest.mark.*` decorators, confirming they are truly unmarked.

## Note

This count represents tests that have **no explicit pytest marker decorator** at the function, class, or module level. Tests are considered "marked" if they have any `@pytest.mark.*` decorator (e.g., `@pytest.mark.unit`, `@pytest.mark.integration`, etc.).
