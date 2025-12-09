"""
Test fixtures for Detection Engine Core.

Handles importing from the hyphenated directory name (detection-engine-core)
by using a MetaPathFinder to intercept imports.
"""
import pytest
from pathlib import Path
import sys
import importlib.util
import importlib.machinery

# Get the actual module directory (with hyphens)
MODULE_ROOT = Path(__file__).resolve().parents[3] / "src" / "cloud_services" / "product_services" / "detection-engine-core"


class HyphenatedModuleLoader(importlib.abc.Loader):
    """Loader for hyphenated module directories."""
    
    def __init__(self, module_path):
        self.module_path = Path(module_path)
    
    def create_module(self, spec):
        return None  # Use default module creation
    
    def exec_module(self, module):
        # Load __init__.py if it exists
        init_file = self.module_path / "__init__.py"
        if init_file.exists():
            with open(init_file, 'rb') as f:
                code = compile(f.read(), str(init_file), 'exec')
                exec(code, module.__dict__)
        # Set __path__ so submodules can be found
        module.__path__ = [str(self.module_path)]


class HyphenatedModuleFinder(importlib.abc.MetaPathFinder):
    """Finder that redirects 'detection_engine_core' imports to 'detection-engine-core' directory."""
    
    def __init__(self, module_name, module_path):
        self.module_name = module_name
        self.module_path = Path(module_path)
        self.loader = HyphenatedModuleLoader(module_path)
    
    def find_spec(self, name, path, target=None):
        # Only handle detection_engine_core imports
        if name == self.module_name or name.startswith(f"{self.module_name}."):
            if name == self.module_name:
                # Importing the package itself
                spec = importlib.util.spec_from_file_location(
                    name,
                    self.module_path / "__init__.py",
                    loader=self.loader,
                    submodule_search_locations=[str(self.module_path)]
                )
                return spec
            else:
                # Importing a submodule (e.g., detection_engine_core.main)
                submodule = name.split(".", 1)[1]
                module_file = self.module_path / f"{submodule}.py"
                if module_file.exists():
                    spec = importlib.util.spec_from_file_location(
                        name,
                        module_file
                    )
                    return spec
        return None


# Register the finder
if not any(isinstance(finder, HyphenatedModuleFinder) for finder in sys.meta_path):
    finder = HyphenatedModuleFinder("detection_engine_core", MODULE_ROOT)
    sys.meta_path.insert(0, finder)

# Also add the directory to sys.path as a fallback
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

# Ensure bare `import routes` resolves to detection_engine_core.routes for tests.
try:
    import detection_engine_core.routes as de_routes  # type: ignore
    sys.modules["routes"] = de_routes
except Exception:
    pass
