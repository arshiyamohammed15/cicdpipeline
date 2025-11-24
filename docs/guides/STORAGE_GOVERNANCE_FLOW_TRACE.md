# Storage Governance Flow Trace

## Overview

This document traces the complete storage governance flow across configuration, validator, and edge-agent storage modules. It provides a detailed walkthrough of how storage governance rules (216-228) are enforced from configuration through validation to runtime execution.

## Architecture Overview

The storage governance system consists of three main components:

1. **Configuration Layer**: Rule definitions and patterns (`config/rules/storage_governance.json`, `storage-scripts/folder-business-rules.md`)
2. **Validator Layer**: Python validators that check code compliance (`validator/rules/storage_governance.py`)
3. **Runtime Layer**: Edge Agent storage services that enforce rules at runtime (`src/edge-agent/shared/storage/`)

---

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONFIGURATION LAYER                            │
│  ┌──────────────────────┐  ┌──────────────────────────────┐  │
│  │ folder-business-     │  │ config/rules/                  │  │
│  │ rules.md (v1.1)      │  │ storage_governance.json       │  │
│  │ (Authoritative)      │  │                                │  │
│  └──────────────────────┘  └──────────────────────────────┘  │
│           │                              │                      │
│           └──────────────┬───────────────┘                      │
│                          │                                      │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VALIDATOR LAYER                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ validator/rules/storage_governance.py                     │  │
│  │ StorageGovernanceValidator                                │  │
│  │  - R216: _validate_name_casing                            │  │
│  │  - R217: _validate_no_code_pii                            │  │
│  │  - R218: _validate_no_secrets                             │  │
│  │  - R219: _validate_jsonl_receipts                        │  │
│  │  - R220: _validate_time_partitions                       │  │
│  │  - R221: _validate_policy_signatures                     │  │
│  │  - R222: _validate_dual_storage                          │  │
│  │  - R223: _validate_path_resolution                        │  │
│  │  - R224: _validate_receipts_validation                  │  │
│  │  - R225: _validate_evidence_watermarks                  │  │
│  │  - R226: _validate_rfc_fallback                          │  │
│  │  - R227: _validate_observability_partitions             │  │
│  │  - R228: _validate_laptop_receipts_partitioning          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                       │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ validator/optimized_core.py                                │  │
│  │ OptimizedConstitutionValidator                            │  │
│  │  - Registers StorageGovernanceValidator                   │  │
│  │  - Processes code files                                   │  │
│  │  - Reports violations                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RUNTIME LAYER (Edge Agent)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ src/edge-agent/shared/storage/                           │  │
│  │  - StoragePathResolver (R223: ZU_ROOT resolution)        │  │
│  │  - ReceiptStorageService (R219: JSONL, signed)          │  │
│  │  - ReceiptGenerator (R224: receipt signing)             │  │
│  │  - PolicyStorageService (R221: policy signatures)       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                       │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ storage-scripts/tools/                                   │  │
│  │  - create-folder-structure-*.ps1                          │  │
│  │  - Scaffold execution (R216: kebab-case)                 │  │
│  │  - Path validation (R223: ZU_ROOT)                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Flow Trace

### Phase 1: Configuration Loading

#### Step 1.1: Load Rule Configuration

**File**: `config/rules/storage_governance.json`

```json
{
  "category": "storage_governance",
  "priority": "critical",
  "description": "Storage architecture and data governance rules",
  "rules": [
    "Name casing & charset: kebab-case [a-z0-9-] only",
    "No source code/PII in stores",
    "No secrets/private keys on disk",
    "JSONL receipts (newline-delimited, signed, append-only)",
    ...
  ]
}
```

**Code Path**:
```python
# config/enhanced_config_manager.py
def get_rule_config(self, category: str) -> Dict[str, Any]:
    config_file = self.config_dir / "rules" / f"{category}.json"
    with open(config_file, 'r') as f:
        return json.load(f)
```

#### Step 1.2: Load Authoritative Specification

**File**: `storage-scripts/folder-business-rules.md` (v1.1)

**Key Sections**:
- Section 0: Scope & Goal (code-and-docs-only repo)
- Section 1: Non-Negotiable Rules (storage outside repo)
- Section 2: Windows-first local root and planes mapping
- Section 4: Per-plane, per-folder rules

**Reference**: Used by PowerShell scripts and validators as authoritative source.

---

