"""
Pytest configuration for Alerting & Notification Service tests.

SOLUTION: Use absolute imports instead of relative imports.
- Tests use absolute imports: `from alerting_notification_service.database.models import Alert`
- Custom import hook handles hyphenated directory name (alerting-notification-service -> alerting_notification_service)
- Simple, Pythonic, and maintainable
"""
import asyncio
import sys
import importlib.util
import importlib.abc
import importlib.machinery
import types
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

# ============================================================================
# PATH SETUP
# ============================================================================

# Add package root to sys.path so absolute imports work
# __file__ is tests/conftest.py, so:
# parents[0] = tests/
# parents[1] = alerting-notification-service/ (PACKAGE_ROOT)
# parents[2] = shared-services/ (PARENT_DIR)
# parents[3] = cloud_services/
# parents[4] = src/
# parents[5] = ZeroUI2.0/ (REPO_ROOT)
PACKAGE_ROOT = Path(__file__).resolve().parents[1]  # alerting-notification-service/
PARENT_DIR = PACKAGE_ROOT.parent  # shared-services/
REPO_ROOT = Path(__file__).resolve().parents[5]  # ZeroUI2.0/

# CRITICAL: Add repo root FIRST so config.constitution and tests.shared_harness can be imported
# This must be before PARENT_DIR to ensure config and tests packages are found
repo_root_str = str(REPO_ROOT)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)
elif sys.path.index(repo_root_str) > 0:
    # Move REPO_ROOT to front if it's not already first
    sys.path.remove(repo_root_str)
    sys.path.insert(0, repo_root_str)

# Add parent directory to sys.path for alerting-notification-service package
# But ensure it doesn't shadow repo root packages
parent_dir_str = str(PARENT_DIR)
if parent_dir_str not in sys.path:
    # Insert after REPO_ROOT to ensure repo root packages are found first
    if repo_root_str in sys.path:
        idx = sys.path.index(repo_root_str)
        sys.path.insert(idx + 1, parent_dir_str)
    else:
        sys.path.insert(0, parent_dir_str)

# ============================================================================
# CUSTOM IMPORT HOOK FOR HYPHENATED DIRECTORY
# ============================================================================

