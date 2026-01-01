# Module Reference Number Analysis Report

**Date:** 2025-01-27  
**Scope:** Entire project codebase  
**Total Matches Found:** 1,311 matches across 389 files

---

## Executive Summary

This report provides a systematic analysis of all old module reference numbers (M## format) found across the ZeroUI 2.0 project. References are categorized by type and priority for updating to the new PM-X/EPC-X/FM-X/CCP-X format as defined in `docs/architecture/ZeroUI Module Categories V 3.0.md`.

---

## Categories of References

### 1. **INTENTIONAL CODE IDENTIFIERS (DO NOT CHANGE)**

These are `__module_id__` fields in Python `__init__.py` files that serve as code identifiers per `MODULE_ID_NAMING_RATIONALE.md`:

**Files:**
- `src/cloud_services/shared-services/identity-access-management/__init__.py` - `__module_id__ = "M21"` (EPC-1)
- `src/cloud_services/shared-services/configuration-policy-management/__init__.py` - `__module_id__ = "M23"` (EPC-3)
- `src/cloud_services/shared-services/key-management-service/__init__.py` - `__module_id__ = "M33"` (EPC-11)
- `src/cloud_services/shared-services/contracts-schema-registry/__init__.py` - `__module_id__ = "M34"` (EPC-12)
- `src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/__init__.py` - `__module_id__ = "M35"` (EPC-13)

**Status:** ✅ **CORRECT** - These are intentional code identifiers and should remain unchanged per architectural decision.

---

### 2. **MODULE MANIFEST IDs (REVIEW NEEDED)**

These are module identifiers in VS Code extension manifest files:

**Files:**
- `src/vscode-extension/modules/m21-identity-access-management/index.ts` - `id: "M21"`
- `src/vscode-extension/modules/m23-configuration-policy-management/module.manifest.json` - `"module_id": "M23"`

**Status:** ⚠️ **REVIEW** - These may need updating to EPC-1 and EPC-3 respectively, but check if they're used by VS Code extension runtime.

---

### 3. **FOLDER-BASED MODULE IDENTIFIERS (DO NOT CHANGE)**

These are lowercase module IDs used in folder names and VS Code extension module IDs:

**Pattern:** `m01`, `m02`, `m03`, etc. (lowercase)

**Examples:**
- `src/vscode-extension/modules/m05-detection-engine-core/index.ts` - `id: 'm05'`
- Folder names: `m01-mmm-engine`, `m02-cross-cutting-concern-services`, etc.

**Status:** ✅ **CORRECT** - These are file system paths and VS Code extension module IDs. They should remain unchanged as they're tied to folder structure.

---

### 4. **COMMENTS AND DOCSTRINGS (NEEDS UPDATING)**

References in code comments, docstrings, and inline documentation that should reference new module IDs:

#### 4.1 Detection Engine Core (M05 → PM-4)
**Status:** ✅ **ALREADY UPDATED** in previous session
- `src/cloud_services/product_services/detection-engine-core/__init__.py`
- `src/cloud_services/product_services/detection-engine-core/services.py`
- `src/cloud_services/product_services/detection-engine-core/models.py`
- `src/cloud_services/product_services/detection-engine-core/routes.py`
- `src/vscode-extension/modules/m05-detection-engine-core/` (all TypeScript files)

#### 4.2 Integration Adapters (M10 → PM-5)
**Status:** ✅ **ALREADY UPDATED** in previous session
- `src/cloud_services/client-services/integration-adapters/__init__.py`

#### 4.3 Configuration & Policy Management (M23 → EPC-3)
**Status:** ✅ **ALREADY UPDATED** in previous session
- `src/vscode-extension/modules/m23-configuration-policy-management/index.ts`
- `src/vscode-extension/modules/m23-configuration-policy-management/commands.ts`
- `src/vscode-extension/ui/configuration-policy-management/ExtensionInterface.ts`

#### 4.4 Mock Dependencies (M27, M29, M31, M32, M33, M21)
**Status:** ✅ **ALREADY UPDATED** in previous session
- `src/cloud_services/shared-services/identity-access-management/dependencies.py` - M27→PM-7, M29→CCP-6, M32→CCP-1
- `src/cloud_services/shared-services/key-management-service/dependencies.py` - M27→PM-7, M29→CCP-6, M32→CCP-1, M21→EPC-1
- `src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/dependencies.py` - M27→PM-7, M29→CCP-6, M31→EPC-4, M33→EPC-11, M21→EPC-1

#### 4.5 Remaining Code References (NEEDS UPDATING)

**High Priority - Active Code Files:**

1. **M21 references** (222 matches in 58 files):
   - `src/cloud_services/shared-services/key-management-service/routes.py` - Comments referencing M21
   - `src/cloud_services/shared-services/key-management-service/middleware.py` - Comments referencing M21
   - `src/cloud_services/shared-services/key-management-service/services.py` - Comments referencing M21
   - `src/cloud_services/shared-services/data-governance-privacy/services.py` - Comments referencing M21
   - `src/cloud_services/shared-services/contracts-schema-registry/services.py` - Comments referencing M21
   - `src/cloud_services/shared-services/configuration-policy-management/services.py` - Comments referencing M21
   - `src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/services/receipt_service.py` - Comments referencing M21

2. **M23 references**:
   - Various service files referencing M23 in comments

3. **M33 references**:
   - Various service files referencing M33 in comments

4. **M34 references**:
   - Various service files referencing M34 in comments

5. **M27, M29, M31, M32 references**:
   - Already updated in dependencies.py files
   - May exist in other service files

---

### 5. **DOCUMENTATION FILES (MEDIUM PRIORITY)**

References in documentation that should be updated for consistency:

**Files Found:**
- `docs/architecture/modules/` - Multiple PRD files
- `docs/modules/` - Module README files
- `docs/root-notes/` - Various analysis reports
- `docs/testing/` - Test documentation
- `README.md` - Root README

**Status:** ⚠️ **REVIEW** - Documentation should reference new module IDs for consistency, but lower priority than code.

---

### 6. **ARCHIVE FILES (LOW PRIORITY)**

References in archive/validation report files:

**Files Found:**
- `src/cloud_services/*/archive/` - Various validation reports
- `src/cloud_services/client-services/integration-adapters/archive/` - Multiple archive files

**Status:** ⚠️ **OPTIONAL** - Archive files are historical and may not need updating.

---

### 7. **TEST FILES (MEDIUM PRIORITY)**

References in test files:

**Files Found:**
- `tests/test_*.py` - Various test files
- `tests/cloud_services/` - Test files referencing M-numbers
- `src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/tests/test_auth.py` - References M35

**Status:** ⚠️ **REVIEW** - Test files should be updated for consistency, especially if they reference module IDs in assertions or comments.

---

### 8. **CONFIGURATION FILES (REVIEW NEEDED)**

References in configuration files:

**Files Found:**
- `src/cloud_services/*/requirements.txt` - May contain M-number references
- `src/cloud_services/*/env.example` - Environment variable examples
- `src/cloud_services/*/database/schema.sql` - Database schemas
- `pyproject.toml` - Project configuration

**Status:** ⚠️ **REVIEW** - Configuration files may need updating if they reference module IDs.

---

## Detailed File-by-File Analysis

### Source Code Files Requiring Updates

#### High Priority (Active Implementation Code)

1. **Key Management Service:**
   - `src/cloud_services/shared-services/key-management-service/routes.py` - M21 references in comments
   - `src/cloud_services/shared-services/key-management-service/middleware.py` - M21 references
   - `src/cloud_services/shared-services/key-management-service/services.py` - M21, M33 references
   - `src/cloud_services/shared-services/key-management-service/README.md` - M21, M33 references

2. **Identity & Access Management:**
   - `src/cloud_services/shared-services/identity-access-management/README.md` - M21 references

3. **Data Governance & Privacy:**
   - `src/cloud_services/shared-services/data-governance-privacy/services.py` - M21 references
   - `src/cloud_services/shared-services/data-governance-privacy/dependencies.py` - M21 references
   - `src/cloud_services/shared-services/data-governance-privacy/README.md` - M21 references

4. **Contracts & Schema Registry:**
   - `src/cloud_services/shared-services/contracts-schema-registry/services.py` - M21, M34 references
   - `src/cloud_services/shared-services/contracts-schema-registry/routes.py` - M21, M34 references
   - `src/cloud_services/shared-services/contracts-schema-registry/env.example` - M21, M34 references
   - `src/cloud_services/shared-services/contracts-schema-registry/README.md` - M21, M34 references

5. **Configuration & Policy Management:**
   - `src/cloud_services/shared-services/configuration-policy-management/services.py` - M21, M23 references
   - `src/cloud_services/shared-services/configuration-policy-management/routes.py` - M21, M23 references
   - `src/cloud_services/shared-services/configuration-policy-management/README.md` - M21, M23 references

6. **Budgeting, Rate-Limiting & Cost Observability:**
   - `src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/services/receipt_service.py` - M21, M27, M33 references
   - `src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/services/quota_service.py` - M21 references
   - `src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/services/budget_service.py` - M21 references
   - `src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/routes.py` - M21 references
   - `src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/main.py` - M21 references
   - `src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/README.md` - M21 references
   - `src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/tests/test_auth.py` - M35 references

7. **Integration Adapters:**
   - `src/cloud_services/client-services/integration-adapters/services/polling_service.py` - M21 references
   - `src/cloud_services/client-services/integration-adapters/integrations/kms_client.py` - M21 references
   - `src/cloud_services/client-services/integration-adapters/integrations/iam_client.py` - M21 references
   - `src/cloud_services/client-services/integration-adapters/integrations/budget_client.py` - M21 references
   - `src/cloud_services/client-services/integration-adapters/README.md` - M21 references

8. **Signal Ingestion & Normalization:**
   - `src/cloud_services/product_services/signal-ingestion-normalization/dependencies.py` - M21 references

9. **Evidence & Receipt Indexing Service:**
   - `src/cloud_services/shared-services/evidence-receipt-indexing-service/dependencies.py` - M21 references

10. **Shared Libraries:**
    - `src/shared_libs/cccs/integration/edge_agent_bridge.py` - M21 references
    - `src/shared_libs/cccs/integration/cloud_services_integration.py` - M21 references

---

## Module Reference Mapping

### Old → New Mapping (from V 3.0)

| Old Reference | New Reference | Module Name | Status |
|--------------|---------------|-------------|--------|
| M01 | PM-1 | MMM Engine | ✅ Folder name correct |
| M02 | PM-2 | Cross-Cutting Concern Services | ✅ Folder name correct |
| M03 | FM-1 | Release Failures & Rollbacks | ✅ Folder name correct |
| M04 | PM-3 | Signal Ingestion & Normalization | ✅ Folder name correct |
| M05 | PM-4 | Detection Engine Core | ✅ Updated |
| M06 | FM-2 | Working Safely with Legacy Systems | ✅ Folder name correct |
| M07 | FM-3 | Technical Debt Accumulation | ✅ Folder name correct |
| M08 | FM-4 | Merge Conflicts & Delays | ✅ Folder name correct |
| M10 | PM-5 | Integration Adapters | ✅ Updated |
| M11 | FM-6 | Feature Development Blind Spots | ✅ Folder name correct |
| M13 | FM-8 | Monitoring & Observability Gaps | ✅ Folder name correct |
| M14 | FM-13 | Tenant Admin Portal | ✅ Folder name correct |
| M15 | FM-15 | Product Operations Portal | ✅ Folder name correct |
| M16 | FM-14 | ROI Dashboards | ✅ Folder name correct |
| M17 | EPC-10 | Gold Standards | ✅ Folder name correct |
| M18 | FM-9 | Knowledge Integrity & Discovery | ✅ Folder name correct |
| M20 | FM-10 | QA & Testing Deficiencies | ✅ Folder name correct |
| M21 | EPC-1 | Identity & Access Management | ⚠️ Code identifier (keep), update comments |
| M23 | EPC-3 | Configuration & Policy Management | ⚠️ Code identifier (keep), update comments |
| M27 | PM-7 | Evidence & Receipt Indexing Service (ERIS) | ✅ Updated in dependencies |
| M29 | CCP-6 | Data & Memory Plane | ✅ Updated in dependencies |
| M31 | EPC-4 | Alerting & Notification Service | ✅ Updated in dependencies |
| M32 | CCP-1 | Identity & Trust Plane | ✅ Updated in dependencies |
| M33 | EPC-11 | Key & Trust Management | ⚠️ Code identifier (keep), update comments |
| M34 | EPC-12 | Contracts & Schema Registry | ⚠️ Code identifier (keep), update comments |
| M35 | EPC-13 | Budgeting, Rate-Limiting & Cost Observability | ⚠️ Code identifier (keep), update comments |

---

## Recommendations

### Immediate Actions (High Priority)

1. **Update code comments/docstrings** in active service files:
   - Replace M21 → EPC-1 in comments (keep `__module_id__ = "M21"` in `__init__.py`)
   - Replace M23 → EPC-3 in comments (keep `__module_id__ = "M23"` in `__init__.py`)
   - Replace M33 → EPC-11 in comments (keep `__module_id__ = "M33"` in `__init__.py`)
   - Replace M34 → EPC-12 in comments (keep `__module_id__ = "M34"` in `__init__.py`)
   - Replace M35 → EPC-13 in comments (keep `__module_id__ = "M35"` in `__init__.py`)

2. **Review VS Code extension manifest files:**
   - `src/vscode-extension/modules/m21-identity-access-management/index.ts` - Consider updating `id: "M21"` to `id: "EPC-1"` if compatible
   - `src/vscode-extension/modules/m23-configuration-policy-management/module.manifest.json` - Consider updating `"module_id": "M23"` to `"module_id": "EPC-3"` if compatible

### Medium Priority

3. **Update test files** for consistency
4. **Update documentation files** for consistency
5. **Update README files** in module directories

### Low Priority

6. **Archive files** - Optional, historical reference
7. **Configuration files** - Review if module IDs are used in runtime

---

## Summary Statistics

- **Total Files with M-number References:** 389 files
- **Total Matches:** 1,311 matches
- **Code Identifier Files (Keep As-Is):** 5 files
- **Already Updated:** ~25 files (from previous session)
- **Requires Updates:** ~359 files (mostly documentation and comments)

---

## Notes

1. **Code Identifiers:** M21, M23, M33, M34, M35 in `__module_id__` fields are **intentional** and should **NOT** be changed per `MODULE_ID_NAMING_RATIONALE.md`.

2. **Folder Names:** Lowercase module folder names (`m01-mmm-engine`, etc.) are **file system paths** and should **NOT** be changed.

3. **VS Code Extension IDs:** Module IDs in VS Code extension code (`id: 'm05'`) are **runtime identifiers** tied to folder structure and should **NOT** be changed.

4. **Comments/Docstrings:** All references in comments, docstrings, and documentation should be updated to use new PM-X/EPC-X/FM-X/CCP-X format for consistency.

5. **Mock Class Names:** Mock class names (MockM27EvidenceLedger, etc.) are kept for backward compatibility, but docstrings have been updated to reference new module IDs.

---

**Report Generated:** 2025-01-27  
**Next Review:** After implementing recommended updates

