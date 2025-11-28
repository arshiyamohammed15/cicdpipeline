"""
Add actor preferences table for FR-14.

Per PRD Section 10.2, creates mmm_actor_preferences table with:
- preference_id, tenant_id, actor_id
- opt_out_categories, snooze_until, preferred_surfaces
- created_at, updated_at
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002_add_actor_preferences"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mmm_actor_preferences",
        sa.Column("preference_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=False),
        sa.Column("actor_id", sa.String(255), nullable=False),
        sa.Column("opt_out_categories", postgresql.JSONB, server_default="[]"),
        sa.Column("snooze_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("preferred_surfaces", postgresql.JSONB, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index(
        "idx_actor_preferences_tenant_actor",
        "mmm_actor_preferences",
        ["tenant_id", "actor_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("idx_actor_preferences_tenant_actor", table_name="mmm_actor_preferences")
    op.drop_table("mmm_actor_preferences")