class HyphenatedPackageImporter(importlib.abc.MetaPathFinder):
    """Import hook to handle alerting-notification-service -> alerting_notification_service mapping."""
    
    def find_spec(self, name, path, target=None):
        # Only handle our specific package
        if name == "alerting_notification_service" or name.startswith("alerting_notification_service."):
            # Map to actual directory name with hyphens
            actual_dir = PARENT_DIR / "alerting-notification-service"
            if not actual_dir.exists():
                return None
            
            # For the root package
            if name == "alerting_notification_service":
                init_file = actual_dir / "__init__.py"
                if actual_dir.is_dir():
                    # Create spec for package
                    loader = self._create_loader(actual_dir, name)
                    spec = importlib.machinery.ModuleSpec(
                        name,
                        loader,
                        origin=str(init_file) if init_file.exists() else None,
                        is_package=True
                    )
                    spec.submodule_search_locations = [str(actual_dir)]
                    return spec
            
            # For submodules
            parts = name.split(".")
            if parts[0] == "alerting_notification_service":
                rel_parts = parts[1:]
                module_path = actual_dir
                for part in rel_parts:
                    module_path = module_path / part
                
                # Try .py file first
                py_file = module_path.with_suffix(".py")
                if py_file.exists():
                    # CRITICAL: Ensure REPO_ROOT is on sys.path before creating spec
                    # This is needed for config.constitution.path_utils imports in config.py
                    if str(REPO_ROOT) not in sys.path:
                        sys.path.insert(0, str(REPO_ROOT))
                    spec = importlib.util.spec_from_file_location(name, py_file)
                    # Replace loader with custom loader that ensures REPO_ROOT is on sys.path
                    if spec and spec.loader:
                        original_loader = spec.loader
                        class CustomFileLoader(importlib.abc.Loader):
                            def __init__(self, original):
                                self.original = original
                            
                            def create_module(self, spec):
                                return self.original.create_module(spec) if hasattr(self.original, 'create_module') else None
                            
                            def exec_module(self, module):
                                # CRITICAL: Ensure REPO_ROOT is on sys.path before executing module
                                # This must be FIRST in sys.path to ensure config package is found before local config.py
                                repo_root_str = str(REPO_ROOT)
                                if repo_root_str not in sys.path:
                                    sys.path.insert(0, repo_root_str)
                                elif sys.path.index(repo_root_str) > 0:
                                    # Move REPO_ROOT to front if it's not already first
                                    sys.path.remove(repo_root_str)
                                    sys.path.insert(0, repo_root_str)
                                
                                # CRITICAL: For config.py specifically, ensure config package import works
                                # Temporarily store the module file path to prevent it from being found as 'config'
                                module_file = getattr(module, '__file__', None)
                                
                                try:
                                    # Execute the module
                                    self.original.exec_module(module)
                                    
                                    # After execution, if this is config.py and it tried to import config.constitution,
                                    # ensure the import succeeded by checking if it's in sys.modules
                                    if module.__name__ == 'alerting_notification_service.config':
                                        # Verify config.constitution is importable
                                        try:
                                            import config.constitution.path_utils
                                        except ImportError:
                                            # If import failed, try to fix it by ensuring repo root config is found
                                            # This should not happen if REPO_ROOT is first in sys.path
                                            pass
                                finally:
                                    # Restore any state if needed
                                    pass
                        spec.loader = CustomFileLoader(original_loader)
                    return spec
                
                # Try package directory
                if module_path.is_dir():
                    init_file = module_path / "__init__.py"
                    spec = importlib.machinery.ModuleSpec(
                        name,
                        self._create_loader(module_path, name),
                        origin=str(init_file) if init_file.exists() else None,
                        is_package=True
                    )
                    spec.submodule_search_locations = [str(module_path)]
                    return spec
        
        return None
    
    def _create_loader(self, path, name):
        """Create a loader for a package directory."""
        class PackageLoader(importlib.abc.Loader):
            def __init__(self, path, name):
                self.path = path
                self.name = name
            
            def create_module(self, spec):
                # Return None to use default module creation
                return None
            
            def exec_module(self, module):
                # CRITICAL: Ensure REPO_ROOT is on sys.path before executing any module code
                # This must be FIRST in sys.path to ensure config package is found before local config.py
                if str(REPO_ROOT) not in sys.path:
                    sys.path.insert(0, str(REPO_ROOT))
                elif sys.path.index(str(REPO_ROOT)) > 0:
                    # Move REPO_ROOT to front if it's not already first
                    sys.path.remove(str(REPO_ROOT))
                    sys.path.insert(0, str(REPO_ROOT))
                
                # Set package attributes
                init_file = self.path / "__init__.py"
                module.__file__ = str(init_file) if init_file.exists() else None
                # CRITICAL: Set __path__ to the actual path passed to loader, not derived path
                module.__path__ = [str(self.path.resolve())]
                module.__package__ = self.name
                
                # Execute __init__.py if it exists
                if init_file.exists():
                    with open(init_file, "rb") as f:
                        code = compile(f.read(), str(init_file), "exec")
                        exec(code, module.__dict__)
                
                # CRITICAL: Re-verify __path__ is correct after execution
                # Some __init__.py files might modify __path__, so we force it back
                if hasattr(module, "__path__") and module.__path__[0] != str(self.path.resolve()):
                    module.__path__ = [str(self.path.resolve())]
        
        return PackageLoader(path, name)

# Install import hook
if not any(isinstance(imp, HyphenatedPackageImporter) for imp in sys.meta_path):
    sys.meta_path.insert(0, HyphenatedPackageImporter())

# ============================================================================
# IMPORT HOOK FOR tests.shared_harness
# ============================================================================

class TestsSharedHarnessImporter(importlib.abc.MetaPathFinder):
    """Import hook to route tests.shared_harness to repo root tests package."""
    
    def find_spec(self, name, path, target=None):
        # Only handle tests.shared_harness imports
        if name == "tests" or name.startswith("tests."):
            # Check if this is tests.shared_harness or a submodule
            if name == "tests.shared_harness" or name.startswith("tests.shared_harness."):
                # Route to repo root tests package
                repo_tests_dir = REPO_ROOT / "tests"
                if repo_tests_dir.exists():
                    if name == "tests.shared_harness":
                        shared_harness_dir = repo_tests_dir / "shared_harness"
                        if shared_harness_dir.exists():
                            init_file = shared_harness_dir / "__init__.py"
                            spec = importlib.machinery.ModuleSpec(
                                name,
                                importlib.machinery.SourceFileLoader(name, str(init_file)),
                                origin=str(init_file) if init_file.exists() else None,
                                is_package=True
                            )
                            spec.submodule_search_locations = [str(shared_harness_dir)]
                            return spec
                    else:
                        # Submodule of tests.shared_harness
                        parts = name.split(".")
                        if len(parts) > 2 and parts[0] == "tests" and parts[1] == "shared_harness":
                            rel_parts = parts[2:]
                            module_path = repo_tests_dir / "shared_harness"
                            for part in rel_parts:
                                module_path = module_path / part
                            
                            py_file = module_path.with_suffix(".py")
                            if py_file.exists():
                                return importlib.util.spec_from_file_location(name, py_file)
                            
                            if module_path.is_dir():
                                init_file = module_path / "__init__.py"
                                spec = importlib.machinery.ModuleSpec(
                                    name,
                                    importlib.machinery.SourceFileLoader(name, str(init_file)),
                                    origin=str(init_file) if init_file.exists() else None,
                                    is_package=True
                                )
                                spec.submodule_search_locations = [str(module_path)]
                                return spec
        return None

