"""
Add tenant MMM policy configuration table for FR-13.

Per PRD Section 10.2, creates mmm_tenant_policies table with:
- policy_id, tenant_id (unique)
- enabled_surfaces, quotas, quiet_hours, enabled_action_types
- created_at, updated_at
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "003_add_tenant_policies"
down_revision = "002_add_actor_preferences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mmm_tenant_policies",
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=False, unique=True),
        sa.Column("enabled_surfaces", postgresql.JSONB, server_default='["ide", "ci", "alert"]'),
        sa.Column("quotas", postgresql.JSONB, server_default='{"max_actions_per_day": 10, "max_actions_per_hour": 3}'),
        sa.Column("quiet_hours", postgresql.JSONB, server_default='{"start": 22, "end": 6}'),
        sa.Column("enabled_action_types", postgresql.JSONB, server_default='["mirror", "mentor", "multiplier"]'),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index(
        "idx_tenant_policies_tenant",
        "mmm_tenant_policies",
        ["tenant_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("idx_tenant_policies_tenant", table_name="mmm_tenant_policies")
    op.drop_table("mmm_tenant_policies")

