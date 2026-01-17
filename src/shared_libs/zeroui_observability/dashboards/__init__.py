"""
Dashboard definitions for ZeroUI Observability Layer.

15 dashboards (D1-D15) per PRD Section 6.
"""

from .dashboard_loader import DashboardLoader, load_dashboard

__all__ = ["DashboardLoader", "load_dashboard"]