# Install import hook for tests.shared_harness
if not any(isinstance(imp, TestsSharedHarnessImporter) for imp in sys.meta_path):
    sys.meta_path.insert(0, TestsSharedHarnessImporter())

# ============================================================================
# PYTEST HOOKS FOR TEST COLLECTION
# ============================================================================

def pytest_configure(config):
    """Ensure REPO_ROOT is on sys.path before test collection and register custom markers."""
    # Register custom pytest markers to avoid warnings
    config.addinivalue_line("markers", "alerting_regression: mark test as an alerting regression test")
    config.addinivalue_line("markers", "alerting_security: mark test as an alerting security test")
    config.addinivalue_line("markers", "alerting_performance: mark test as an alerting performance test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "security: mark test as a security test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    
    # Ensure REPO_ROOT is first in sys.path for tests.shared_harness imports
    repo_root_str = str(REPO_ROOT)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    elif sys.path.index(repo_root_str) > 0:
        sys.path.remove(repo_root_str)
        sys.path.insert(0, repo_root_str)

# CRITICAL: Pre-import the package to ensure it's available
# This ensures the import hook has processed it before test files try to import
try:
    # Force import using the hook
    import alerting_notification_service
    # CRITICAL: ALWAYS correct __path__ to point to actual package directory
    # The import hook may set it incorrectly, so we force it here
    alerting_notification_service.__path__ = [str(PACKAGE_ROOT)]
    # Verify it's correct
    if alerting_notification_service.__path__[0] != str(PACKAGE_ROOT):
        alerting_notification_service.__path__ = [str(PACKAGE_ROOT)]
except ImportError:
    # If import fails, try to manually create the package
    import types
    pkg = types.ModuleType("alerting_notification_service")
    pkg.__path__ = [str(PACKAGE_ROOT)]
    pkg.__package__ = "alerting_notification_service"
    sys.modules["alerting_notification_service"] = pkg

# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def engine():
    """Provide an in-memory SQLite database engine for testing."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    async with test_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
    yield test_engine
    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for testing."""
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def override_dependencies(engine):
    """Override FastAPI dependencies to use test database."""
    from alerting_notification_service.main import app
    from alerting_notification_service.dependencies import get_session
    from sqlalchemy.ext.asyncio import async_sessionmaker
    
    # Ensure tables are created
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_maker() as session:
            yield session
    
    app.dependency_overrides[get_session] = get_test_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client():
    """Provide a FastAPI test client."""
    from alerting_notification_service.main import app
    from fastapi.testclient import TestClient
    # TestClient in FastAPI 0.104.1 uses deprecated httpx app= shortcut
    # This will be fixed by upgrading FastAPI/Starlette to versions compatible with httpx>=0.27
    # For now, we use TestClient and accept the deprecation warning
    return TestClient(app)


@pytest.fixture(scope="function")
def test_client():
    """
    Provide a FastAPI test client with default headers for testing.
    
    Sets default X-Tenant-ID header to 'tenant-integration' for test consistency.
    """
    from alerting_notification_service.main import app
    from fastapi.testclient import TestClient
    # TestClient in FastAPI 0.104.1 uses deprecated httpx app= shortcut
    # This will be fixed by upgrading FastAPI/Starlette to versions compatible with httpx>=0.27
    # For now, we use TestClient and accept the deprecation warning
    client = TestClient(app)
    # Set default tenant header for tests
    client.headers.update({
        "X-Tenant-ID": "tenant-integration",
        "Content-Type": "application/json"
    })
    # Store app reference for tests that need it
    client.app = app
    return client


@pytest.fixture(scope="function")
def perf_runner():
    """
    Provide a PerfRunner instance for performance tests.
    """
    from tests.shared_harness import PerfRunner
    return PerfRunner()
