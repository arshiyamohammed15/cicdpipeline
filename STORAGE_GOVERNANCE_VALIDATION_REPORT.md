# Storage Governance Validation Report

**Date**: 2025-01-XX  
**Validator**: Triple Validation Against `storage-scripts/folder-business-rules.md`  
**Status**: VIOLATIONS FOUND

## Executive Summary

This report documents violations of the ZeroUI 2.0 Folder Business Rules (v2.0) found in the repository structure. All violations are verified against the authoritative rules document.

---

## CRITICAL VIOLATIONS

### 1. Prohibited Database Files in Repository Root

**Rule Violated**: Section 1, Rule 3 - "Prohibited under repo: `*.db`, `*.sqlite`, `*.sqlite3`"

**Violations Found**:
- `health_reliability_monitoring.db` (root directory)

**Required Action**: 
- Move this file to external storage: `D:\ZeroUI\edge.db` or appropriate location under `${ZU_ROOT}`
- Add to `.gitignore` if not already present
- Remove from repository tracking

**Status**: ❌ **CRITICAL VIOLATION**

---

### 2. Prohibited Log Files in Repository

**Rule Violated**: Section 1, Rule 3 - "Prohibited under repo: `*.log`"

**Violations Found**:
- `validation_service.log` (root directory)

**Note**: This file is already in `.gitignore` (line 51), but the file physically exists in the repository.

**Required Action**:
- Delete the file from repository
- Ensure all scripts write logs to `${ZEROU_LOG_ROOT}/constitution/` (external storage)

**Status**: ⚠️ **VIOLATION** (mitigated by .gitignore, but file should not exist)

---

### 3. Prohibited Archive Files in Repository

**Rule Violated**: Section 1, Rule 3 - "Prohibited under repo: `*.zip`"

**Violations Found**:
- `tools/k6/k6.zip`

**Note**: This file is already in `.gitignore` (line 60), but the file physically exists in the repository.

**Required Action**:
- Delete the file from repository
- If k6 tool is needed, it should be installed via package manager or downloaded to external location

**Status**: ⚠️ **VIOLATION** (mitigated by .gitignore, but file should not exist)

---

### 4. Storage Plane Folders in Repository

**Rule Violated**: Section 1, Rule 1 - "Storage lives outside the repo" and Section 0 - "Forbidden in repo: any storage/data artifacts"

**Violations Found**:
- `db/edge/` (empty folder)
- `db/ops/` (empty folder)
- `db/product/` (empty folder)
- `db/tenant/` (empty folder)

**Analysis**:
- The rules state: "Repo holds only: `/db/**` SQL (DDL/perf/checks/retention/signing glue)"
- These folders (`edge`, `ops`, `product`, `tenant`) appear to be storage plane folders, not SQL DDL files
- Storage plane folders should live under `${ZU_ROOT}`, not in the repository

**Required Action**:
- Verify if these folders are intended for SQL DDL files only
- If they are storage plane folders, remove them from repository
- If they are for SQL DDL, ensure they only contain `.sql` files (DDL/perf/checks/retention/signing glue)
- Currently all four folders are empty, which suggests they may be placeholders for storage planes

**Status**: ⚠️ **POTENTIAL VIOLATION** (requires clarification)

---

## COMPLIANT AREAS

### ✅ Allowed Database Structure

**Compliant**:
- `db/migrations/health_reliability_monitoring/001_initial.sql` - This is SQL DDL, which is allowed per rules

**Status**: ✅ **COMPLIANT**

---

### ✅ Folder Naming Convention

**Analysis**: 
- Most folders follow kebab-case `[a-z0-9-]+` convention
- Exceptions found are in `.cache/` directory which is already in `.gitignore`
- All repository-tracked folders appear to follow kebab-case

**Status**: ✅ **COMPLIANT**

---

### ✅ No Prohibited Folder Names

**Verified**:
- No folders named `evidence` found
- No folders named `Evidence` found  
- No folders named `zeroui_logs` found

**Status**: ✅ **COMPLIANT**

---

### ✅ .gitignore Configuration

**Analysis**:
- `.gitignore` properly excludes:
  - `*.log` files (line 49)
  - `*.zip` files (line 60)
  - `product/`, `tenant/`, `shared/` folders (lines 55-57)
  - `validation_service.log` specifically (line 51)

**Status**: ✅ **COMPLIANT**

---

## RECOMMENDATIONS

### Immediate Actions Required

1. **Remove `health_reliability_monitoring.db` from repository**
   ```powershell
   git rm health_reliability_monitoring.db
   # Ensure database is created in external storage: D:\ZeroUI\edge.db
   ```

2. **Delete `validation_service.log` if it exists**
   ```powershell
   Remove-Item validation_service.log -ErrorAction SilentlyContinue
   ```

3. **Delete `tools/k6/k6.zip` if it exists**
   ```powershell
   Remove-Item tools\k6\k6.zip -ErrorAction SilentlyContinue
   ```

4. **Clarify `db/` folder structure**
   - If `db/edge/`, `db/ops/`, `db/product/`, `db/tenant/` are for storage planes → Remove them
   - If they are for SQL DDL files → Ensure they only contain `.sql` files
   - Document the intended purpose in repository

### Long-term Actions

1. **Add pre-commit hook** to prevent committing prohibited file types
2. **Add CI validation** to check for storage governance violations
3. **Document storage plane setup** in README with clear instructions
4. **Review all scripts** to ensure they write to `${ZU_ROOT}` not repository paths

---

## VALIDATION METHODOLOGY

1. **File Type Scanning**: Searched for prohibited extensions (`.db`, `.sqlite`, `.sqlite3`, `.wal`, `.shm`, `.log`, `.zip`)
2. **Folder Name Scanning**: Searched for prohibited folder names (`evidence`, `Evidence`, `zeroui_logs`)
3. **Folder Structure Analysis**: Examined `db/` folder structure against rules
4. **Naming Convention Check**: Verified folder names follow kebab-case `[a-z0-9-]+`
5. **.gitignore Review**: Verified exclusion patterns match rules

---

## CONCLUSION

**Total Violations Found**: 4 (1 critical, 3 warnings)

**Compliance Status**: ⚠️ **NON-COMPLIANT** (requires immediate remediation)

The repository contains prohibited storage artifacts that must be removed. The most critical violation is the database file in the repository root. All violations can be remediated by:
1. Moving storage artifacts to external `${ZU_ROOT}` location
2. Removing prohibited files from repository
3. Clarifying and fixing `db/` folder structure

---

**Report Generated**: Automated validation against `storage-scripts/folder-business-rules.md` v2.0

