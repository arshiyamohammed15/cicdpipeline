"""
Path Normalizer for Hyphenated Directory Names.

Maps hyphenated directory names to valid Python identifiers and fixes import paths.
"""

import sys
from pathlib import Path
from typing import Dict, Optional


class PathNormalizer:
    """Normalizes paths and creates import aliases for hyphenated directories."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.aliases: Dict[str, str] = {}
        self._setup_aliases()

    def _setup_aliases(self):
        """Set up import aliases for hyphenated directories."""
        # Common hyphenated module names
        hyphenated_modules = [
            "identity-access-management",
            "key-management-service",
            "data-governance-privacy",
            "alerting-notification-service",
            "budgeting-rate-limiting-cost-observability",
            "configuration-policy-management",
            "health-reliability-monitoring",
            "evidence-receipt-indexing-service",
            "deployment-infrastructure",
            "signal-ingestion-normalization",
            "user-behaviour-intelligence",
            "knowledge-integrity-discovery",
        ]

        for module_name in hyphenated_modules:
            # Convert to valid Python identifier
            alias = module_name.replace("-", "_")
            self.aliases[module_name] = alias

            # Add to sys.modules if module exists
            module_path = (
                self.project_root
                / "src"
                / "cloud_services"
                / "shared-services"
                / module_name
            )
            if module_path.exists():
                # Create import alias
                import importlib.util

                try:
                    # Try to load module
                    spec = importlib.util.spec_from_file_location(
                        alias, module_path / "__init__.py"
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[alias] = module
                        sys.modules[f"src.cloud_services.shared_services.{alias}"] = (
                            module
                        )
                except Exception:
                    pass

    def normalize_path(self, path: Path) -> Path:
        """Normalize a path by replacing hyphens with underscores in module names."""
        parts = list(path.parts)
        normalized_parts = []

        for part in parts:
            if part in self.aliases:
                normalized_parts.append(self.aliases[part])
            else:
                normalized_parts.append(part)

        return Path(*normalized_parts)

    def add_to_sys_path(self, path: Path):
        """Add path to sys.path if not already present."""
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def setup_path_normalization(project_root: Optional[Path] = None):
    """Set up path normalization for the project."""
    if project_root is None:
        project_root = Path(__file__).resolve().parents[2]

    normalizer = PathNormalizer(project_root)
    
    # Add src/ to path
    src_path = project_root / "src"
    normalizer.add_to_sys_path(src_path)

    return normalizer

