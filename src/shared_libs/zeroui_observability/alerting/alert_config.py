"""
OBS-10: Alert Config Contract + Loader (zero_ui.alert_config.v1).

Implements config schema, loader, validation, and default ticket-only config examples.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import jsonschema
    from jsonschema import ValidationError, validate
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = Exception  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class WindowConfig:
    """Window duration configuration."""

    short: str  # ISO-8601 duration, e.g., PT5M
    mid: str  # ISO-8601 duration
    long: str  # ISO-8601 duration


@dataclass
class BurnRateConfig:
    """Burn-rate threshold configuration."""

    fast: float
    fast_confirm: float
    slow: float
    slow_confirm: float


@dataclass
class MinTrafficConfig:
    """Minimum traffic configuration."""

    min_total_events: int


@dataclass
class ConfidenceGateConfig:
    """Confidence gate configuration."""

    enabled: bool
    min_confidence: Optional[float] = None  # 0.0 to 1.0


@dataclass
class RoutingConfig:
    """Alert routing configuration."""

    mode: str  # "ticket" | "page"
    target: str  # team/oncall route


@dataclass
class AlertConfig:
    """
    Alert configuration per zero_ui.alert_config.v1 contract.
    
    Represents a single alert rule with multi-window burn-rate thresholds.
    """

    alert_id: str
    slo_id: str
    objective: str
    windows: WindowConfig
    burn_rate: BurnRateConfig
    min_traffic: MinTrafficConfig
    routing: RoutingConfig
    confidence_gate: Optional[ConfidenceGateConfig] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "alert_id": self.alert_id,
            "slo_id": self.slo_id,
            "objective": self.objective,
            "windows": {
                "short": self.windows.short,
                "mid": self.windows.mid,
                "long": self.windows.long,
            },
            "burn_rate": {
                "fast": self.burn_rate.fast,
                "fast_confirm": self.burn_rate.fast_confirm,
                "slow": self.burn_rate.slow,
                "slow_confirm": self.burn_rate.slow_confirm,
            },
            "min_traffic": {
                "min_total_events": self.min_traffic.min_total_events,
            },
            "routing": {
                "mode": self.routing.mode,
                "target": self.routing.target,
            },
        }
        if self.confidence_gate:
            result["confidence_gate"] = {
                "enabled": self.confidence_gate.enabled,
            }
            if self.confidence_gate.min_confidence is not None:
                result["confidence_gate"]["min_confidence"] = self.confidence_gate.min_confidence
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertConfig":
        """Create AlertConfig from dictionary."""
        windows = WindowConfig(
            short=data["windows"]["short"],
            mid=data["windows"]["mid"],
            long=data["windows"]["long"],
        )
        burn_rate = BurnRateConfig(
            fast=data["burn_rate"]["fast"],
            fast_confirm=data["burn_rate"]["fast_confirm"],
            slow=data["burn_rate"]["slow"],
            slow_confirm=data["burn_rate"]["slow_confirm"],
        )
        min_traffic = MinTrafficConfig(
            min_total_events=data["min_traffic"]["min_total_events"],
        )
        routing = RoutingConfig(
            mode=data["routing"]["mode"],
            target=data["routing"]["target"],
        )
        confidence_gate = None
        if "confidence_gate" in data:
            cg_data = data["confidence_gate"]
            confidence_gate = ConfidenceGateConfig(
                enabled=cg_data["enabled"],
                min_confidence=cg_data.get("min_confidence"),
            )
        return cls(
            alert_id=data["alert_id"],
            slo_id=data["slo_id"],
            objective=data["objective"],
            windows=windows,
            burn_rate=burn_rate,
            min_traffic=min_traffic,
            routing=routing,
            confidence_gate=confidence_gate,
        )


class AlertConfigLoader:
    """
    Loader for alert configurations with schema validation.
    
    Supports:
    - Loading from JSON files
    - Schema validation (zero_ui.alert_config.v1)
    - Runtime reload
    - Default ticket-only config examples
    """

    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize loader.
        
        Args:
            schema_path: Optional path to alert_config schema JSON file.
                        If None, uses default schema embedded in class.
        """
        self._schema_path = schema_path
        self._schema: Optional[Dict[str, Any]] = None
        self._configs: Dict[str, AlertConfig] = {}

    def _get_schema(self) -> Dict[str, Any]:
        """Get alert config schema."""
        if self._schema is not None:
            return self._schema

        if self._schema_path and self._schema_path.exists():
            with open(self._schema_path, "r", encoding="utf-8") as f:
                self._schema = json.load(f)
                return self._schema

        # Embedded default schema per PRD Appendix E.1
        self._schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "zero_ui.alert_config.v1",
            "type": "object",
            "required": ["alert_id", "slo_id", "objective", "windows", "burn_rate", "min_traffic", "routing"],
            "properties": {
                "alert_id": {"type": "string"},
                "slo_id": {"type": "string"},
                "objective": {"type": "string", "description": "what the alert protects"},
                "windows": {
                    "type": "object",
                    "required": ["short", "mid", "long"],
                    "properties": {
                        "short": {"type": "string", "description": "ISO-8601 duration, e.g., PT5M"},
                        "mid": {"type": "string", "description": "ISO-8601 duration"},
                        "long": {"type": "string", "description": "ISO-8601 duration"},
                    },
                },
                "burn_rate": {
                    "type": "object",
                    "required": ["fast", "fast_confirm", "slow", "slow_confirm"],
                    "properties": {
                        "fast": {"type": "number"},
                        "fast_confirm": {"type": "number"},
                        "slow": {"type": "number"},
                        "slow_confirm": {"type": "number"},
                    },
                },
                "min_traffic": {
                    "type": "object",
                    "required": ["min_total_events"],
                    "properties": {
                        "min_total_events": {"type": "integer", "minimum": 1},
                    },
                },
                "confidence_gate": {
                    "type": "object",
                    "required": ["enabled"],
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "min_confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                },
                "routing": {
                    "type": "object",
                    "required": ["mode", "target"],
                    "properties": {
                        "mode": {"type": "string", "enum": ["ticket", "page"]},
                        "target": {"type": "string", "description": "team/oncall route"},
                    },
                },
            },
        }
        return self._schema

    def validate_config(self, config_dict: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate config against schema.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not JSONSCHEMA_AVAILABLE:
            logger.warning("jsonschema not available, skipping validation")
            return True, None

        schema = self._get_schema()
        try:
            validate(instance=config_dict, schema=schema)
            return True, None
        except ValidationError as e:
            error_msg = f"Validation failed: {e.message} at {'.'.join(str(p) for p in e.path)}"
            return False, error_msg

    def load_from_file(self, config_path: Path) -> AlertConfig:
        """
        Load alert config from JSON file.
        
        Args:
            config_path: Path to config JSON file
            
        Returns:
            AlertConfig instance
            
        Raises:
            ValueError: If config is invalid
            IOError: If file cannot be read
        """
        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = json.load(f)

        is_valid, error_msg = self.validate_config(config_dict)
        if not is_valid:
            raise ValueError(f"Invalid alert config: {error_msg}")

        config = AlertConfig.from_dict(config_dict)
        self._configs[config.alert_id] = config
        return config

    def load_from_dict(self, config_dict: Dict[str, Any]) -> AlertConfig:
        """
        Load alert config from dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            AlertConfig instance
            
        Raises:
            ValueError: If config is invalid
        """
        is_valid, error_msg = self.validate_config(config_dict)
        if not is_valid:
            raise ValueError(f"Invalid alert config: {error_msg}")

        config = AlertConfig.from_dict(config_dict)
        self._configs[config.alert_id] = config
        return config

    def get_config(self, alert_id: str) -> Optional[AlertConfig]:
        """Get config by alert_id."""
        return self._configs.get(alert_id)

    def list_configs(self) -> List[str]:
        """List all loaded alert IDs."""
        return list(self._configs.keys())

    def reload_config(self, alert_id: str, config_path: Path) -> AlertConfig:
        """
        Reload config from file (runtime reload support).
        
        Args:
            alert_id: Alert ID to reload
            config_path: Path to config JSON file
            
        Returns:
            Reloaded AlertConfig instance
        """
        config = self.load_from_file(config_path)
        if config.alert_id != alert_id:
            raise ValueError(f"Config alert_id mismatch: expected {alert_id}, got {config.alert_id}")
        return config


def load_alert_config(config_path: Path, schema_path: Optional[Path] = None) -> AlertConfig:
    """
    Convenience function to load a single alert config.
    
    Args:
        config_path: Path to config JSON file
        schema_path: Optional path to schema JSON file
        
    Returns:
        AlertConfig instance
    """
    loader = AlertConfigLoader(schema_path=schema_path)
    return loader.load_from_file(config_path)
