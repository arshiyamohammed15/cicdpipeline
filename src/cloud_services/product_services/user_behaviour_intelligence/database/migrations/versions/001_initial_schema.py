"""Initial schema migration for UBI Module (EPC-9).

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-01-XX

Per PRD: Complete database schema with time-series partitioning.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply initial schema migration."""
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    
    # Note: Full schema creation is in schema.sql
    # This migration file is a placeholder for Alembic integration
    # In production, schema.sql should be applied first, then Alembic tracks future migrations
    pass


def downgrade() -> None:
    """Revert initial schema migration."""
    # Drop tables in reverse order
    op.drop_table('receipt_dlq')
    op.drop_table('receipt_queue')
    op.drop_table('tenant_configurations')
    op.drop_table('behavioural_signals')
    op.drop_table('behavioural_baselines')
    op.drop_table('behavioural_features')
    op.drop_table('behavioural_events')
    
    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS "pg_trgm"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')

