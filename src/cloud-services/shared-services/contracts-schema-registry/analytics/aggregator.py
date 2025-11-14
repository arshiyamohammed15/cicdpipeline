"""
Analytics aggregator for Contracts & Schema Registry.

What: Aggregates metrics for hourly/daily/weekly/monthly periods per PRD
Why: Provides usage analytics with retention policies
Reads/Writes: Reads raw metrics, writes aggregated analytics to database
Contracts: PRD analytics specification (retention: hourly 7d, daily 90d, weekly 1y, monthly 7y)
Risks: Data retention violations, aggregation errors
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import and_

from ..database.connection import get_session
from ..database.models import SchemaAnalytics

logger = logging.getLogger(__name__)

# Retention periods per PRD
RETENTION_HOURLY_DAYS = 7
RETENTION_DAILY_DAYS = 90
RETENTION_WEEKLY_DAYS = 365
RETENTION_MONTHLY_DAYS = 2555  # 7 years


class AnalyticsAggregator:
    """
    Analytics aggregator.

    Per PRD: Hourly (7-day retention), daily (90-day), weekly (1-year), monthly (7-year).
    """

    def __init__(self):
        """Initialize analytics aggregator."""
        pass

    def aggregate_hourly(
        self,
        schema_id: str,
        tenant_id: str,
        period_start: datetime,
        metrics: Dict[str, Any]
    ) -> None:
        """
        Aggregate hourly metrics.

        Args:
            schema_id: Schema identifier
            tenant_id: Tenant identifier
            period_start: Period start time
            metrics: Metrics dictionary
        """
        period_end = period_start + timedelta(hours=1)

        db = get_session()
        try:
            analytics = SchemaAnalytics(
                analytics_id=uuid.uuid4(),
                schema_id=uuid.UUID(schema_id),
                tenant_id=uuid.UUID(tenant_id),
                period="hourly",
                period_start=period_start,
                period_end=period_end,
                metrics=metrics
            )

            db.add(analytics)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to aggregate hourly metrics: {e}")
            db.rollback()
        finally:
            db.close()

    def aggregate_daily(
        self,
        schema_id: str,
        tenant_id: str,
        period_start: datetime,
        metrics: Dict[str, Any]
    ) -> None:
        """
        Aggregate daily metrics.

        Args:
            schema_id: Schema identifier
            tenant_id: Tenant identifier
            period_start: Period start time
            metrics: Metrics dictionary
        """
        period_end = period_start + timedelta(days=1)

        db = get_session()
        try:
            analytics = SchemaAnalytics(
                analytics_id=uuid.uuid4(),
                schema_id=uuid.UUID(schema_id),
                tenant_id=uuid.UUID(tenant_id),
                period="daily",
                period_start=period_start,
                period_end=period_end,
                metrics=metrics
            )

            db.add(analytics)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to aggregate daily metrics: {e}")
            db.rollback()
        finally:
            db.close()

    def cleanup_expired(self) -> None:
        """
        Clean up expired analytics per retention policies.

        Per PRD: Remove analytics older than retention periods.
        """
        db = get_session()
        try:
            now = datetime.utcnow()

            # Cleanup hourly (older than 7 days)
            hourly_cutoff = now - timedelta(days=RETENTION_HOURLY_DAYS)
            db.query(SchemaAnalytics).filter(
                and_(
                    SchemaAnalytics.period == "hourly",
                    SchemaAnalytics.period_start < hourly_cutoff
                )
            ).delete()

            # Cleanup daily (older than 90 days)
            daily_cutoff = now - timedelta(days=RETENTION_DAILY_DAYS)
            db.query(SchemaAnalytics).filter(
                and_(
                    SchemaAnalytics.period == "daily",
                    SchemaAnalytics.period_start < daily_cutoff
                )
            ).delete()

            # Cleanup weekly (older than 1 year)
            weekly_cutoff = now - timedelta(days=RETENTION_WEEKLY_DAYS)
            db.query(SchemaAnalytics).filter(
                and_(
                    SchemaAnalytics.period == "weekly",
                    SchemaAnalytics.period_start < weekly_cutoff
                )
            ).delete()

            # Cleanup monthly (older than 7 years)
            monthly_cutoff = now - timedelta(days=RETENTION_MONTHLY_DAYS)
            db.query(SchemaAnalytics).filter(
                and_(
                    SchemaAnalytics.period == "monthly",
                    SchemaAnalytics.period_start < monthly_cutoff
                )
            ).delete()

            db.commit()
            logger.info("Cleaned up expired analytics")

        except Exception as e:
            logger.error(f"Failed to cleanup expired analytics: {e}")
            db.rollback()
        finally:
            db.close()
