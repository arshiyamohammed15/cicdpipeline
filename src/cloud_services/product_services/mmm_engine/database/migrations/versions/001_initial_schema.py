"""
Initial MMM Engine schema migration.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Placeholder: declarative Base metadata will be used in production migrations.
    pass


def downgrade() -> None:
    pass


