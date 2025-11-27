"""
Configuration Management for UBI Module (EPC-9).

What: Tenant configuration storage, validation, and versioning
Why: Enable tenant-specific customization per PRD FR-12
Reads/Writes: Configuration storage and retrieval
Contracts: PRD FR-12 (Configuration APIs)
Risks: Configuration validation failures, version conflicts
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from .models import (
    TenantConfigRequest, TenantConfigResponse,
    SignalType, Dimension
)

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """
    Configuration manager for tenant configurations.

    Per PRD FR-12: Manages versioned tenant configurations with validation.
    """

    def __init__(self):
        """Initialize configuration manager."""
        # In-memory store for now - will be database-backed in production
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.default_config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration template.

        Returns:
            Default configuration dictionary
        """
        return {
            "enabled_event_categories": [
                "file_edited", "file_created", "file_deleted",
                "build_failed", "build_succeeded", "test_failed", "test_passed",
                "pr_created", "pr_merged", "pr_closed", "pr_reviewed",
                "commit_created", "commit_pushed",
                "llm_request_submitted", "llm_request_completed", "llm_request_failed",
                "context_switch", "focus_session_started", "focus_session_ended",
                "gate_evaluated", "policy_violation", "override_attempted"
            ],
            "feature_windows": {
                "24h": "24 hours",
                "7d": "7 days",
                "28d": "28 days"
            },
            "aggregation_thresholds": {
                "min_team_size": 5  # k-anonymity requirement
            },
            "enabled_signal_types": [SignalType.RISK, SignalType.OPPORTUNITY, SignalType.INFORMATIONAL],
            "privacy_settings": {
                "data_minimisation": True,
                "purpose_limitation": True
            },
            "anomaly_thresholds": {
                Dimension.ACTIVITY: {"warn": 2.5, "critical": 3.5},
                Dimension.FLOW: {"warn": 2.5, "critical": 3.5},
                Dimension.COLLABORATION: {"warn": 2.5, "critical": 3.5},
                Dimension.AGENT_SYNERGY: {"warn": 2.5, "critical": 3.5}
            },
            "baseline_algorithm": {
                "alpha": 0.1,  # EMA alpha parameter
                "min_data_points_days": 7,  # Warm-up period
                "outlier_std_dev": 3.0  # Outlier exclusion threshold
            }
        }

    def get_config(self, tenant_id: str) -> TenantConfigResponse:
        """
        Get tenant configuration.

        Args:
            tenant_id: Tenant identifier

        Returns:
            TenantConfigResponse with current configuration
        """
        if tenant_id not in self.configs:
            # Return default configuration
            return TenantConfigResponse(
                tenant_id=tenant_id,
                config_version="1.0.0",
                enabled_event_categories=self.default_config["enabled_event_categories"],
                feature_windows=self.default_config["feature_windows"],
                aggregation_thresholds=self.default_config["aggregation_thresholds"],
                enabled_signal_types=self.default_config["enabled_signal_types"],
                privacy_settings=self.default_config["privacy_settings"],
                anomaly_thresholds=self.default_config["anomaly_thresholds"],
                baseline_algorithm=self.default_config["baseline_algorithm"]
            )

        config = self.configs[tenant_id]
        return TenantConfigResponse(
            tenant_id=tenant_id,
            config_version=config["config_version"],
            enabled_event_categories=config["enabled_event_categories"],
            feature_windows=config["feature_windows"],
            aggregation_thresholds=config["aggregation_thresholds"],
            enabled_signal_types=config["enabled_signal_types"],
            privacy_settings=config["privacy_settings"],
            anomaly_thresholds=config["anomaly_thresholds"],
            baseline_algorithm=config["baseline_algorithm"]
        )

    def update_config(
        self,
        tenant_id: str,
        request: TenantConfigRequest,
        created_by: Optional[str] = None
    ) -> TenantConfigResponse:
        """
        Update tenant configuration with versioning.

        Args:
            tenant_id: Tenant identifier
            request: TenantConfigRequest with updates
            created_by: User/service that made the change

        Returns:
            TenantConfigResponse with updated configuration
        """
        # Get current config
        current_config = self.get_config(tenant_id)
        
        # Merge updates
        updated_config = {
            "enabled_event_categories": request.enabled_event_categories or current_config.enabled_event_categories,
            "feature_windows": request.feature_windows or current_config.feature_windows,
            "aggregation_thresholds": request.aggregation_thresholds or current_config.aggregation_thresholds,
            "enabled_signal_types": request.enabled_signal_types or current_config.enabled_signal_types,
            "privacy_settings": request.privacy_settings or current_config.privacy_settings,
            "anomaly_thresholds": request.anomaly_thresholds or current_config.anomaly_thresholds,
            "baseline_algorithm": request.baseline_algorithm or current_config.baseline_algorithm
        }
        
        # Validate configuration
        self._validate_config(updated_config)
        
        # Increment version
        current_version = current_config.config_version
        version_parts = current_version.split(".")
        if len(version_parts) == 3:
            major, minor, patch = version_parts
            new_version = f"{major}.{minor}.{int(patch) + 1}"
        else:
            new_version = "1.0.1"
        
        # Store updated config
        updated_config["config_version"] = new_version
        updated_config["updated_at"] = datetime.utcnow().isoformat()
        updated_config["created_by"] = created_by
        self.configs[tenant_id] = updated_config
        
        logger.info(f"Updated tenant config: tenant_id={tenant_id}, version={new_version}")
        
        return TenantConfigResponse(
            tenant_id=tenant_id,
            config_version=new_version,
            enabled_event_categories=updated_config["enabled_event_categories"],
            feature_windows=updated_config["feature_windows"],
            aggregation_thresholds=updated_config["aggregation_thresholds"],
            enabled_signal_types=updated_config["enabled_signal_types"],
            privacy_settings=updated_config["privacy_settings"],
            anomaly_thresholds=updated_config["anomaly_thresholds"],
            baseline_algorithm=updated_config["baseline_algorithm"]
        )

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration values.

        Args:
            config: Configuration dictionary

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate aggregation thresholds
        if "aggregation_thresholds" in config:
            thresholds = config["aggregation_thresholds"]
            if "min_team_size" in thresholds:
                if thresholds["min_team_size"] < 5:
                    raise ValueError("min_team_size must be at least 5 for k-anonymity")
        
        # Validate anomaly thresholds
        if "anomaly_thresholds" in config:
            thresholds = config["anomaly_thresholds"]
            for dimension, dim_thresholds in thresholds.items():
                if "warn" in dim_thresholds and "critical" in dim_thresholds:
                    if dim_thresholds["warn"] >= dim_thresholds["critical"]:
                        raise ValueError(f"WARN threshold must be less than CRITICAL threshold for {dimension}")
        
        # Validate baseline algorithm
        if "baseline_algorithm" in config:
            algo = config["baseline_algorithm"]
            if "alpha" in algo:
                if not (0.0 < algo["alpha"] <= 1.0):
                    raise ValueError("EMA alpha must be between 0.0 and 1.0")
            if "min_data_points_days" in algo:
                if algo["min_data_points_days"] < 7:
                    raise ValueError("Minimum data points must be at least 7 days")

    def is_event_type_enabled(self, tenant_id: str, event_type: str) -> bool:
        """
        Check if event type is enabled for tenant.

        Args:
            tenant_id: Tenant identifier
            event_type: Event type to check

        Returns:
            True if event type is enabled, False otherwise
        """
        config = self.get_config(tenant_id)
        return event_type in config.enabled_event_categories

    def is_signal_type_enabled(self, tenant_id: str, signal_type: SignalType) -> bool:
        """
        Check if signal type is enabled for tenant.

        Args:
            tenant_id: Tenant identifier
            signal_type: Signal type to check

        Returns:
            True if signal type is enabled, False otherwise
        """
        config = self.get_config(tenant_id)
        return signal_type in config.enabled_signal_types