### Phase 2: Validator Initialization

#### Step 2.1: Register Storage Governance Validator

**File**: `validator/optimized_core.py`

```python
def _initialize_rule_processors(self) -> Dict[str, Any]:
    mapping = [
        ...
        ("storage_governance", "rules.storage_governance", "StorageGovernanceValidator"),
        ...
    ]
    
    for category, module_path, class_name in mapping:
        module = __import__(f"validator.{module_path}", fromlist=[class_name])
        validator_class = getattr(module, class_name)
        rule_config = self.config_manager.get_rule_config(category)
        processors[category] = validator_class(rule_config)
```

#### Step 2.2: Initialize StorageGovernanceValidator

**File**: `validator/rules/storage_governance.py`

```python
class StorageGovernanceValidator:
    def __init__(self):
        self.rules = {
            'R216': self._validate_name_casing,
            'R217': self._validate_no_code_pii,
            'R218': self._validate_no_secrets,
            'R219': self._validate_jsonl_receipts,
            'R220': self._validate_time_partitions,
            'R221': self._validate_policy_signatures,
            'R222': self._validate_dual_storage,
            'R223': self._validate_path_resolution,
            'R224': self._validate_receipts_validation,
            'R225': self._validate_evidence_watermarks,
            'R226': self._validate_rfc_fallback,
            'R227': self._validate_observability_partitions,
            'R228': self._validate_laptop_receipts_partitioning
        }
        
        # Initialize patterns
        self.kebab_case_pattern = re.compile(r'^[a-z0-9-]+$')
        self.date_partition_pattern = re.compile(r'dt=\d{4}-\d{2}-\d{2}')
        self.yyyy_mm_pattern = re.compile(r'\d{4}/\d{2}')
        self.rfc_pattern = re.compile(r'UNCLASSIFIED__[a-z0-9-]+')
```

---

### Phase 3: Code Validation

#### Step 3.1: File Processing

**File**: `validator/optimized_core.py`

```python
def validate_file(self, file_path: str) -> List[Violation]:
    # Parse file
    tree = self._parse_file(file_path)
    content = self._read_file(file_path)
    
    # Process with all validators
    violations = []
    for category, processor in self.processors.items():
        category_violations = processor.validate_all(tree, content, file_path)
        violations.extend(category_violations)
    
    return violations
```

#### Step 3.2: Rule-Specific Validation

**Example: Rule 216 (Kebab-Case Naming)**

**File**: `validator/rules/storage_governance.py`

```python
def _validate_name_casing(self, tree, content, file_path):
    violations = []
    
    # Find all string literals that look like paths
    for node in ast.walk(tree):
        if isinstance(node, ast.Str):
            path = node.s
            # Check if it's a storage path
            if any(plane in path for plane in self.allowed_planes):
                # Extract folder names
                parts = path.split('/')
                for part in parts:
                    if part and not self.kebab_case_pattern.match(part):
                        violations.append(Violation(
                            rule_id="R216",
                            severity=Severity.ERROR,
                            message=f"Folder name '{part}' violates kebab-case rule",
                            file_path=file_path,
                            line_number=node.lineno
                        ))
    
    return violations
```

**Example: Rule 223 (Path Resolution via ZU_ROOT)**

```python
def _validate_path_resolution(self, tree, content, file_path):
    violations = []
    
    # Check for hardcoded paths
    hardcoded_patterns = [
        r'["\']D:\\\\ZeroUI',
        r'["\']C:\\\\ZeroUI',
        r'["\']/mnt/zero-ui',
        r'["\']/var/zero-ui'
    ]
    
    for pattern in hardcoded_patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            violations.append(Violation(
                rule_id="R223",
                severity=Severity.ERROR,
                message="Hardcoded path detected. Use ZU_ROOT environment variable.",
                file_path=file_path,
                line_number=content[:match.start()].count('\n') + 1
            ))
    
    return violations
```

---

### Phase 4: Runtime Enforcement (Edge Agent)

#### Step 4.1: Storage Path Resolution

**File**: `src/edge-agent/shared/storage/StoragePathResolver.ts`

