@echo off
REM IAM Module Test Execution Batch Script
REM Execute all IAM test suites

echo ========================================
echo IAM Module (M21) Test Execution
echo ========================================
echo.

cd /d "%~dp0\..\.."

echo Running Unit Tests (test_iam_service.py)...
echo ----------------------------------------
python tests\test_iam_service.py
if errorlevel 1 (
    echo Unit tests failed
) else (
    echo Unit tests completed successfully
)
echo.

echo Running Integration Tests (test_iam_routes.py)...
echo ----------------------------------------
python tests\test_iam_routes.py
if errorlevel 1 (
    echo Integration tests failed
) else (
    echo Integration tests completed successfully
)
echo.

echo Running Performance Tests (test_iam_performance.py)...
echo ----------------------------------------
python tests\test_iam_performance.py
if errorlevel 1 (
    echo Performance tests failed
) else (
    echo Performance tests completed successfully
)
echo.

echo ========================================
echo Test Execution Complete
echo ========================================

pause

