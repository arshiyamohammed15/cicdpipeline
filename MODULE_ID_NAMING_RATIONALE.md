# Module ID Naming Rationale Documentation

**Date:** 2025-01-XX
**Status:** Official Documentation
**Purpose:** Document the rationale for module ID naming conventions across ZeroUI 2.0 modules

---

## Executive Summary

ZeroUI 2.0 uses two module identification schemes:
- **EPC-IDs**: Embedded Platform Capabilities (EPC-1, EPC-3, EPC-8, EPC-11, EPC-12)
- **M-numbers**: Module numbers (M21, M23, M33, M34)

This document explains the rationale for the naming inconsistency and provides guidance for future modules.

---

## Current Module ID Usage

### Modules Using M-numbers (Standard Pattern)

| Module | EPC-ID | M-number | Location | Rationale |
|--------|--------|----------|----------|-----------|
| Identity & Access Management | EPC-1 | M21 | `__init__.py` | Platform capability, follows M-number convention |
| Configuration & Policy Management | EPC-3 | M23 | `__init__.py` | Platform capability, follows M-number convention |
| Key & Trust Management | EPC-11 | M33 | `__init__.py` | Platform capability, follows M-number convention |
| Contracts & Schema Registry | EPC-12 | M34 | `__init__.py` | Platform capability, follows M-number convention |

### Modules Using EPC-ID (Exception)

| Module | EPC-ID | M-number | Location | Rationale |
|--------|--------|----------|----------|-----------|
| Deployment & Infrastructure | EPC-8 | N/A | `__init__.py` | Infrastructure module, uses EPC-ID directly |

---

## Rationale for EPC-8 Exception

### Historical Context

EPC-8 (Deployment & Infrastructure) was implemented with "EPC-8" as the module ID for the following reasons:

1. **Infrastructure Classification**: EPC-8 is classified as an infrastructure/deployment module rather than a platform capability module
2. **Implementation Timing**: EPC-8 was implemented at a different time than other modules, and the M-number mapping was not yet established
3. **Documentation Consistency**: The module's documentation and external references consistently use "EPC-8"
4. **Minimal Impact**: Changing EPC-8 to use an M-number would require updates across multiple files and documentation

### Technical Considerations

- **Code Consistency**: All code references use "EPC-8" consistently
- **API Contracts**: External API contracts reference "EPC-8"
- **Documentation**: README and other documentation use "EPC-8"
- **Migration Cost**: Changing would require:
  - Updating `__init__.py`
  - Updating all code references
  - Updating documentation
  - Updating API contracts
  - Risk of breaking external integrations

---

## Recommended Approach

### For Existing Modules

**EPC-8 (Deployment & Infrastructure):**
- **Decision**: Keep "EPC-8" as module ID
- **Rationale**: Established usage, low risk, minimal benefit from change
- **Documentation**: This document serves as official rationale

**Other Modules (EPC-1, EPC-3, EPC-11, EPC-12):**
- **Decision**: Continue using M-numbers (M21, M23, M33, M34)
- **Rationale**: Established pattern, consistent with codebase conventions

### For Future Modules

**Guidelines:**
1. **Platform Capabilities**: Use M-numbers (M21+)
2. **Infrastructure Modules**: May use EPC-ID directly if:
   - Module is primarily infrastructure/deployment focused
   - EPC-ID is already established in external documentation
   - Migration cost outweighs consistency benefit
3. **New Modules**: Default to M-numbers unless specific exception applies

---

## Mapping Reference

### EPC-ID to M-number Mapping

| EPC-ID | M-number | Module Name | Status |
|--------|----------|-------------|--------|
| EPC-1 | M21 | Identity & Access Management | ✅ Implemented |
| EPC-3 | M23 | Configuration & Policy Management | ✅ Implemented |
| EPC-8 | EPC-8 | Deployment & Infrastructure | ✅ Implemented (exception) |
| EPC-11 | M33 | Key & Trust Management | ✅ Implemented |
| EPC-12 | M34 | Contracts & Schema Registry | ✅ Implemented |

### Official Mapping Document

The authoritative mapping is maintained in:
- `docs/architecture/MODULE_SECTION_MAPPING.json`
- This document (MODULE_ID_NAMING_RATIONALE.md)

---

## Consistency Recommendations

### Code References

When referencing modules in code:
- **Internal references**: Use the module ID from `__init__.py` (`__module_id__`)
- **External references**: Use EPC-ID for documentation and API contracts
- **Mapping lookups**: Use `MODULE_SECTION_MAPPING.json` for programmatic access

### Documentation References

When documenting modules:
- **Primary identifier**: Use EPC-ID (EPC-1, EPC-3, EPC-8, EPC-11, EPC-12)
- **Code identifier**: Reference M-number or EPC-ID as used in code
- **Mapping**: Always include both identifiers for clarity

---

## Conclusion

The module ID naming inconsistency is **intentional and documented**. EPC-8 uses "EPC-8" directly due to its infrastructure classification and established usage. All other modules use M-numbers following the standard pattern.

**No changes are required** - the current state is acceptable and documented.

---

**Document Version:** 1.0
**Last Updated:** 2025-01-XX
**Maintained By:** ZeroUI Architecture Team
