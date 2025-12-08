"""
Repository-level pytest configuration.

Ensures the top-level ``src`` directory is on ``sys.path`` so shim packages
(e.g., ``budgeting_rate_limiting_cost_observability``) resolve correctly.

Also handles importing from hyphenated directory names (e.g., detection-engine-core).
"""

from __future__ import annotations

import sys
from pathlib import Path
import importlib.util
import importlib.abc

SRC_PATH = Path(__file__).resolve().parent / "src"
SRC_STR = str(SRC_PATH)
if SRC_STR not in sys.path:
    sys.path.insert(0, SRC_STR)

# Handle hyphenated module directories (e.g., detection-engine-core -> detection_engine_core)
# Also handle modules that need to be imported from product_services
PRODUCT_SERVICES_PATH = SRC_PATH / "cloud_services" / "product_services"
if str(PRODUCT_SERVICES_PATH) not in sys.path:
    sys.path.insert(0, str(PRODUCT_SERVICES_PATH))

MODULE_MAPPINGS = {
    "detection_engine_core": PRODUCT_SERVICES_PATH / "detection-engine-core",
    "mmm_engine": PRODUCT_SERVICES_PATH / "mmm_engine",
    "signal_ingestion_normalization": PRODUCT_SERVICES_PATH / "signal-ingestion-normalization",
}


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
    """Finder that redirects module imports to hyphenated directories."""
    
    def __init__(self, mappings):
        self.mappings = mappings
        self.loaders = {name: HyphenatedModuleLoader(path) for name, path in mappings.items()}
    
    def find_spec(self, name, path, target=None):
        # Check if this is one of our mapped modules
        if name in self.mappings:
            # Importing the package itself
            module_path = self.mappings[name]
            spec = importlib.util.spec_from_file_location(
                name,
                module_path / "__init__.py",
                loader=self.loaders[name],
                submodule_search_locations=[str(module_path)]
            )
            return spec
        elif "." in name:
            # Check if it's a submodule (e.g., detection_engine_core.main or mmm_engine.integrations.iam_client)
            package_name = name.split(".", 1)[0]
            if package_name in self.mappings:
                module_path = self.mappings[package_name]
                submodule_path = name.split(".", 1)[1]
                
                # Handle nested submodules (e.g., mmm_engine.integrations.iam_client)
                parts = submodule_path.split(".")
                current_path = module_path
                
                # Check if it's a file (e.g., main.py)
                file_path = module_path / f"{parts[0]}.py"
                if file_path.exists():
                    spec = importlib.util.spec_from_file_location(
                        name,
                        file_path
                    )
                    return spec
                
                # Check if it's a subdirectory with __init__.py (e.g., integrations/iam_client.py)
                for i, part in enumerate(parts):
                    dir_path = current_path / part
                    file_path = current_path / f"{part}.py"
                    
                    if file_path.exists():
                        # It's a file
                        spec = importlib.util.spec_from_file_location(
                            name,
                            file_path
                        )
                        return spec
                    elif dir_path.is_dir():
                        # It's a directory, continue traversing
                        current_path = dir_path
                        if i == len(parts) - 1:
                            # Last part, check for __init__.py
                            init_file = dir_path / "__init__.py"
                            if init_file.exists():
                                spec = importlib.util.spec_from_file_location(
                                    name,
                                    init_file,
                                    submodule_search_locations=[str(dir_path)]
                                )
                                return spec
                    else:
                        # Not found
                        break
        return None


# Register the finder if not already registered
if not any(isinstance(finder, HyphenatedModuleFinder) for finder in sys.meta_path):
    finder = HyphenatedModuleFinder(MODULE_MAPPINGS)
    sys.meta_path.insert(0, finder)


