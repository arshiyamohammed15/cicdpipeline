"""
Feature Definitions for UBI Module (EPC-9).

What: Defines behavioural feature types and computation rules
Why: Standardize feature computation per PRD FR-2
Reads/Writes: Feature definitions (no I/O)
Contracts: UBI PRD FR-2
Risks: Feature definition errors
"""

from typing import Dict, Any, List
from enum import Enum


class FeatureCategory(str, Enum):
    """Feature category enumeration."""
    ACTIVITY = "activity"
    FLOW = "flow"
    COLLABORATION = "collaboration"
    AGENT_USAGE = "agent_usage"


# Feature definitions per PRD FR-2
FEATURE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    # Activity features
    "event_count_24h": {
        "category": FeatureCategory.ACTIVITY,
        "description": "Total event count in 24 hours",
        "window": "24h",
        "aggregation": "sum"
    },
    "commit_frequency_7d": {
        "category": FeatureCategory.ACTIVITY,
        "description": "Average commits per day over 7 days",
        "window": "7d",
        "aggregation": "mean"
    },
    "build_test_runs_24h": {
        "category": FeatureCategory.ACTIVITY,
        "description": "Build and test runs in 24 hours",
        "window": "24h",
        "aggregation": "sum"
    },
    "pr_creation_rate_7d": {
        "category": FeatureCategory.ACTIVITY,
        "description": "PRs created per week",
        "window": "7d",
        "aggregation": "count"
    },
    
    # Flow & context features
    "context_switches_per_hour": {
        "category": FeatureCategory.FLOW,
        "description": "Average context switches per hour",
        "window": "24h",
        "aggregation": "mean"
    },
    "focus_session_length_avg": {
        "category": FeatureCategory.FLOW,
        "description": "Average focus session length",
        "window": "24h",
        "aggregation": "mean"
    },
    "after_hours_activity_7d": {
        "category": FeatureCategory.FLOW,
        "description": "Activity outside normal hours over 7 days",
        "window": "7d",
        "aggregation": "sum"
    },
    
    # Collaboration features
    "pr_reviewers_count_7d": {
        "category": FeatureCategory.COLLABORATION,
        "description": "Number of unique PR reviewers over 7 days",
        "window": "7d",
        "aggregation": "count_distinct"
    },
    "cross_team_interactions_28d": {
        "category": FeatureCategory.COLLABORATION,
        "description": "Cross-team interactions over 28 days",
        "window": "28d",
        "aggregation": "count"
    },
    
    # Agent usage features
    "llm_requests_per_work_item": {
        "category": FeatureCategory.AGENT_USAGE,
        "description": "LLM requests per work item",
        "window": "7d",
        "aggregation": "mean"
    },
    "override_frequency_7d": {
        "category": FeatureCategory.AGENT_USAGE,
        "description": "Gate override frequency over 7 days",
        "window": "7d",
        "aggregation": "count"
    }
}


def get_feature_definitions() -> Dict[str, Dict[str, Any]]:
    """
    Get all feature definitions.

    Returns:
        Dictionary of feature definitions
    """
    return FEATURE_DEFINITIONS


def get_features_by_category(category: FeatureCategory) -> List[str]:
    """
    Get feature names by category.

    Args:
        category: Feature category

    Returns:
        List of feature names
    """
    return [
        name for name, definition in FEATURE_DEFINITIONS.items()
        if definition["category"] == category
    ]

