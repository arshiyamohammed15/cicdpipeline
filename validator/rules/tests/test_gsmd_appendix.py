"""
Tests for GSMD appendix rule metadata (documentation-only alignment).

Verifies that deprecated stub rules (229–231) exist in the constitution
metadata and point to the new rule numbers (226–228), without enforcing
runtime behavior.
"""

import json
from pathlib import Path
import unittest


class TestGSMDAppendixMetadata(unittest.TestCase):
    """Validate deprecated GSMD rule stubs and adjacent rules exist in DB JSON."""

    @classmethod
    def setUpClass(cls):
        cls.rules_path = Path("config") / "constitution_rules.json"
        with cls.rules_path.open("r", encoding="utf-8") as f:
            cls.rules_json = json.load(f)
        cls.rules = cls.rules_json.get("rules", {})

    def test_rule_229_deprecated_stub(self):
        self.assertIn("229", self.rules, "Rule 229 missing in constitution JSON")
        title = (self.rules["229"].get("title") or "").lower()
        self.assertIn("deprecated", title, "Rule 229 should be marked deprecated")
        # Soft check reference text
        content = (self.rules["229"].get("content") or "").lower()
        self.assertTrue("226" in content or "rfc fallback" in content,
                        "Rule 229 should reference Rule 226 RFC fallback")

    def test_rule_230_deprecated_stub(self):
        self.assertIn("230", self.rules, "Rule 230 missing in constitution JSON")
        title = (self.rules["230"].get("title") or "").lower()
        self.assertIn("deprecated", title, "Rule 230 should be marked deprecated")
        content = (self.rules["230"].get("content") or "").lower()
        self.assertTrue("227" in content or "observability" in content,
                        "Rule 230 should reference Rule 227 observability partitions")

    def test_rule_231_deprecated_stub(self):
        self.assertIn("231", self.rules, "Rule 231 missing in constitution JSON")
        title = (self.rules["231"].get("title") or "").lower()
        self.assertIn("deprecated", title, "Rule 231 should be marked deprecated")
        content = (self.rules["231"].get("content") or "").lower()
        self.assertTrue("228" in content or "laptop receipts" in content,
                        "Rule 231 should reference Rule 228 laptop receipts")


if __name__ == '__main__':
    unittest.main()


