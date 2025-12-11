"""Initial schema: Signal Ingestion Normalization."""
from __future__ import annotations

from pathlib import Path
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql_path = Path(__file__).resolve().parents[2] / "0001_initial.sql"
    op.execute(sql_path.read_text(encoding="utf-8"))


def downgrade() -> None:
    # Destructive downgrades are not defined; leave as no-op.
    pass
