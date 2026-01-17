"""
Shared utilities for runbook execution.

Provides dashboard access, trace queries, and common runbook operations.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DashboardClient:
    """Client for accessing observability dashboards."""

    def __init__(self, dashboard_base_url: Optional[str] = None):
        """
        Initialize dashboard client.

        Args:
            dashboard_base_url: Base URL for dashboard API
        """
        self._base_url = dashboard_base_url or "http://localhost:3000"

    def query_dashboard(
        self,
        dashboard_id: str,
        panel_id: Optional[str] = None,
        time_range: Optional[Dict[str, str]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query dashboard for data.

        Args:
            dashboard_id: Dashboard ID (D1-D15)
            panel_id: Optional panel ID
            time_range: Optional time range {"from": "...", "to": "..."}
            filters: Optional filters

        Returns:
            Dashboard query results
        """
        # Placeholder implementation
        logger.debug(f"Querying dashboard {dashboard_id}, panel {panel_id}")
        return {"data": [], "status": "success"}

    def get_error_clusters(
        self,
        time_range: Optional[Dict[str, str]] = None,
        component: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get error clusters from D2 (Error Analysis and Debug).

        Args:
            time_range: Optional time range
            component: Optional component filter
            channel: Optional channel filter

        Returns:
            List of error clusters
        """
        return self.query_dashboard("D2", panel_id="d2_p1", filters={"component": component, "channel": channel})

    def get_latency_metrics(
        self,
        time_range: Optional[Dict[str, str]] = None,
        component: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get latency metrics from D12 (Performance Under Load).

        Args:
            time_range: Optional time range
            component: Optional component filter
            channel: Optional channel filter

        Returns:
            Latency metrics (p50, p95, p99)
        """
        return self.query_dashboard("D12", panel_id="d12_p1", filters={"component": component, "channel": channel})

    def get_retrieval_metrics(
        self,
        time_range: Optional[Dict[str, str]] = None,
        corpus_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get retrieval metrics from D9 (Retrieval Evaluation).

        Args:
            time_range: Optional time range
            corpus_id: Optional corpus ID filter

        Returns:
            Retrieval metrics (relevance, timeliness compliance)
        """
        return self.query_dashboard("D9", panel_id="d9_p1", filters={"corpus_id": corpus_id})

    def get_bias_signals(
        self,
        time_range: Optional[Dict[str, str]] = None,
        component: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get bias signals from D6 (Bias Monitoring).

        Args:
            time_range: Optional time range
            component: Optional component filter

        Returns:
            List of bias signals
        """
        return self.query_dashboard("D6", panel_id="d6_p1", filters={"component": component})

    def get_alert_metrics(
        self,
        time_range: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Get alert metrics from D15 (False Positive Control Room).

        Args:
            time_range: Optional time range

        Returns:
            Alert metrics (volume, dedup, rate-limit outcomes)
        """
        return self.query_dashboard("D15", panel_id="d15_p1")


class TraceClient:
    """Client for querying traces."""

    def __init__(self, trace_base_url: Optional[str] = None):
        """
        Initialize trace client.

        Args:
            trace_base_url: Base URL for trace API
        """
        self._base_url = trace_base_url or "http://localhost:4318"

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Get trace by trace_id.

        Args:
            trace_id: Trace ID

        Returns:
            Trace data or None if not found
        """
        logger.debug(f"Getting trace {trace_id}")
        return None

    def get_traces_by_error_class(
        self,
        error_class: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get traces by error class.

        Args:
            error_class: Error class (data, architecture, prompt, etc.)
            limit: Maximum number of traces

        Returns:
            List of trace data
        """
        logger.debug(f"Getting traces for error_class {error_class}")
        return []


class ReplayBundleClient:
    """Client for replay bundle operations."""

    def __init__(self, replay_builder: Optional[Any] = None):
        """
        Initialize replay bundle client.

        Args:
            replay_builder: ReplayBundleBuilder instance
        """
        self._builder = replay_builder

    def create_replay_bundle(
        self,
        trace_id: str,
        tenant_id: str,
        component: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create replay bundle for trace_id.

        Args:
            trace_id: Trace ID
            tenant_id: Tenant ID
            component: Optional component identifier
            channel: Optional channel identifier

        Returns:
            Replay bundle ID or None if creation failed
        """
        if not self._builder:
            logger.warning("ReplayBundleBuilder not available")
            return None

        try:
            bundle = self._builder.build_from_trace_id(
                trace_id,
                tenant_id=tenant_id,
                component=component,
                channel=channel,
            )
            return bundle.replay_id
        except Exception as e:
            logger.error(f"Failed to create replay bundle: {e}")
            return None
