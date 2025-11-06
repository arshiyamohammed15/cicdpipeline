# Recommendation: 45 Rules with Empty Descriptions in MASTER GENERIC RULES.json

**Date:** 2024-11-06  
**Issue:** 45 rules (15% of MASTER GENERIC RULES.json) have empty `description` fields  
**All 45 rules also have:** Empty `requirements` arrays

---

## Analysis of the 45 Rules

### Rule Categories

1. **Deprecated/Reserved Rules (3 rules):**
   - R-105: "(Reserved) See Rule 165: HTTP/Exit Mapping."
   - R-170: "(Deprecated) See Rule 226: RFC Fallback Pattern..."
   - R-171: "(Deprecated) See Rule 227: Observability/Adapters..."
   - R-172: "(Deprecated) See Rule 228: Laptop Receipts..."

2. **Rules with Self-Descriptive Titles (9 rules):**
   These titles are so detailed they essentially serve as descriptions:
   - R-084: "STOP CONDITIONS → ERROR CODES- Python/TS lint or format changes needed ……………… ERROR:STYLE_VIOLATION"
   - R-086: "SELF-AUDIT BEFORE OUTPUT- [ ] File header has What/Why/Reads-Writes/Contracts/Risks"
   - R-087: "STOP CONDITIONS → ERROR CODES- Missing file header or public API docstring ………. ERROR:COMMENT_MISSING"
   - R-089: "STOP CONDITIONS → ERROR CODES- Spectral lint failure …………………………… ERROR:OPENAPI_LINT_FAIL"
   - R-090: "RECEIPTS, LOGGING & EVIDENCE- For any privileged action, append an INTENT receipt..."
   - R-116: "RECEIPTS & GOVERNANCE- Emit JSONL receipts for: contract.publish, contract.diff, contract.violation."

3. **Structural/Organizational Rules (18 rules):**
   These appear to be structural definitions rather than behavioral rules:
   - Storage Scripts Enforcement (10 rules): R-218, R-219, R-220, R-222, R-223, R-225, R-226, R-227, R-228, R-229
   - Observability (3 rules): R-217, R-221
   - Docs (2 rules): R-082, R-224
   - AI & CODE GENERATION RULES (1 rule): R-157
   - Error Handling (1 rule): R-100

4. **Incomplete Rules (15 rules):**
   These have short titles but lack both descriptions and requirements:
   - R-007: "Make Things Fast"
   - R-020: "Process Data Locally First"
   - R-022: "Show Information Gradually"
   - R-024: "Be Smart About Data"
   - R-028: "Design for Quick Adoption"
   - R-029: "Test User Experience"
   - R-031: "Help People Work Better"
   - R-033: "Be Extra Careful with Private Data"
   - R-036: "Detection Engine - Be Accurate"
   - R-074: "Roles & Scope"
   - R-075: "Golden Rules (non-negotiable)"
   - R-076: "Review Outcomes & Severity"
   - R-077: "Stop Conditions → Error Codes (CI/Reviewer)"
   - R-078: "Review Procedure (simple checklist)"
   - R-079: "Evidence Required in PR"
   - R-080: "Automation (CI/Pre-commit)"
   - R-081: "Review Comment Style (simple English)"
   - R-085: "Optional PR Template (drop in .github/pull_request_template.md)"
   - R-127: "Consistent Naming"

---

## Recommendations

### Option 1: LEAVE AS-IS (Acceptable for Some Rules)

**For these rule types, empty descriptions may be acceptable:**
- **Deprecated rules (R-170, R-171, R-172):** These reference other rules and are marked deprecated
- **Reserved rules (R-105):** Placeholder rules that reference other rules
- **Self-descriptive titles (R-084, R-086, R-087, R-089, R-090, R-116):** Titles contain full descriptions

**Action:** Document that empty descriptions are acceptable for deprecated, reserved, or self-descriptive rules.

---

### Option 2: ADD DESCRIPTIONS (Recommended for Most Rules)

**For incomplete rules (15 rules), add descriptions:**

These rules need descriptions to be fully functional:
- R-007, R-020, R-022, R-024, R-028, R-029, R-031, R-033, R-036, R-074, R-075, R-076, R-077, R-078, R-079, R-080, R-081, R-085, R-127

**Action:** Add descriptive text explaining what each rule means and why it's important.

**Example approach:**
- Use the title as a starting point
- Explain the rule's purpose and context
- Add requirements array based on the description

---

### Option 3: MOVE TITLE TO DESCRIPTION (For Self-Descriptive Titles)

**For rules with extremely long titles (9 rules):**

**Action:** Move the detailed title text to the description field, create a shorter title.

**Example:**
- Current: R-084: "STOP CONDITIONS → ERROR CODES- Python/TS lint or format changes needed ……………… ERROR:STYLE_VIOLATION"
- Proposed Title: "STOP CONDITIONS → ERROR CODES: STYLE_VIOLATION"
- Proposed Description: "Python/TS lint or format changes needed. Error code: ERROR:STYLE_VIOLATION"

---

### Option 4: ADD REQUIREMENTS ARRAYS

**All 45 rules also lack requirements arrays.**

**Action:** Add requirements arrays to all rules, even if description remains empty.

**For structural rules:** Requirements could list the structural elements they define.
**For behavioral rules:** Requirements should list the specific behaviors or constraints.

---

## Recommended Action Plan

### Immediate (High Priority)

1. **Add descriptions to 15 incomplete rules:**
   - R-007, R-020, R-022, R-024, R-028, R-029, R-031, R-033, R-036
   - R-074, R-075, R-076, R-077, R-078, R-079, R-080, R-081, R-085, R-127

2. **Add requirements arrays to all 45 rules**

### Medium Priority

3. **Refactor self-descriptive titles (9 rules):**
   - Move detailed text from title to description
   - Create concise titles

### Low Priority (Optional)

4. **Document exceptions for deprecated/reserved rules:**
   - R-105, R-170, R-171, R-172 may remain without descriptions if they're just references

---

## Implementation Notes

### For Structural Rules (Storage Scripts Enforcement, Observability)

These rules define system structure rather than behavior. Consider:
- **Description:** Explain what structure/pattern is being defined
- **Requirements:** List the specific structural elements or constraints

### For Behavioral Rules (Performance, System Design, Teamwork)

These rules define how work should be done. Consider:
- **Description:** Explain the principle and why it matters
- **Requirements:** List specific behaviors or practices required

---

## Impact Assessment

### Current State
- ✅ Rules are functional (have titles, categories, validation)
- ⚠️ Rules lack documentation (descriptions)
- ⚠️ Rules lack explicit requirements (requirements arrays)

### After Implementation
- ✅ All rules fully documented
- ✅ All rules have explicit requirements
- ✅ Better consistency across all rules
- ✅ Improved rule understanding for developers/AI systems

---

## Conclusion

**Recommended Action:** Add descriptions and requirements to all 45 rules, with the following exceptions:
- Deprecated rules (R-170, R-171, R-172) may reference other rules in description
- Reserved rules (R-105) may reference other rules in description
- Self-descriptive titles can be moved to descriptions with shorter titles

**Priority:** High - Completing these rules improves documentation quality and system consistency.

---

**END OF RECOMMENDATION**

