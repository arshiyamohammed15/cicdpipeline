"""
Pytest configuration for M35 tests.

Sets up test fixtures and import paths.
"""

import sys
import os
from pathlib import Path

# Add the module directory to Python path
module_dir = Path(__file__).parent.parent
module_dir_str = str(module_dir)
if module_dir_str not in sys.path:
    sys.path.insert(0, module_dir_str)

# Also add src directory
src_path = Path(__file__).parent.parent.parent.parent.parent
src_path_str = str(src_path)
if src_path_str not in sys.path:
    sys.path.insert(0, src_path_str)

