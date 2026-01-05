"""
Test suite for Memory Model Documentation validation.

Tests cover:
- All 6 memory types are documented
- Each memory type has store mapping
- Each memory type has governance rules
- Plane assignments are correct
- BKG and Semantic Q&A Cache are documented
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
MEMORY_MODEL_DOC = REPO_ROOT / "docs" / "architecture" / "memory_model.md"


@pytest.fixture
def memory_model_text() -> str:
    """Load memory model documentation."""
    with open(MEMORY_MODEL_DOC, encoding="utf-8") as f:
        return f.read()


class TestMemoryModelDocumentationStructure:
    """Test memory model documentation structure."""

    def test_documentation_exists(self) -> None:
        """Memory model documentation must exist."""
        assert MEMORY_MODEL_DOC.exists()

    def test_documentation_has_all_memory_types(self, memory_model_text: str) -> None:
        """Documentation must list all 6 memory types."""
        required_types = [
            "Working Memory",
            "Episodic Memory",
            "Vector DB Memory",
            "SQL DB Memory",
            "File Store",
            "Semantic Q&A Cache",
        ]
        for mem_type in required_types:
            assert mem_type in memory_model_text, f"Memory type '{mem_type}' not found in documentation"

    def test_working_memory_documented(self, memory_model_text: str) -> None:
        """Working Memory must be documented with stores."""
        assert "### 1. Working Memory" in memory_model_text
        assert "IDE Plane" in memory_model_text or "IDE plane" in memory_model_text
        assert "Tenant Plane" in memory_model_text or "Tenant plane" in memory_model_text
        assert "Product Plane" in memory_model_text or "Product plane" in memory_model_text
        assert "Shared Plane" in memory_model_text or "Shared plane" in memory_model_text
        assert "core.tenant" in memory_model_text or "core__tenant" in memory_model_text
        assert "core.repo" in memory_model_text or "core__repo" in memory_model_text
        assert "core.actor" in memory_model_text or "core__actor" in memory_model_text

    def test_episodic_memory_documented(self, memory_model_text: str) -> None:
        """Episodic Memory must be documented with receipts and BKG."""
        assert "### 2. Episodic Memory" in memory_model_text
        assert "Receipts" in memory_model_text or "receipts" in memory_model_text
        assert "BKG" in memory_model_text or "Background Knowledge Graph" in memory_model_text
        assert "core.bkg_edge" in memory_model_text or "core__bkg_edge" in memory_model_text
        assert "JSONL" in memory_model_text

    def test_vector_db_memory_documented(self, memory_model_text: str) -> None:
        """Vector DB Memory must be documented."""
        assert "### 3. Vector DB Memory" in memory_model_text
        assert "pgvector" in memory_model_text or "pgvector" in memory_model_text.lower()
        assert "embedding" in memory_model_text.lower()
        assert "Product Plane" in memory_model_text or "Product plane" in memory_model_text

    def test_sql_db_memory_documented(self, memory_model_text: str) -> None:
        """SQL DB Memory must be documented."""
        assert "### 4. SQL DB Memory" in memory_model_text
        assert "core.bkg_edge" in memory_model_text or "core__bkg_edge" in memory_model_text
        assert "meta.schema_version" in memory_model_text or "meta__schema_version" in memory_model_text

    def test_file_store_documented(self, memory_model_text: str) -> None:
        """File Store must be documented."""
        assert "### 5. File Store" in memory_model_text
        assert "ZU_ROOT" in memory_model_text
        assert "ide/" in memory_model_text or "ide\\" in memory_model_text
        assert "tenant/" in memory_model_text or "tenant\\" in memory_model_text
        assert "product/" in memory_model_text or "product\\" in memory_model_text
        assert "shared/" in memory_model_text or "shared\\" in memory_model_text

    def test_semantic_qa_cache_documented(self, memory_model_text: str) -> None:
        """Semantic Q&A Cache must be documented."""
        assert "### 6. Semantic Q&A Cache" in memory_model_text
        assert "semantic_qa_cache" in memory_model_text or "semantic-qa-cache" in memory_model_text.lower()
        assert "NOT used for gating" in memory_model_text or "not used for gating" in memory_model_text.lower()
        assert "Product Plane" in memory_model_text or "Product plane" in memory_model_text

    def test_bkg_phase0_stub_documented(self, memory_model_text: str) -> None:
        """BKG Phase 0 stub status must be documented."""
        assert "Phase 0 stub" in memory_model_text or "Phase 0" in memory_model_text
        assert "BKG" in memory_model_text or "Background Knowledge Graph" in memory_model_text

    def test_governance_rules_section_exists(self, memory_model_text: str) -> None:
        """Documentation must have governance rules section."""
        assert "## Governance Rules" in memory_model_text or "### Governance Rules" in memory_model_text

    def test_memory_type_summary_table_exists(self, memory_model_text: str) -> None:
        """Documentation must have memory type summary table."""
        # Look for markdown table with memory types
        assert "| Memory Type" in memory_model_text or "Memory Type" in memory_model_text
        assert "IDE Plane" in memory_model_text or "IDE plane" in memory_model_text
        assert "Tenant Plane" in memory_model_text or "Tenant plane" in memory_model_text
        assert "Product Plane" in memory_model_text or "Product plane" in memory_model_text
        assert "Shared Plane" in memory_model_text or "Shared plane" in memory_model_text

    def test_references_section_exists(self, memory_model_text: str) -> None:
        """Documentation must have references section."""
        assert "## References" in memory_model_text or "### References" in memory_model_text


class TestMemoryModelPlaneAssignments:
    """Test memory model plane assignments are correct."""

    def test_working_memory_all_planes(self, memory_model_text: str) -> None:
        """Working Memory must be assigned to all planes."""
        working_memory_section = memory_model_text.split("### 1. Working Memory")[1].split("### 2.")[0]
        assert "IDE Plane" in working_memory_section or "IDE plane" in working_memory_section
        assert "Tenant Plane" in working_memory_section or "Tenant plane" in working_memory_section
        assert "Product Plane" in working_memory_section or "Product plane" in working_memory_section
        assert "Shared Plane" in working_memory_section or "Shared plane" in working_memory_section

    def test_vector_db_memory_product_only(self, memory_model_text: str) -> None:
        """Vector DB Memory must be Product Plane only."""
        vector_section = memory_model_text.split("### 3. Vector DB Memory")[1].split("### 4.")[0]
        assert "Product Plane" in vector_section or "Product plane" in vector_section
        # Should not mention other planes for vector DB
        assert "IDE Plane" not in vector_section or "N/A" in vector_section
        assert "Tenant Plane" not in vector_section or "N/A" in vector_section
        assert "Shared Plane" not in vector_section or "N/A" in vector_section

    def test_semantic_qa_cache_product_only(self, memory_model_text: str) -> None:
        """Semantic Q&A Cache must be Product Plane only."""
        qa_cache_section = memory_model_text.split("### 6. Semantic Q&A Cache")[1].split("---")[0]
        assert "Product Plane" in qa_cache_section or "Product plane" in qa_cache_section
        # Should not mention other planes for Q&A cache
        assert "IDE Plane" not in qa_cache_section or "N/A" in qa_cache_section
        assert "Tenant Plane" not in qa_cache_section or "N/A" in qa_cache_section
        assert "Shared Plane" not in qa_cache_section or "N/A" in qa_cache_section

    def test_file_store_all_planes(self, memory_model_text: str) -> None:
        """File Store must be assigned to all planes."""
        file_store_section = memory_model_text.split("### 5. File Store")[1].split("### 6.")[0]
        assert "IDE Plane" in file_store_section or "ide/" in file_store_section
        assert "Tenant Plane" in file_store_section or "tenant/" in file_store_section
        assert "Product Plane" in file_store_section or "product/" in file_store_section
        assert "Shared Plane" in file_store_section or "shared/" in file_store_section


class TestMemoryModelGovernanceRules:
    """Test memory model governance rules are documented."""

    def test_governance_rules_listed(self, memory_model_text: str) -> None:
        """Governance rules section must list rules."""
        governance_section = memory_model_text.split("## Governance Rules")[-1] if "## Governance Rules" in memory_model_text else ""
        if not governance_section:
            governance_section = memory_model_text.split("### Governance Rules")[-1] if "### Governance Rules" in memory_model_text else ""

        assert len(governance_section) > 100, "Governance rules section too short"

    def test_plane_isolation_rule_documented(self, memory_model_text: str) -> None:
        """Plane isolation rule must be documented."""
        assert "Plane Isolation" in memory_model_text or "plane isolation" in memory_model_text.lower()

    def test_source_of_truth_rule_documented(self, memory_model_text: str) -> None:
        """Source of truth rule must be documented."""
        assert "Source of Truth" in memory_model_text or "source of truth" in memory_model_text.lower()
        assert "JSONL" in memory_model_text

    def test_no_secrets_pii_rule_documented(self, memory_model_text: str) -> None:
        """No secrets/PII rule must be documented."""
        assert "No Secrets" in memory_model_text or "no secrets" in memory_model_text.lower() or "secrets" in memory_model_text.lower()
        assert "PII" in memory_model_text or "pii" in memory_model_text.lower()

    def test_identical_schema_rule_documented(self, memory_model_text: str) -> None:
        """Identical schema contract rule must be documented."""
        assert "Identical Schema" in memory_model_text or "identical schema" in memory_model_text.lower()

    def test_semantic_qa_cache_governance_rule_documented(self, memory_model_text: str) -> None:
        """Semantic Q&A Cache governance rule must be documented."""
        qa_cache_section = memory_model_text.split("### 6. Semantic Q&A Cache")[1].split("---")[0]
        assert "NOT used for gating" in qa_cache_section or "not used for gating" in qa_cache_section.lower()