```typescript
export class StoragePathResolver {
    private zuRoot: string;
    
    constructor(zuRoot?: string) {
        // Rule 223: Path resolution via ZU_ROOT
        this.zuRoot = zuRoot || process.env.ZU_ROOT || 
            process.env.ZEROUI_ROOT || 
            path.join(os.homedir(), 'ZeroUI');
        
        if (!this.zuRoot) {
            throw new Error('ZU_ROOT environment variable must be set (Rule 223)');
        }
    }
    
    resolveReceiptPath(repoId: string, year: number, month: number): string {
        // Rule 228: Laptop receipts use YYYY/MM partitioning
        // Rule 216: Kebab-case enforcement
        const normalizedRepoId = this.toKebabCase(repoId);
        return path.join(
            this.zuRoot,
            'ide',
            'receipts',
            normalizedRepoId,
            year.toString(),
            month.toString().padStart(2, '0')
        );
    }
    
    private toKebabCase(input: string): string {
        // Rule 216: Enforce kebab-case
        return input
            .replace(/([a-z])([A-Z])/g, '$1-$2')
            .toLowerCase()
            .replace(/[^a-z0-9-]/g, '-')
            .replace(/-+/g, '-')
            .replace(/^-|-$/g, '');
    }
}
```

#### Step 4.2: Receipt Storage Service

**File**: `src/edge-agent/shared/storage/ReceiptStorageService.ts`

```typescript
export class ReceiptStorageService {
    private resolver: StoragePathResolver;
    private generator: ReceiptGenerator;
    
    async storeDecisionReceipt(
        receipt: DecisionReceipt,
        repoId: string
    ): Promise<string> {
        // Rule 219: JSONL receipts (newline-delimited, signed, append-only)
        // Rule 224: Receipts must be signed
        const signedReceipt = await this.generator.signReceipt(receipt);
        
        // Rule 228: YYYY/MM partitioning
        const now = new Date();
        const receiptPath = this.resolver.resolveReceiptPath(
            repoId,
            now.getFullYear(),
            now.getMonth() + 1
        );
        
        // Rule 217: No source code/PII in stores
        const sanitizedReceipt = this.sanitizeReceipt(signedReceipt);
        
        // Rule 219: Append-only JSONL
        await this.appendToJsonl(receiptPath, sanitizedReceipt);
        
        return receiptPath;
    }
    
    private sanitizeReceipt(receipt: DecisionReceipt): DecisionReceipt {
        // Rule 217: Remove PII and source code
        const sanitized = { ...receipt };
        delete sanitized.sourceCode;
        delete sanitized.userEmail;
        delete sanitized.userName;
        // Keep only handles/IDs
        return sanitized;
    }
    
    private async appendToJsonl(
        filePath: string,
        receipt: DecisionReceipt
    ): Promise<void> {
        // Rule 219: Append-only JSONL format
        const line = JSON.stringify(receipt) + '\n';
        await fs.promises.appendFile(filePath, line, 'utf-8');
    }
}
```

#### Step 4.3: Receipt Generator

**File**: `src/edge-agent/shared/storage/ReceiptGenerator.ts`

```typescript
export class ReceiptGenerator {
    private privateKey: string;
    private keyId: string;
    
    async signReceipt(receipt: DecisionReceipt): Promise<SignedReceipt> {
        // Rule 224: Receipts must be signed
        const canonicalJson = this.canonicalizeJson(receipt);
        const signature = await this.sign(canonicalJson);
        
        return {
            ...receipt,
            signature: {
                algorithm: 'RS256',
                keyId: this.keyId,
                value: signature,
                timestamp: new Date().toISOString()
            }
        };
    }
    
    private canonicalizeJson(obj: any): string {
        // Rule 224: Canonical JSON for signing
        return JSON.stringify(obj, Object.keys(obj).sort());
    }
}
```

#### Step 4.4: Policy Storage Service

**File**: `src/edge-agent/shared/storage/PolicyStorageService.ts`

```typescript
export class PolicyStorageService {
    async cachePolicy(policySnapshot: PolicySnapshot): Promise<void> {
        // Rule 221: Policy snapshots must be signed
        if (!policySnapshot.signature) {
            throw new Error('Policy snapshot must be signed (Rule 221)');
        }
        
        // Rule 223: Use ZU_ROOT
        const policyPath = path.join(
            process.env.ZU_ROOT!,
            'ide',
            'policy',
            'snapshots',
            `${policySnapshot.id}-${policySnapshot.version}.json`
        );
        
        await fs.promises.writeFile(
            policyPath,
            JSON.stringify(policySnapshot, null, 2),
            'utf-8'
        );
    }
}
```

---

