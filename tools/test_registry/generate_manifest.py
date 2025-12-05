#!/usr/bin/env python3
"""
Test Manifest Generator for ZeroUI 2.0.

Scans the project for test files and generates a JSON manifest with test metadata.
This manifest enables fast test discovery without importing modules.

Usage:
    python tools/test_registry/generate_manifest.py
    python tools/test_registry/generate_manifest.py --update
"""

import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


class TestManifestGenerator:
    """Generates test manifest by scanning test files without importing them."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.manifest: Dict[str, Any] = {
            "version": "1.0.0",
            "generated_at": None,
            "test_files": [],
            "test_count": 0,
            "markers": {},
            "modules": {},
        }

    def scan_test_files(self) -> List[Path]:
        """Scan project for test files."""
        test_files = []
        
        # Scan tests/ directory (new centralized structure)
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            # New structure: tests/cloud_services/{category}/{module}/{test_type}/
            test_files.extend(tests_dir.rglob("test_*.py"))
            test_files.extend(tests_dir.rglob("*_test.py"))
            
            # Also scan old structure for backward compatibility during migration
            # Old structure: tests/{module_name}/ or tests/{category}/
            test_files.extend(tests_dir.rglob("test_*.py"))
            test_files.extend(tests_dir.rglob("*_test.py"))

        # Scan module test directories (old structure - will be removed after migration)
        modules_dir = self.project_root / "src" / "cloud_services"
        if modules_dir.exists():
            for test_dir in modules_dir.rglob("tests"):
                test_files.extend(test_dir.rglob("test_*.py"))
                test_files.extend(test_dir.rglob("*_test.py"))
            
            # Also check __tests__ directories
            for test_dir in modules_dir.rglob("__tests__"):
                test_files.extend(test_dir.rglob("test_*.py"))
                test_files.extend(test_dir.rglob("*_test.py"))

        # Remove duplicates and sort
        test_files = sorted(set(test_files))
        return test_files

    def extract_test_metadata(self, test_file: Path) -> Optional[Dict[str, Any]]:
        """Extract test metadata from file without importing it."""
        try:
            content = test_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(test_file))
        except Exception as e:
            print(f"Warning: Could not parse {test_file}: {e}", file=sys.stderr)
            return None

        metadata = {
            "path": str(test_file.relative_to(self.project_root)),
            "absolute_path": str(test_file),
            "test_classes": [],
            "test_functions": [],
            "markers": set(),
            "imports": [],
            "dependencies": [],
        }

        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    metadata["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    metadata["imports"].append(f"{module}.{alias.name}")

        # Extract test classes and functions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name.startswith("Test"):
                    class_info = {
                        "name": node.name,
                        "methods": [],
                        "markers": self._extract_decorators(node),
                    }
                    # Extract test methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                            method_info = {
                                "name": item.name,
                                "markers": self._extract_decorators(item),
                            }
                            class_info["methods"].append(method_info)
                            metadata["markers"].update(method_info["markers"])
                    metadata["test_classes"].append(class_info)
                    metadata["markers"].update(class_info["markers"])

            elif isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                func_info = {
                    "name": node.name,
                    "markers": self._extract_decorators(node),
                }
                metadata["test_functions"].append(func_info)
                metadata["markers"].update(func_info["markers"])

        # Convert markers set to list
        metadata["markers"] = sorted(list(metadata["markers"]))

        # Extract dependencies from imports
        metadata["dependencies"] = self._extract_dependencies(metadata["imports"])

        # Calculate file hash for change detection
        metadata["hash"] = hashlib.sha256(content.encode()).hexdigest()[:16]

        return metadata

    def _extract_decorators(self, node: ast.AST) -> List[str]:
        """Extract pytest markers from decorators."""
        markers = []
        if not hasattr(node, "decorator_list"):
            return markers

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr == "mark":
                        # @pytest.mark.marker_name
                        if decorator.args:
                            for arg in decorator.args:
                                if isinstance(arg, ast.Constant):
                                    markers.append(arg.value)
                elif isinstance(decorator.func, ast.Name):
                    if decorator.func.id == "pytest":
                        # @pytest.mark.marker_name
                        if decorator.args:
                            for arg in decorator.args:
                                if isinstance(arg, ast.Constant):
                                    markers.append(arg.value)
            elif isinstance(decorator, ast.Attribute):
                # @pytest.mark.marker_name
                markers.append(decorator.attr)
            elif isinstance(decorator, ast.Name):
                # @marker_name
                markers.append(decorator.id)

        return markers

    def _extract_dependencies(self, imports: List[str]) -> List[str]:
        """Extract heavy dependencies that should be lazy-loaded."""
        heavy_deps = [
            "fastapi",
            "sqlalchemy",
            "pydantic",
            "database",
            "services",
            "models",
        ]
        dependencies = []
        for imp in imports:
            for dep in heavy_deps:
                if dep in imp.lower():
                    dependencies.append(imp)
                    break
        return dependencies

    def generate(self, output_path: Optional[Path] = None) -> Path:
        """Generate test manifest."""
        if output_path is None:
            output_path = self.project_root / "artifacts" / "test_manifest.json"

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"Scanning test files in {self.project_root}...")
        test_files = self.scan_test_files()
        print(f"Found {len(test_files)} test files")

        # Extract metadata from each test file
        for test_file in test_files:
            metadata = self.extract_test_metadata(test_file)
            if metadata:
                self.manifest["test_files"].append(metadata)
                # Count tests
                test_count = sum(
                    len(cls["methods"]) for cls in metadata["test_classes"]
                ) + len(metadata["test_functions"])
                self.manifest["test_count"] += test_count

                # Track markers
                for marker in metadata["markers"]:
                    if marker not in self.manifest["markers"]:
                        self.manifest["markers"][marker] = []
                    self.manifest["markers"][marker].append(metadata["path"])

                # Track modules
                module_path = Path(metadata["path"]).parts[0]
                if module_path not in self.manifest["modules"]:
                    self.manifest["modules"][module_path] = []
                self.manifest["modules"][module_path].append(metadata["path"])

        # Add generation timestamp
        from datetime import datetime

        self.manifest["generated_at"] = datetime.utcnow().isoformat()

        # Write manifest
        output_path.write_text(json.dumps(self.manifest, indent=2), encoding="utf-8")
        print(f"Generated manifest: {output_path}")
        print(f"Total tests: {self.manifest['test_count']}")
        print(f"Total markers: {len(self.manifest['markers'])}")
        print(f"Total modules: {len(self.manifest['modules'])}")

        return output_path


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate test manifest")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path for manifest (default: artifacts/test_manifest.json)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update existing manifest (incremental)",
    )
    args = parser.parse_args()

    generator = TestManifestGenerator(PROJECT_ROOT)
    output_path = generator.generate(args.output)

    if args.update:
        print("Manifest updated successfully")
    else:
        print("Manifest generated successfully")


if __name__ == "__main__":
    main()

