from types import ModuleType
from pathlib import Path
import importlib
import sys


def test_shim_imports_target_module() -> None:
    module = importlib.reload(
        sys.modules.get("src.key_management_service")
        or importlib.import_module("src.key_management_service")
    )

    assert module is sys.modules["src.key_management_service"]
    assert isinstance(module._module, ModuleType)
    assert module._target_package_dir().is_dir()
    assert Path(module._module.__file__).is_file()

