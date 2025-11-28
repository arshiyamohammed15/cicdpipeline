"""
Add dual-channel approval table for FR-6.

Per PRD Section 10.2, creates mmm_dual_channel_approvals table with:
- approval_id, action_id, decision_id, actor_id, approver_id
- first_approval_at, second_approval_at, status
- created_at, updated_at
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "004_add_dual_channel_approvals"
down_revision = "003_add_tenant_policies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mmm_dual_channel_approvals",
        sa.Column("approval_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("action_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", sa.String(255), nullable=False),
        sa.Column("approver_id", sa.String(255), nullable=True),
        sa.Column("first_approval_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("second_approval_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(50), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_dual_channel_action", "mmm_dual_channel_approvals", ["action_id"])
    op.create_index("idx_dual_channel_decision", "mmm_dual_channel_approvals", ["decision_id"])
    op.create_index("idx_dual_channel_status", "mmm_dual_channel_approvals", ["status"])


def downgrade() -> None:
    op.drop_index("idx_dual_channel_status", table_name="mmm_dual_channel_approvals")
    op.drop_index("idx_dual_channel_decision", table_name="mmm_dual_channel_approvals")
    op.drop_index("idx_dual_channel_action", table_name="mmm_dual_channel_approvals")
    op.drop_table("mmm_dual_channel_approvals")

