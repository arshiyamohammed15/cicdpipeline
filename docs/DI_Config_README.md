<!--
PATCH HEADER

Discovered anchors:
  - config/InfraConfig.ts: loadInfraConfig() function, precedence logic, vendor-neutrality validation
  - storage-scripts/config/environments.json: environments structure, top-level infra defaults
  - config/infra.config.schema.json: schema reference
  - scripts/di_config_verify.ps1: verification script

Files created/edited:
  - docs/DI_Config_README.md (created)
  - scripts/di_config_verify.ps1 (created)
  - src/platform/config/infra_config_runner.ts (created)
  - tsconfig.config.json (created)

STOP/MISSING triggers:
  - None encountered
  - No new dependencies added
  - No placeholder interpolation (documented as no-interpolation rule)
  - No vendor strings in neutral infra (documented as vendor-neutrality scope)
  - No environments.json keys renamed/removed
  - No log truncation behavior introduced
-->

# DI Config (Infrastructure Configuration)

## Overview

The DI (Dependency Injection) Config system provides a vendor-neutral infrastructure configuration mechanism for ZeroUI 2.0. It supports environment-specific overrides while maintaining strict precedence rules and vendor-neutrality validation.

## Key Concepts

### Neutral Infra

The infrastructure configuration is **vendor-neutral**, meaning it does not contain vendor-specific strings (e.g., `aws`, `s3`, `azure`, `gcs`, `kms`, `arn`). This allows the system to work with any cloud provider or local adapters without vendor lock-in.

The neutral infra configuration includes:
- **Compute**: Baseline capacity and spot instance settings
- **Routing**: Default routing strategy and cost profiles
- **Storage**: Object and backup storage roots
- **Network**: TLS requirements
- **Observability**: Metrics and cost tracking flags
- **DR**: Disaster recovery settings
- **Feature Flags**: Infrastructure and adapter enablement flags

### Precedence

Configuration loading follows strict precedence order:

1. **Defaults** (top-level `infra` in `environments.json`)
2. **Per-Environment Override** (`environments.<env-name>.infra`)
3. **Policy Overlay** (optional, if `policyOverlayPath` is provided)

Each layer merges with the previous layer, with later layers taking precedence for overlapping fields.

### Feature Flags

The configuration includes feature flags that control infrastructure functionality:

- `infra_enabled`: Master switch for infrastructure features
- `local_adapters_enabled`: Enables local adapter implementations

Both flags must be `true` for infrastructure features to be active.

### No Interpolation Rule

The configuration loader **does not perform placeholder interpolation**. Placeholder strings like `{zu_root_pattern}` are preserved as-is in the configuration. This ensures deterministic behavior and prevents unexpected transformations.

### Vendor-Neutrality Scope

Vendor-neutrality validation applies **only to neutral infra fields**. Vendor-specific configuration blocks (if present) are not validated for neutrality, allowing integration with vendor-specific services when needed.

## Configuration Files

### `storage-scripts/config/environments.json`

Main configuration file containing:
- Top-level `infra` block (defaults)
- `environments` object with per-environment overrides

### `config/infra.config.schema.json`

JSON schema reference (for documentation only). The loader uses internal type-guards, not JSON Schema validation.

## Usage

### Loading Configuration

```typescript
import { loadInfraConfig } from './config/InfraConfig';

const result = loadInfraConfig('development');
if (result.isEnabled) {
  // Infrastructure features are enabled
  const config = result.config;
  // Use config...
}
```

### Verification Script

The PowerShell script `scripts/di_config_verify.ps1` validates all environments:

```powershell
# Build the TypeScript runner first (if needed)
tsc

# Run verification
.\scripts\di_config_verify.ps1
```

The script:
1. Enumerates all environments from `environments.json`
2. Runs the compiled Node.js runner (`dist/platform/config/infra_config_runner.js`) for each environment
3. Prints a PASS/FAIL line for each environment with reason
4. Displays a final PASS matrix
5. Exits with code 0 only if all environments PASS; otherwise exits non-zero

### Example Output

```
=== DI Config Verification ===
Environments to verify: 3

  development ... PASS
  staging ... PASS
  production ... FAIL
    Reason: Environment "production" not found in environments.json

=== PASS Matrix ===

  Environment  Status  Reason
  --------------------------------------------------
  development  PASS    Configuration loaded successfully
  staging      PASS    Configuration loaded successfully
  production   FAIL    Environment "production" not found in environments.json

Summary: 2/3 PASSED, 1/3 FAILED

FAIL: One or more environments failed validation
```

## Implementation Details

### Type Safety

The configuration uses TypeScript interfaces with internal type-guards. No external JSON Schema engine is used, ensuring:
- No additional dependencies
- Fast validation
- Type-safe configuration access

### Frozen Configuration

The returned configuration object is **frozen** (using `Object.freeze`), preventing accidental mutations and ensuring deterministic behavior.

### Error Handling

The loader throws descriptive errors for:
- Missing configuration files
- Invalid JSON syntax
- Missing required fields
- Invalid field types
- Vendor-specific strings in neutral fields
- Missing environments

## Best Practices

1. **Always use the verification script** before deploying configuration changes
2. **Keep vendor-specific config separate** from neutral infra blocks
3. **Test all environments** when modifying defaults
4. **Document environment-specific overrides** in environment descriptions
5. **Use feature flags** to gradually enable infrastructure features

## Related Files

- `config/InfraConfig.ts`: Configuration loader implementation
- `src/platform/config/infra_config_runner.ts`: Node.js runner for validation
- `scripts/di_config_verify.ps1`: PowerShell verification script
- `storage-scripts/config/environments.json`: Configuration source
- `config/infra.config.schema.json`: Schema reference