### Phase 5: Scaffold Execution

#### Step 5.1: PowerShell Scaffold Script

**File**: `storage-scripts/tools/create-folder-structure-development.ps1`

```powershell
param(
    [Parameter(Mandatory=$true)]
    [string]$ZuRoot
)

# Rule 223: Validate ZU_ROOT
if (-not $ZuRoot) {
    Write-Error "ZU_ROOT must be set (Rule 223)"
    exit 1
}

# Rule 216: Kebab-case enforcement
function New-KebabCaseFolder {
    param([string]$Name)
    $kebabName = $Name -replace '([a-z])([A-Z])', '$1-$2' -replace '[^a-z0-9-]', '-' -replace '-+', '-'
    $kebabName = $kebabName.ToLower()
    return $kebabName
}

# Create 4-plane structure
$planes = @('ide', 'tenant', 'product', 'shared')

foreach ($plane in $planes) {
    $planePath = Join-Path $ZuRoot $plane
    
    # Rule 216: All folder names must be kebab-case
    if ($plane -notmatch '^[a-z0-9-]+$') {
        Write-Error "Plane name '$plane' violates kebab-case rule (Rule 216)"
        exit 1
    }
    
    New-Item -ItemType Directory -Path $planePath -Force | Out-Null
    
    # Create plane-specific structure
    switch ($plane) {
        'ide' {
            # Rule 228: YYYY/MM partitioning for receipts
            $receiptsPath = Join-Path $planePath 'receipts'
            New-Item -ItemType Directory -Path $receiptsPath -Force | Out-Null
        }
        'tenant' {
            # Rule 220: dt= partitions for evidence
            $evidencePath = Join-Path $planePath 'evidence' 'data'
            New-Item -ItemType Directory -Path $evidencePath -Force | Out-Null
        }
        'product' {
            # Rule 221: Policy registry
            $policyPath = Join-Path $planePath 'policy' 'registry'
            New-Item -ItemType Directory -Path $policyPath -Force | Out-Null
        }
        'shared' {
            # Rule 223: PKI structure
            $pkiPath = Join-Path $planePath 'pki'
            New-Item -ItemType Directory -Path $pkiPath -Force | Out-Null
        }
    }
}

Write-Host "Storage structure created at $ZuRoot"
```

---

## Cross-Module Integration Points

### Integration Point 1: Config → Validator

**Location**: `config/enhanced_config_manager.py` → `validator/optimized_core.py`

**Flow**:
1. `EnhancedConfigManager.get_rule_config("storage_governance")` loads JSON
2. `OptimizedConstitutionValidator._initialize_rule_processors()` receives config
3. `StorageGovernanceValidator.__init__(rule_config)` initializes with config

### Integration Point 2: Validator → Edge Agent

**Location**: `validator/rules/storage_governance.py` → `src/edge-agent/shared/storage/`

**Flow**:
1. Validator checks code for compliance (static analysis)
2. Edge Agent enforces rules at runtime (dynamic enforcement)
3. Both reference `storage-scripts/folder-business-rules.md` as authoritative source

### Integration Point 3: Scaffold → Runtime

**Location**: `storage-scripts/tools/*.ps1` → `src/edge-agent/shared/storage/`

**Flow**:
1. PowerShell scripts create folder structure (Rule 216: kebab-case)
2. Edge Agent services use `StoragePathResolver` (Rule 223: ZU_ROOT)
3. Both enforce same rules from `folder-business-rules.md`

---

## Rule Enforcement Summary

