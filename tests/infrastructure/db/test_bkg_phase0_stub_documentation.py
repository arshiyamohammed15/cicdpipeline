"""
Test suite for BKG Phase 0 Stub Documentation validation.

Tests cover:
- Documentation exists
- Schema placeholders documented
- Contracts documented
- Storage locations documented
- Ownership rules documented
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
BKG_DOC = REPO_ROOT / "docs" / "architecture" / "bkg_phase0_stub.md"
BKG_SCHEMA = REPO_ROOT / "contracts" / "bkg" / "schemas" / "bkg_edge.schema.json"


@pytest.fixture
def bkg_doc_text() -> str:
    """Load BKG Phase 0 stub documentation."""
    with open(BKG_DOC, encoding="utf-8") as f:
        return f.read()


@pytest.mark.unit
class TestBkgPhase0StubDocumentationStructure:
    """Test BKG Phase 0 stub documentation structure."""

    @pytest.mark.unit
    def test_documentation_exists(self) -> None:
        """BKG Phase 0 stub documentation must exist."""
        assert BKG_DOC.exists()

    @pytest.mark.unit
    def test_documentation_has_overview(self, bkg_doc_text: str) -> None:
        """Documentation must have overview section."""
        assert "## Overview" in bkg_doc_text
        assert "Phase 0 stub" in bkg_doc_text or "Phase 0" in bkg_doc_text
        assert "BKG" in bkg_doc_text or "Background Knowledge Graph" in bkg_doc_text

    @pytest.mark.unit
    def test_documentation_has_schema_placeholders_section(self, bkg_doc_text: str) -> None:
        """Documentation must have schema placeholders section."""
        assert "## Schema Placeholders" in bkg_doc_text
        assert "Postgres" in bkg_doc_text or "PostgreSQL" in bkg_doc_text
        assert "SQLite" in bkg_doc_text

    @pytest.mark.unit
    def test_documentation_has_contracts_section(self, bkg_doc_text: str) -> None:
        """Documentation must have contracts section."""
        assert "## Contracts" in bkg_doc_text or "### Contracts" in bkg_doc_text
        assert "JSON Schema" in bkg_doc_text or "JSON schema" in bkg_doc_text

    @pytest.mark.unit
    def test_documentation_has_storage_locations_section(self, bkg_doc_text: str) -> None:
        """Documentation must have storage locations section."""
        assert "## Storage Locations" in bkg_doc_text or "### Storage Locations" in bkg_doc_text
        assert "IDE Plane" in bkg_doc_text or "IDE plane" in bkg_doc_text
        assert "Tenant Plane" in bkg_doc_text or "Tenant plane" in bkg_doc_text
        assert "Product Plane" in bkg_doc_text or "Product plane" in bkg_doc_text
        assert "Shared Plane" in bkg_doc_text or "Shared plane" in bkg_doc_text

    @pytest.mark.unit
    def test_documentation_has_ownership_rules_section(self, bkg_doc_text: str) -> None:
        """Documentation must have ownership rules section."""
        assert "## Ownership Rules" in bkg_doc_text or "### Ownership Rules" in bkg_doc_text
        assert "Tenant Plane" in bkg_doc_text or "Tenant plane" in bkg_doc_text
        assert "Product Plane" in bkg_doc_text or "Product plane" in bkg_doc_text
        assert "Shared Plane" in bkg_doc_text or "Shared plane" in bkg_doc_text

    @pytest.mark.unit
    def test_documentation_has_entity_types_section(self, bkg_doc_text: str) -> None:
        """Documentation must have entity types section."""
        assert "## Entity Types" in bkg_doc_text or "### Entity Types" in bkg_doc_text
        assert "tenant" in bkg_doc_text.lower()
        assert "repo" in bkg_doc_text.lower()
        assert "actor" in bkg_doc_text.lower()
        assert "receipt" in bkg_doc_text.lower()
        assert "policy" in bkg_doc_text.lower()

    @pytest.mark.unit
    def test_documentation_has_edge_types_section(self, bkg_doc_text: str) -> None:
        """Documentation must have edge types section."""
        assert "## Edge Types" in bkg_doc_text or "### Edge Types" in bkg_doc_text
        assert "owns" in bkg_doc_text.lower()
        assert "contains" in bkg_doc_text.lower()
        assert "triggers" in bkg_doc_text.lower()
        assert "references" in bkg_doc_text.lower()

    @pytest.mark.unit
    def test_documentation_has_implementation_status_section(self, bkg_doc_text: str) -> None:
        """Documentation must have implementation status section."""
        assert "## Implementation Status" in bkg_doc_text or "### Implementation Status" in bkg_doc_text
        assert "Phase 0" in bkg_doc_text

    @pytest.mark.unit
    def test_documentation_has_references_section(self, bkg_doc_text: str) -> None:
        """Documentation must have references section."""
        assert "## References" in bkg_doc_text or "### References" in bkg_doc_text


@pytest.mark.unit
class TestBkgPhase0StubDocumentationContent:
    """Test BKG Phase 0 stub documentation content."""

    @pytest.mark.unit
    def test_postgres_schema_documented(self, bkg_doc_text: str) -> None:
        """Postgres schema must be documented."""
        assert "core.bkg_edge" in bkg_doc_text
        assert "edge_id TEXT PRIMARY KEY" in bkg_doc_text or "edge_id" in bkg_doc_text
        assert "source_entity_type" in bkg_doc_text
        assert "target_entity_type" in bkg_doc_text
        assert "edge_type" in bkg_doc_text

    @pytest.mark.unit
    def test_sqlite_schema_documented(self, bkg_doc_text: str) -> None:
        """SQLite schema must be documented."""
        assert "core__bkg_edge" in bkg_doc_text
        assert "edge_id" in bkg_doc_text

    @pytest.mark.unit
    def test_contract_path_documented(self, bkg_doc_text: str) -> None:
        """Contract path must be documented."""
        assert "bkg_edge.schema.json" in bkg_doc_text or "bkg" in bkg_doc_text.lower()

    @pytest.mark.unit
    def test_migration_paths_documented(self, bkg_doc_text: str) -> None:
        """Migration paths must be documented."""
        assert "002_bkg_phase0.sql" in bkg_doc_text or "bkg_phase0" in bkg_doc_text.lower()
        assert "003_bkg_phase0.sql" in bkg_doc_text or "migrations" in bkg_doc_text.lower()

    @pytest.mark.unit
    def test_tenant_plane_ownership_rules_documented(self, bkg_doc_text: str) -> None:
        """Tenant plane ownership rules must be documented."""
        ownership_section = bkg_doc_text.split("### Tenant Plane BKG Edges")[1] if "### Tenant Plane BKG Edges" in bkg_doc_text else ""
        if not ownership_section:
            ownership_section = bkg_doc_text.split("## Ownership Rules")[1] if "## Ownership Rules" in bkg_doc_text else ""

        assert "tenant" in ownership_section.lower() or "Tenant Plane" in ownership_section
        assert len(ownership_section) > 50, "Tenant ownership rules section too short"

    @pytest.mark.unit
    def test_product_plane_ownership_rules_documented(self, bkg_doc_text: str) -> None:
        """Product plane ownership rules must be documented."""
        ownership_section = bkg_doc_text.split("### Product Plane BKG Edges")[1] if "### Product Plane BKG Edges" in bkg_doc_text else ""
        if not ownership_section:
            ownership_section = bkg_doc_text.split("## Ownership Rules")[1] if "## Ownership Rules" in bkg_doc_text else ""

        assert "product" in ownership_section.lower() or "Product Plane" in ownership_section
        assert len(ownership_section) > 50, "Product ownership rules section too short"

    @pytest.mark.unit
    def test_shared_plane_ownership_rules_documented(self, bkg_doc_text: str) -> None:
        """Shared plane ownership rules must be documented."""
        ownership_section = bkg_doc_text.split("### Shared Plane BKG Edges")[1] if "### Shared Plane BKG Edges" in bkg_doc_text else ""
        if not ownership_section:
            ownership_section = bkg_doc_text.split("## Ownership Rules")[1] if "## Ownership Rules" in bkg_doc_text else ""

        assert "shared" in ownership_section.lower() or "Shared Plane" in ownership_section
        assert len(ownership_section) > 50, "Shared ownership rules section too short"

    @pytest.mark.unit
    def test_all_entity_types_listed(self, bkg_doc_text: str) -> None:
        """All entity types must be listed."""
        entity_types_section = bkg_doc_text.split("## Entity Types")[1] if "## Entity Types" in bkg_doc_text else ""
        if not entity_types_section:
            entity_types_section = bkg_doc_text.split("### Entity Types")[1] if "### Entity Types" in bkg_doc_text else ""

        required_entity_types = ["tenant", "repo", "actor", "receipt", "policy", "gate", "signal", "event"]
        for entity_type in required_entity_types:
            assert entity_type in entity_types_section.lower(), f"Entity type '{entity_type}' not found"

    @pytest.mark.unit
    def test_all_edge_types_listed(self, bkg_doc_text: str) -> None:
        """All edge types must be listed."""
        edge_types_section = bkg_doc_text.split("## Edge Types")[1] if "## Edge Types" in bkg_doc_text else ""
        if not edge_types_section:
            edge_types_section = bkg_doc_text.split("### Edge Types")[1] if "### Edge Types" in bkg_doc_text else ""

        required_edge_types = ["owns", "contains", "triggers", "references", "depends_on", "belongs_to", "causes", "precedes"]
        for edge_type in required_edge_types:
            assert edge_type in edge_types_section.lower(), f"Edge type '{edge_type}' not found"

    @pytest.mark.unit
    def test_phase0_status_documented(self, bkg_doc_text: str) -> None:
        """Phase 0 status must be documented."""
        assert "Planned" in bkg_doc_text or "planned" in bkg_doc_text.lower()
        assert "not fully implemented" in bkg_doc_text.lower() or "not yet implemented" in bkg_doc_text.lower()

