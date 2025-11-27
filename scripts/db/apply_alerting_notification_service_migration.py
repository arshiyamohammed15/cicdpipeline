"""Apply Alerting & Notification Service schema migration to the alerting database."""
from __future__ import annotations

import argparse
import sys
import sqlite3
from pathlib import Path

# Add repo root to path for imports
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.constitution.path_utils import resolve_alerting_db_path

DEFAULT_DB = resolve_alerting_db_path()
MIGRATION_FILE = Path("src/cloud-services/shared-services/alerting_notification_service/database/migrations/001_extend_schema.sql")


def apply_migration(db_path: Path, migration_path: Path) -> None:
    if not migration_path.is_file():
        raise FileNotFoundError(f"Migration file not found: {migration_path}")
    sql = migration_path.read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as conn:
        conn.executescript(sql)
        conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply Alerting & Notification Service schema migration.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to SQLite database file.")
    parser.add_argument(
        "--migration",
        type=Path,
        default=MIGRATION_FILE,
        help="Path to 001_extend_schema.sql migration file.",
    )
    args = parser.parse_args()
    apply_migration(args.db, args.migration)
    print(f"Applied migration {args.migration} to {args.db}")


if __name__ == "__main__":
    main()