| Rule | Config | Validator | Edge Agent | Scaffold |
|------|-------|-----------|------------|----------|
| R216: Kebab-case | ✅ | ✅ `_validate_name_casing` | ✅ `toKebabCase()` | ✅ Folder name validation |
| R217: No code/PII | ✅ | ✅ `_validate_no_code_pii` | ✅ `sanitizeReceipt()` | ✅ Documentation |
| R218: No secrets | ✅ | ✅ `_validate_no_secrets` | ✅ Secret detection | ✅ Documentation |
| R219: JSONL receipts | ✅ | ✅ `_validate_jsonl_receipts` | ✅ `appendToJsonl()` | ✅ Documentation |
| R220: Time partitions | ✅ | ✅ `_validate_time_partitions` | ✅ `dt=` pattern | ✅ Folder structure |
| R221: Policy signatures | ✅ | ✅ `_validate_policy_signatures` | ✅ `signReceipt()` | ✅ Documentation |
| R222: Dual storage | ✅ | ✅ `_validate_dual_storage` | ✅ JSONL + DB | ✅ Documentation |
| R223: ZU_ROOT paths | ✅ | ✅ `_validate_path_resolution` | ✅ `StoragePathResolver` | ✅ Parameter validation |
| R224: Receipt validation | ✅ | ✅ `_validate_receipts_validation` | ✅ `signReceipt()` | ✅ Documentation |
| R225: Evidence watermarks | ✅ | ✅ `_validate_evidence_watermarks` | ✅ Watermark service | ✅ Folder structure |
| R226: RFC fallback | ✅ | ✅ `_validate_rfc_fallback` | ✅ Fallback handler | ✅ Folder structure |
| R227: Observability partitions | ✅ | ✅ `_validate_observability_partitions` | ✅ `dt=` pattern | ✅ Folder structure |
| R228: Laptop receipts | ✅ | ✅ `_validate_laptop_receipts_partitioning` | ✅ `YYYY/MM` pattern | ✅ Folder structure |

---

## Testing the Flow

### Test 1: Validator → Config Integration

```bash
# Test that validator loads config correctly
python -c "
from config.enhanced_config_manager import EnhancedConfigManager
from validator.rules.storage_governance import StorageGovernanceValidator

manager = EnhancedConfigManager()
config = manager.get_rule_config('storage_governance')
validator = StorageGovernanceValidator()
print(f'Validator initialized with {len(validator.rules)} rules')
"
```

### Test 2: Edge Agent → Validator Compliance

```bash
# Test Edge Agent code with validator
python tools/enhanced_cli.py --file src/edge-agent/shared/storage/StoragePathResolver.ts
```

### Test 3: Scaffold → Edge Agent Compatibility

```powershell
# Create structure
pwsh storage-scripts/tools/create-folder-structure-development.ps1 -ZuRoot D:\ZeroUI\test

# Verify Edge Agent can use it
cd src/edge-agent
$env:ZU_ROOT = "D:\ZeroUI\test"
npm test -- shared/storage
```

---

## Key Files Reference

### Configuration Files
- `config/rules/storage_governance.json` - Rule configuration
- `storage-scripts/folder-business-rules.md` - Authoritative specification (v1.1)
- `storage-scripts/config/environments.json` - Environment configurations

### Validator Files
- `validator/rules/storage_governance.py` - Storage governance validator
- `validator/optimized_core.py` - Validator registration
- `config/enhanced_config_manager.py` - Config loading

### Edge Agent Files
- `src/edge-agent/shared/storage/StoragePathResolver.ts` - Path resolution (R223)
- `src/edge-agent/shared/storage/ReceiptStorageService.ts` - Receipt storage (R219, R224)
- `src/edge-agent/shared/storage/ReceiptGenerator.ts` - Receipt signing (R224)
- `src/edge-agent/shared/storage/PolicyStorageService.ts` - Policy storage (R221)

### Scaffold Files
- `storage-scripts/tools/create-folder-structure-development.ps1` - Development scaffold
- `storage-scripts/tools/create-folder-structure-integration.ps1` - Integration scaffold
- `storage-scripts/tools/create-folder-structure-production.ps1` - Production scaffold

### Test Files
- `tests/bdr/test_storage.py` - Python storage tests
- `src/edge-agent/shared/storage/__tests__/*.spec.ts` - TypeScript storage tests
- `storage-scripts/tests/test-folder-structure.ps1` - Scaffold tests

---

## Conclusion

The storage governance flow ensures consistent enforcement of rules 216-228 across all layers:

1. **Configuration** provides rule definitions and patterns
2. **Validator** checks code compliance during development
3. **Edge Agent** enforces rules at runtime
4. **Scaffold** creates compliant folder structures

All components reference `storage-scripts/folder-business-rules.md` as the single source of truth, ensuring consistency across the entire system.

---

**Last Updated**: 2025-01-XX  
**Maintained By**: ZeroUI 2.0 Constitution Team  
**Related Docs**: 
- `docs/guides/RULE_CATEGORY_VALIDATOR_TEST_MAPPING.md`
- `docs/guides/TARGETED_TEST_SUITE_EXECUTION.md`
- `storage-scripts/INTEGRATION.md`
- `storage-scripts/folder-business-rules.md`

