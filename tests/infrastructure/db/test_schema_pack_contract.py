"""
Test suite for ZeroUI Schema Pack Contract validation.

Tests cover:
- Canonical schema contract JSON structure
- Contract matches migration SQL files
- Primary key definitions
- BKG edge table inclusion
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PACK_ROOT = REPO_ROOT / "infra" / "db" / "schema_pack"
CONTRACT_PATH = SCHEMA_PACK_ROOT / "canonical_schema_contract.json"
PG_MIGRATION = SCHEMA_PACK_ROOT / "migrations" / "pg" / "001_core.sql"


@pytest.fixture
def contract() -> dict:
    """Load canonical schema contract."""
    with open(CONTRACT_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def pg_migration_text() -> str:
    """Load Postgres migration SQL."""
    with open(PG_MIGRATION, encoding="utf-8") as f:
        return f.read()




@pytest.mark.unit
class TestSchemaContractStructure:
    """Test canonical schema contract JSON structure."""

    @pytest.mark.unit
    def test_contract_has_schema_pack_id(self, contract: dict) -> None:
        """Contract must have schema_pack_id."""
        assert "schema_pack_id" in contract
        assert contract["schema_pack_id"] == "zeroui_core_schema_pack"

    @pytest.mark.unit
    def test_contract_has_schema_version(self, contract: dict) -> None:
        """Contract must have schema_version."""
        assert "schema_version" in contract
        assert contract["schema_version"] == "001"

    @pytest.mark.unit
    def test_contract_has_postgres_section(self, contract: dict) -> None:
        """Contract must have postgres section."""
        assert "postgres" in contract
        assert "schema" in contract["postgres"]
        assert contract["postgres"]["schema"] == "core"
        assert "tables" in contract["postgres"]
        assert isinstance(contract["postgres"]["tables"], list)


    @pytest.mark.unit
    def test_contract_tables_have_required_fields(self, contract: dict) -> None:
        """All tables must have name, primary_key, columns."""
        for table in contract["postgres"]["tables"]:
            assert "name" in table
            assert "primary_key" in table
            assert "columns" in table
            assert isinstance(table["primary_key"], list)
            assert isinstance(table["columns"], list)
            assert len(table["primary_key"]) > 0
            assert len(table["columns"]) > 0

    @pytest.mark.unit
    def test_contract_primary_keys_are_in_columns(self, contract: dict) -> None:
        """Primary key columns must be in columns list."""
        for table in contract["postgres"]["tables"]:
            for pk_col in table["primary_key"]:
                assert pk_col in table["columns"], f"Primary key '{pk_col}' not in columns for {table['name']}"

    @pytest.mark.unit
    def test_contract_has_meta_schema_version_table(self, contract: dict) -> None:
        """Contract must include meta.schema_version table."""
        pg_tables = {t["name"]: t for t in contract["postgres"]["tables"]}

        assert "meta.schema_version" in pg_tables

        pg_meta = pg_tables["meta.schema_version"]

        assert pg_meta["primary_key"] == ["schema_pack_id"]
        assert set(pg_meta["columns"]) == {"schema_pack_id", "schema_version", "applied_at"}

    @pytest.mark.unit
    def test_contract_has_bkg_edge_table(self, contract: dict) -> None:
        """Contract must include BKG edge table."""
        pg_tables = {t["name"]: t for t in contract["postgres"]["tables"]}

        assert "core.bkg_edge" in pg_tables

        pg_bkg = pg_tables["core.bkg_edge"]

        assert pg_bkg["primary_key"] == ["edge_id"]

        required_columns = {
            "edge_id",
            "source_entity_type",
            "source_entity_id",
            "target_entity_type",
            "target_entity_id",
            "edge_type",
            "metadata",
            "created_at",
        }
        assert set(pg_bkg["columns"]) == required_columns

    @pytest.mark.unit
    def test_contract_core_tables_count(self, contract: dict) -> None:
        """Contract must have expected number of core tables."""
        # meta.schema_version + core.tenant + core.repo + core.actor + core.receipt_index + core.bkg_edge
        assert len(contract["postgres"]["tables"]) == 6


@pytest.mark.unit
class TestPostgresMigrationMatchesContract:
    """Test Postgres migration SQL matches contract."""

    @pytest.mark.unit
    def test_pg_migration_creates_meta_schema(self, pg_migration_text: str) -> None:
        """Postgres migration must create meta schema."""
        assert "CREATE SCHEMA IF NOT EXISTS meta" in pg_migration_text

    @pytest.mark.unit
    def test_pg_migration_creates_core_schema(self, pg_migration_text: str) -> None:
        """Postgres migration must create core schema."""
        assert "CREATE SCHEMA IF NOT EXISTS core" in pg_migration_text

    @pytest.mark.unit
    def test_pg_migration_creates_meta_schema_version_table(self, pg_migration_text: str) -> None:
        """Postgres migration must create meta.schema_version table."""
        assert "CREATE TABLE IF NOT EXISTS meta.schema_version" in pg_migration_text
        assert "schema_pack_id TEXT PRIMARY KEY" in pg_migration_text
        assert "schema_version TEXT NOT NULL" in pg_migration_text
        assert "applied_at TIMESTAMPTZ NOT NULL DEFAULT now()" in pg_migration_text

    @pytest.mark.unit
    def test_pg_migration_creates_core_tenant_table(self, pg_migration_text: str) -> None:
        """Postgres migration must create core.tenant table."""
        assert "CREATE TABLE IF NOT EXISTS core.tenant" in pg_migration_text
        assert "tenant_id TEXT PRIMARY KEY" in pg_migration_text
        assert "created_at TIMESTAMPTZ NOT NULL DEFAULT now()" in pg_migration_text

    @pytest.mark.unit
    def test_pg_migration_creates_core_repo_table(self, pg_migration_text: str) -> None:
        """Postgres migration must create core.repo table."""
        assert "CREATE TABLE IF NOT EXISTS core.repo" in pg_migration_text
        assert "repo_id TEXT PRIMARY KEY" in pg_migration_text
        assert "tenant_id TEXT NOT NULL REFERENCES core.tenant" in pg_migration_text

    @pytest.mark.unit
    def test_pg_migration_creates_core_actor_table(self, pg_migration_text: str) -> None:
        """Postgres migration must create core.actor table."""
        assert "CREATE TABLE IF NOT EXISTS core.actor" in pg_migration_text
        assert "actor_id TEXT PRIMARY KEY" in pg_migration_text
        assert "tenant_id TEXT NOT NULL REFERENCES core.tenant" in pg_migration_text

    @pytest.mark.unit
    def test_pg_migration_creates_core_receipt_index_table(self, pg_migration_text: str) -> None:
        """Postgres migration must create core.receipt_index table."""
        assert "CREATE TABLE IF NOT EXISTS core.receipt_index" in pg_migration_text
        assert "receipt_id TEXT PRIMARY KEY" in pg_migration_text
        assert "tenant_id TEXT NOT NULL REFERENCES core.tenant" in pg_migration_text
        assert "repo_id TEXT NOT NULL REFERENCES core.repo" in pg_migration_text
        assert "gate_id TEXT NOT NULL" in pg_migration_text
        assert "receipt_type TEXT NOT NULL" in pg_migration_text
        assert "outcome TEXT NOT NULL" in pg_migration_text
        assert "policy_snapshot_hash TEXT NULL" in pg_migration_text
        assert "emitted_at TIMESTAMPTZ NOT NULL" in pg_migration_text
        assert "zu_root_relpath TEXT NOT NULL" in pg_migration_text
        assert "payload_sha256 TEXT NULL" in pg_migration_text

    @pytest.mark.unit
    def test_pg_migration_creates_bkg_edge_table(self, pg_migration_text: str) -> None:
        """Postgres migration must create core.bkg_edge table."""
        assert "CREATE TABLE IF NOT EXISTS core.bkg_edge" in pg_migration_text
        assert "edge_id TEXT PRIMARY KEY" in pg_migration_text
        assert "source_entity_type TEXT NOT NULL" in pg_migration_text
        assert "source_entity_id TEXT NOT NULL" in pg_migration_text
        assert "target_entity_type TEXT NOT NULL" in pg_migration_text
        assert "target_entity_id TEXT NOT NULL" in pg_migration_text
        assert "edge_type TEXT NOT NULL" in pg_migration_text
        assert "metadata JSONB NULL" in pg_migration_text
        assert "created_at TIMESTAMPTZ NOT NULL DEFAULT now()" in pg_migration_text

    @pytest.mark.unit
    def test_pg_migration_creates_bkg_edge_indexes(self, pg_migration_text: str) -> None:
        """Postgres migration must create BKG edge indexes."""
        assert "CREATE INDEX IF NOT EXISTS idx_bkg_edge_source" in pg_migration_text
        assert "CREATE INDEX IF NOT EXISTS idx_bkg_edge_target" in pg_migration_text
        assert "CREATE INDEX IF NOT EXISTS idx_bkg_edge_type" in pg_migration_text
        assert "CREATE INDEX IF NOT EXISTS idx_bkg_edge_source_target" in pg_migration_text

    @pytest.mark.unit
    def test_pg_migration_records_schema_version(self, pg_migration_text: str) -> None:
        """Postgres migration must record schema version."""
        assert "INSERT INTO meta.schema_version" in pg_migration_text
        assert "zeroui_core_schema_pack" in pg_migration_text
        assert "001" in pg_migration_text
        assert "ON CONFLICT" in pg_migration_text

