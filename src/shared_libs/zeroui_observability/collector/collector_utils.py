"""
Collector utilities for ZeroUI Observability Layer.

Configuration loader, validation, and plane-aware storage path resolution.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Four-Plane storage path patterns per storage-scripts/folder-business-rules.md
_STORAGE_PATTERNS = {
    "ide": "{ZU_ROOT}/ide/telemetry/{signal_type}/dt={yyyy}-{mm}-{dd}/",
    "tenant": "{ZU_ROOT}/tenant/{tenant_id}/{region}/telemetry/{signal_type}/dt={yyyy}-{mm}-{dd}/",
    "product": "{ZU_ROOT}/product/{region}/telemetry/{signal_type}/dt={yyyy}-{mm}-{dd}/",
    "shared": "{ZU_ROOT}/shared/{org_id}/{region}/telemetry/{signal_type}/dt={yyyy}-{mm}-{dd}/",
}


def load_collector_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load collector configuration with environment variable substitution.

    Args:
        config_path: Path to collector config YAML file, or None for default

    Returns:
        Configuration dictionary (for YAML loading)
    """
    if config_path is None:
        config_path = Path(__file__).parent / "collector-config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Collector config not found: {config_path}")

    # Read config file
    with open(config_path, "r", encoding="utf-8") as f:
        config_content = f.read()

    # Substitute environment variables: ${VAR:default}
    def substitute_env(match: re.Match) -> str:
        var_expr = match.group(1)
        if ":" in var_expr:
            var_name, default = var_expr.split(":", 1)
            return os.getenv(var_name, default)
        else:
            return os.getenv(var_expr, "")

    # Replace ${VAR:default} patterns
    config_content = re.sub(r"\$\{([^}]+)\}", substitute_env, config_content)

    # Parse YAML (if yaml available)
    try:
        import yaml
        config = yaml.safe_load(config_content)
        return config
    except ImportError:
        logger.warning("PyYAML not available, returning raw config string")
        return {"raw": config_content}


def resolve_storage_path(
    plane: str,
    signal_type: str,
    tenant_id: Optional[str] = None,
    org_id: Optional[str] = None,
    region: Optional[str] = None,
    date: Optional[str] = None,
) -> str:
    """
    Resolve storage path for telemetry based on Four-Plane architecture.

    Args:
        plane: Plane name (ide, tenant, product, shared)
        signal_type: Signal type (metrics, traces, logs)
        tenant_id: Tenant ID (required for tenant plane)
        org_id: Organization ID (required for shared plane)
        region: Region identifier
        date: Date in format YYYY-MM-DD (defaults to today)

    Returns:
        Resolved storage path

    Raises:
        ValueError: If required parameters are missing for the plane
    """
    if plane not in _STORAGE_PATTERNS:
        raise ValueError(f"Invalid plane: {plane}. Must be one of {list(_STORAGE_PATTERNS.keys())}")

    if signal_type not in ["metrics", "traces", "logs"]:
        raise ValueError(f"Invalid signal_type: {signal_type}. Must be metrics, traces, or logs")

    # Get ZU_ROOT from environment
    zu_root = os.getenv("ZU_ROOT", "D:\\ZeroUI")
    if not zu_root:
        raise ValueError("ZU_ROOT environment variable not set")

    # Get date (default to today)
    if date is None:
        from datetime import datetime
        date = datetime.utcnow().strftime("%Y-%m-%d")
    yyyy, mm, dd = date.split("-")

    # Validate plane-specific requirements
    if plane == "tenant" and not tenant_id:
        raise ValueError("tenant_id required for tenant plane")
    if plane == "shared" and not org_id:
        raise ValueError("org_id required for shared plane")

    # Get region (default from env or empty)
    if not region:
        region = os.getenv("ZU_REGION", "")

    # Build path
    pattern = _STORAGE_PATTERNS[plane]
    path = pattern.format(
        ZU_ROOT=zu_root,
        signal_type=signal_type,
        tenant_id=tenant_id or "",
        org_id=org_id or "",
        region=region or "",
        yyyy=yyyy,
        mm=mm,
        dd=dd,
    )

    return path


def validate_collector_config(config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate collector configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_sections = ["receivers", "processors", "exporters", "service"]
    for section in required_sections:
        if section not in config:
            return False, f"Missing required section: {section}"

    # Validate service pipelines
    if "pipelines" not in config.get("service", {}):
        return False, "Missing service.pipelines section"

    pipelines = config["service"]["pipelines"]
    required_pipelines = ["traces", "metrics", "logs"]
    for pipeline_name in required_pipelines:
        if pipeline_name not in pipelines:
            return False, f"Missing required pipeline: {pipeline_name}"

        pipeline = pipelines[pipeline_name]
        if "receivers" not in pipeline or not pipeline["receivers"]:
            return False, f"Pipeline {pipeline_name} missing receivers"
        if "exporters" not in pipeline or not pipeline["exporters"]:
            return False, f"Pipeline {pipeline_name} missing exporters"

    return True, None


def get_collector_health_endpoint() -> str:
    """
    Get collector health check endpoint.

    Returns:
        Health check endpoint URL
    """
    host = os.getenv("COLLECTOR_HEALTH_HOST", "localhost")
    port = os.getenv("COLLECTOR_HEALTH_PORT", "13133")
    return f"http://{host}:{port}"
