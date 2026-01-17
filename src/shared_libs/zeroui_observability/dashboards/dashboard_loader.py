"""
Dashboard loader for ZeroUI Observability Layer.

Loads and validates dashboard definitions (JSON/YAML).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)

# Dashboard directory
_DASHBOARD_DIR = Path(__file__).parent


class DashboardLoader:
    """
    Loads and validates dashboard definitions.

    Supports JSON and YAML formats.
    """

    def __init__(self, dashboard_dir: Optional[Path] = None):
        """
        Initialize dashboard loader.

        Args:
            dashboard_dir: Directory containing dashboard files (defaults to package dir)
        """
        self._dashboard_dir = dashboard_dir or _DASHBOARD_DIR
        self._dashboards: Dict[str, Dict[str, Any]] = {}

    def load_dashboard(self, dashboard_id: str) -> Optional[Dict[str, Any]]:
        """
        Load dashboard by ID (e.g., "d1", "D1", "d1_system_health").

        Args:
            dashboard_id: Dashboard identifier

        Returns:
            Dashboard dictionary or None if not found
        """
        # Normalize dashboard ID
        dashboard_id = dashboard_id.lower().replace("_", "")
        if not dashboard_id.startswith("d"):
            dashboard_id = f"d{dashboard_id}"

        # Check cache
        if dashboard_id in self._dashboards:
            return self._dashboards[dashboard_id]

        # Try to load from file
        dashboard_file = self._dashboard_dir / f"{dashboard_id}_*.json"
        matching_files = list(self._dashboard_dir.glob(f"{dashboard_id}_*.json"))
        if not matching_files:
            # Try without prefix
            matching_files = list(self._dashboard_dir.glob(f"*{dashboard_id}*.json"))

        if matching_files:
            dashboard_file = matching_files[0]
        else:
            logger.warning(f"Dashboard file not found for {dashboard_id}")
            return None

        try:
            with open(dashboard_file, "r", encoding="utf-8") as f:
                if dashboard_file.suffix == ".yaml" or dashboard_file.suffix == ".yml":
                    if YAML_AVAILABLE:
                        dashboard = yaml.safe_load(f)
                    else:
                        logger.error("PyYAML not available, cannot load YAML dashboard")
                        return None
                else:
                    dashboard = json.load(f)

            self._dashboards[dashboard_id] = dashboard
            return dashboard
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load dashboard {dashboard_id}: {e}")
            return None

    def load_all_dashboards(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all dashboards (D1-D15).

        Returns:
            Dictionary mapping dashboard ID to dashboard definition
        """
        dashboards = {}
        for i in range(1, 16):
            dashboard_id = f"d{i}"
            dashboard = self.load_dashboard(dashboard_id)
            if dashboard:
                dashboards[dashboard_id] = dashboard
        return dashboards

    def validate_dashboard(self, dashboard: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate dashboard schema.

        Args:
            dashboard: Dashboard dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = ["id", "title", "panels"]
        for field in required_fields:
            if field not in dashboard:
                return False, f"Missing required field: {field}"

        # Validate panels
        panels = dashboard.get("panels", [])
        if not isinstance(panels, list):
            return False, "panels must be a list"

        for panel in panels:
            if not isinstance(panel, dict):
                return False, "panel must be a dictionary"
            if "title" not in panel:
                return False, "panel missing title"

        return True, None


def load_dashboard(dashboard_id: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to load a dashboard.

    Args:
        dashboard_id: Dashboard identifier

    Returns:
        Dashboard dictionary or None
    """
    loader = DashboardLoader()
    return loader.load_dashboard(dashboard_id)
