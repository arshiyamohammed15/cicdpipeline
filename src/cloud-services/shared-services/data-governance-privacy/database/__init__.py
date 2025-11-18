"""
Database package for Data Governance & Privacy Module (M22).

What: Exposes SQLAlchemy Base and models.
Why: Ensures importers can access ORM models consistently.
"""

from .models import (  # noqa: F401
    Base,
    DataClassification,
    ConsentRecord,
    DataLineage,
    RetentionPolicy,
)
