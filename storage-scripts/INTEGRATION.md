# Storage Scripts Integration with ZeroUI Constitution

## Overview

The storage-scripts folder contains the **4-Plane Storage Architecture** implementation for ZeroUI. This document describes how storage governance rules have been integrated into the ZeroUI Constitution validator system.

## Architecture

### 4-Plane Storage Structure

The ZeroUI storage architecture consists of four planes:

1. **IDE Plane** (`{ZU_ROOT}/ide/`): Developer laptop storage
   - Agent receipts with YYYY/MM partitioning
   - Policy cache, trust keys, config
   - LLM prompts, tools, adapters, caches
   - Queue management

2. **Tenant Plane** (`{ZU_ROOT}/tenant/`): Per-tenant storage
   - Evidence (receipts, manifests, checksums, DLQ, watermarks)
   - Observability (metrics, traces, logs) with dt= partitions
   - Adapters and gateway logs
   - Reporting marts

3. **Product Plane** (`{ZU_ROOT}/product/`): Cross-tenant product storage
   - Policy registry (releases, templates, revocations)
   - Service metrics
   - Trust and public keys
   - Reporting aggregates

4. **Shared Plane** (`{ZU_ROOT}/shared/`): Shared infrastructure
   - PKI (trust anchors, intermediates, CRL)
   - Observability (OTel metrics, traces, logs)
   - SIEM (detections, events)
   - BI lake, governance controls

## Scaffold Execution

### Running the Scaffold

The PowerShell scaffold script creates the complete folder structure:

```powershell
# Dry run (preview)
powershell -File storage-scripts\tools\scaffold\zero_ui_scaffold.ps1 `
  -ZuRoot D:\ZeroUI `
  -Tenant default-tenant `
  -Env dev `
  -Repo ZeroUI2.0 `
  -CreateDt 2025-10-20 `
  -Consumer metrics `
  -DryRun

# Actual execution
powershell -File storage-scripts\tools\scaffold\zero_ui_scaffold.ps1 `
  -ZuRoot D:\ZeroUI `
  -Tenant default-tenant `
  -Env dev `
  -Repo ZeroUI2.0 `
  -CreateDt 2025-10-20 `
  -Consumer metrics
```

### Script Features

- **Idempotent**: Safe to re-run multiple times
- **Folders Only**: No files created
- **Date Partitioning**: Creates dt=YYYY-MM-DD partitions when -CreateDt provided
- **Month Partitioning**: Creates YYYY/MM for laptop receipts
- **Consumer Watermarks**: Creates per-consumer evidence tracking
- **RFC Fallback**: Supports UNCLASSIFIED__slug pattern
- **Compatible**: Optional deprecated alias support via -CompatAliases

## Constitution Integration

### New Rules (216-228)

The storage governance rules have been added to the ZeroUI Constitution:

| Rule | Name | Description |
|------|------|-------------|
| 216 | Name Casing & Charset | Kebab-case [a-z0-9-] only |
| 217 | No Code/PII in Stores | Use handles/IDs only |
| 218 | No Secrets on Disk | Use secrets manager/HSM/KMS |
| 219 | JSONL Receipts | Signed, append-only, newline-delimited |
| 220 | Time Partitions | UTC dt=YYYY-MM-DD format |
| 221 | Policy Signatures | All policies must be signed |
| 222 | Dual Storage | JSONL authority, DB mirrors |
| 223 | Path Resolution | Use ZU_ROOT environment variable |
| 224 | Receipts Validation | Verify signatures, enforce append-only |
| 225 | Evidence Watermarks | Per-consumer structure |
| 226 | RFC Fallback | UNCLASSIFIED__slug with 24h resolution |
| 227 | Observability Partitions | dt= partitions required |
| 228 | Laptop Receipts | YYYY/MM month partitioning |

### Validator Integration

The **StorageGovernanceValidator** has been integrated into the core validator:

```python
# validator/rules/storage_governance.py
class StorageGovernanceValidator:
    """Validates storage governance and 4-plane architecture compliance."""
    
    def validate(self, file_path: str, content: str) -> List[Violation]:
        """Validate storage governance compliance for a file."""
        # Checks all 13 rules (216-228)
```

### Configuration Files

#### Rule Configuration
**File**: `config/rules/storage_governance.json`

```json
{
  "category": "storage_governance",
  "priority": "critical",
  "description": "Storage architecture and data governance rules",
  "rules": [216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228]
}
```

#### Validation Patterns
**File**: `config/patterns/storage_governance_patterns.json`

Contains regex patterns for:
- Kebab-case validation
- Date partition formats
- RFC fallback patterns
- Secret detection
- PII detection
- JSONL format validation
- Path structure requirements

## Validation Examples

### Rule 216: Kebab-Case Naming

```python
# ❌ Violation
path = "storage/MyFolder/UserData"

# ✅ Good
path = "storage/my-folder/user-data"
```

### Rule 218: No Secrets

```python
# ❌ Violation
api_key = "sk-1234567890abcdef"
password = "SecretPass123"

# ✅ Good
api_key = os.environ.get("API_KEY")
password = os.environ.get("DB_PASSWORD")
```

### Rule 220: Time Partitions

```python
# ❌ Violation
path = "observability/metrics/date=20251020"

# ✅ Good
path = "observability/metrics/dt=2025-10-20"
```

### Rule 223: Path Resolution

```python
# ❌ Violation
storage_path = "D:\\ZeroUI\\tenant\\evidence"

# ✅ Good
zu_root = os.environ.get("ZU_ROOT")
storage_path = os.path.join(zu_root, "tenant", "evidence")
```

### Rule 228: Laptop Receipts

```python
# ❌ Violation
receipt_path = "ide/agent/receipts/repo/"

# ✅ Good
receipt_path = "ide/agent/receipts/repo/2025/10/"
```

## Usage

### Running Validation

```bash
# Validate a file with storage governance rules
python enhanced_cli.py --file myfile.py

# Check storage governance rule statistics
python enhanced_cli.py --rule-stats --category storage_governance

# List all storage governance rules
python enhanced_cli.py --rules-by-category storage_governance
```

### Enable/Disable Rules

```bash
# Enable a specific storage rule
python enhanced_cli.py --enable-rule 216

# Disable a rule temporarily
python enhanced_cli.py --disable-rule 220 --disable-reason "Testing alternate partition format"
```

### Rebuild Constitution Database

After adding or modifying rules:

```bash
# Rebuild from markdown (single source of truth)
python enhanced_cli.py --rebuild-from-markdown

# Verify consistency across all sources
python enhanced_cli.py --verify-consistency
```

## Key Principles

1. **No Hallucination**: Rules are extracted exactly from `folder-business-rules.md`
2. **No Assumptions**: Specifications followed precisely
3. **No Breaking Changes**: Backward compatible with existing 215 rules
4. **Gold Standard Quality**: Enterprise-grade validation
5. **Privacy by Default**: No code/PII in stores
6. **Security First**: No secrets on disk
7. **JSONL Authority**: Files are source of truth, DB mirrors for queries
8. **Portable Paths**: All paths via ZU_ROOT

## Storage Governance Workflow

1. **Development**:
   - Set `ZU_ROOT` environment variable
   - Use scaffold to create structure
   - Follow naming conventions (kebab-case)
   - Never hardcode paths

2. **Data Storage**:
   - Write receipts as JSONL (append-only)
   - Sign all receipts and policies
   - Use dt= partitions for time-series data
   - Use YYYY/MM for laptop receipts

3. **Evidence Management**:
   - Store only handles/IDs, no code/PII
   - Create per-consumer watermarks
   - Use RFC fallback for unclassified data
   - Resolve unclassified within 24h

4. **Validation**:
   - Run validator on code changes
   - Fix violations before commit
   - Update patterns if needed
   - Document exceptions with RFC

## Files Created/Modified

### New Files
- `validator/rules/storage_governance.py` - Validator implementation
- `config/rules/storage_governance.json` - Rule configuration
- `config/patterns/storage_governance_patterns.json` - Validation patterns
- `storage-scripts/INTEGRATION.md` - This file

### Modified Files
- `ZeroUI2.0_Master_Constitution.md` - Added rules 216-228
- `validator/core.py` - Integrated storage governance validator
- `README.md` - Updated with storage governance section

## Testing

Tests are located in `validator/rules/tests/test_storage_governance.py` covering:
- Each rule (216-228) individually
- Positive cases (compliant code)
- Negative cases (violations)
- Edge cases and boundary conditions
- Integration with core validator

## Documentation References

- **Specification**: `storage-scripts/folder-business-rules.md` (v1.1)
- **Scaffold README**: `storage-scripts/README_scaffold.md`
- **Quick Start**: `storage-scripts/scaffold.md`
- **Constitution**: `ZeroUI2.0_Master_Constitution.md` (Rules 216-228)
- **Main README**: `README.md` (Storage Governance section)

## Success Criteria

✅ Scaffold creates all 4 planes correctly  
✅ Rules 216-228 extracted and documented  
✅ StorageGovernanceValidator implements all 13 rules  
✅ Integration with core validator complete  
✅ All tests pass (100% coverage for new rules)  
✅ Documentation complete and accurate  
✅ No breaking changes to existing system  
✅ Consistency verification passes  

## Support

For issues or questions:
1. Review this integration guide
2. Check `folder-business-rules.md` for specifications
3. Run `python enhanced_cli.py --rule-stats` for rule status
4. Use `--verbose` flag for detailed validation output
5. Check logs in `config/logs/` for troubleshooting

---

**Last Updated**: 2025-10-20  
**Version**: 1.0  
**Status**: Production Ready

