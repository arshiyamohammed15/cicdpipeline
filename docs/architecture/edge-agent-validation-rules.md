# Edge Agent Validation Rules Catalog

## Overview

This document defines the validation rules catalog for the Edge Agent's `ValidationCoordinator`. The Edge Agent performs **validation-only** operations - it validates `DelegationResult` objects returned from task processing but does not contain business logic.

## Validation Architecture

### Validation Flow

1. Task is processed by a delegation module
2. Module returns `DelegationResult` with metadata
3. `ValidationCoordinator` runs all registered validation rules
4. Each rule evaluates specific aspects of the result
5. Overall validation passes only if all rules pass
6. Validation metrics are tracked for monitoring

### Validation Rule Structure

Each validation rule implements the `ValidationRule` interface:

```typescript
interface ValidationRule {
    name: string;
    description: string;
    validate: (result: DelegationResult) => Promise<boolean>;
    severity: 'low' | 'medium' | 'high' | 'critical';
    category: 'security' | 'performance' | 'compliance' | 'data-integrity';
}
```

## Rule Catalog

### Rule: `security`

**Category**: `security`
**Severity**: `critical`
**Description**: Validates that the delegation result has passed security validation checks.

**Validation Logic**:
```typescript
result.metadata.securityValidated === true
```

**Pass Criteria**:
- `securityValidated` field in result metadata must be `true`

**Fail Criteria**:
- `securityValidated` is `false` or `undefined`

**Impact**:
- Critical failure blocks task completion
- Security validation is mandatory for all delegation results

**Metrics Mapping**:
- **Pass**: Contributes to overall validation pass (all rules must pass)
- **Fail**: Causes overall validation to fail (`isValid: false`)
- **Severity**: `critical` (defined in rule structure, may be used for future metric aggregation)

---

### Rule: `integrity`

**Category**: `data-integrity`
**Severity**: `high`
**Description**: Validates that data integrity checks have passed for the delegation result.

**Validation Logic**:
```typescript
result.metadata.dataIntegrity === true
```

**Pass Criteria**:
- `dataIntegrity` field in result metadata must be `true`

**Fail Criteria**:
- `dataIntegrity` is `false` or `undefined`

**Impact**:
- High severity failure indicates potential data corruption or tampering
- Data integrity validation is mandatory for all delegation results

**Metrics Mapping**:
- **Pass**: Contributes to overall validation pass (all rules must pass)
- **Fail**: Causes overall validation to fail (`isValid: false`)
- **Severity**: `high` (defined in rule structure, may be used for future metric aggregation)

---

### Rule: `performance`

**Category**: `performance`
**Severity**: `medium`
**Description**: Validates that task processing completed within acceptable performance thresholds.

**Validation Logic**:
```typescript
result.metadata.performanceMetrics &&
result.metadata.performanceMetrics.latency < 1000
```

**Pass Criteria**:
- `performanceMetrics` object exists in result metadata
- `latency` value is less than 1000 milliseconds (1 second)

**Fail Criteria**:
- `performanceMetrics` is missing or `undefined`
- `latency` is greater than or equal to 1000 milliseconds

**Impact**:
- Medium severity failure indicates performance degradation
- Causes overall validation to fail (all rules must pass)
- Signals optimization needed for future tasks

**Metrics Mapping**:
- **Pass**: Contributes to overall validation pass (all rules must pass)
- **Fail**: Causes overall validation to fail (`isValid: false`)
- **Severity**: `medium` (defined in rule structure, may be used for future metric aggregation)

---

### Rule: `compliance`

**Category**: `compliance`
**Severity**: `high`
**Description**: Validates that the delegation result meets compliance requirements by ensuring both security and data integrity validations have passed.

**Validation Logic**:
```typescript
result.metadata.securityValidated === true &&
result.metadata.dataIntegrity === true
```

**Pass Criteria**:
- Both `securityValidated` and `dataIntegrity` must be `true`

**Fail Criteria**:
- Either `securityValidated` or `dataIntegrity` is `false` or `undefined`

**Impact**:
- High severity failure indicates compliance violation
- Compliance validation is mandatory for all delegation results

**Metrics Mapping**:
- **Pass**: Contributes to overall validation pass (all rules must pass)
- **Fail**: Causes overall validation to fail (`isValid: false`)
- **Severity**: `high` (defined in rule structure, may be used for future metric aggregation)

---

## Validation Metrics Mapping

### Overall Validation Result

The `ValidationCoordinator.validate()` method returns a boolean:
- **`true`**: All validation rules passed
- **`false`**: One or more validation rules failed

### Validation Metrics Structure

The `getValidationStats()` method returns:

```typescript
{
    total: number;                    // Total number of validations performed
    passed: number;                    // Number of validations that passed
    failed: number;                    // Number of validations that failed
    successRate: number;               // Percentage of successful validations (0-100)
}
```

> **Note**: The `ValidationMetrics` interface defines additional fields (`averageScore`, `criticalFailures`, category-specific failures), but the current implementation only tracks basic pass/fail statistics. Future enhancements may add these metrics.

### Metrics Calculation Rules

1. **Total**: Count of all validation runs (length of `validationHistory`)
2. **Passed**: Count of validation runs where `isValid === true`
3. **Failed**: Count of validation runs where `isValid === false` (calculated as `total - passed`)
4. **Success Rate**: Percentage calculated as `(passed / total) * 100` when `total > 0`, otherwise `0`

### Severity and Category Tracking

While the current implementation tracks overall pass/fail, individual rule results in `validationHistory` contain:
- Rule name
- Pass/fail status
- Error messages (if any)

The `ValidationRule` interface defines `severity` and `category` fields, which can be used for future metric aggregation:
- **Severity levels**: `low`, `medium`, `high`, `critical`
- **Categories**: `security`, `performance`, `compliance`, `data-integrity`

### Severity Impact on Overall Validation

The current implementation requires **all rules to pass** for overall validation to succeed. Any rule failure causes `validate()` to return `false`.

Severity levels are defined in the `ValidationRule` interface but do not affect the pass/fail logic:
- **Critical** (`security`): Failure causes overall validation to fail
- **High** (`integrity`, `compliance`): Failure causes overall validation to fail
- **Medium** (`performance`): Failure causes overall validation to fail

> **Note**: All rules are evaluated regardless of severity. Severity may be used for future metric aggregation or alerting, but currently all failures are treated equally in terms of overall validation result.

## Rule Registration

### Default Rules

The following rules are automatically registered during `ValidationCoordinator.initialize()`:

1. `security` (critical, security)
2. `integrity` (high, data-integrity)
3. `performance` (medium, performance)
4. `compliance` (high, compliance)

### Dynamic Rule Management

Rules can be added or removed at runtime:

```typescript
// Add a custom validation rule
validationCoordinator.addValidationRule('custom-rule', {
    name: 'custom-rule',
    description: 'Custom validation rule',
    validate: async (result: DelegationResult) => {
        // Custom validation logic
        return true;
    },
    severity: 'medium',
    category: 'performance'
});

// Remove a validation rule
validationCoordinator.removeValidationRule('custom-rule');
```

## Validation Result Structure

### Validation History Entry

Each validation run creates a history entry:

```typescript
{
    result: DelegationResult,           // The result that was validated
    timestamp: string,                  // ISO 8601 timestamp
    validations: Array<{
        rule: string,                    // Rule name
        passed: boolean,                // Whether rule passed
        message: string                 // Pass/Fail message or error
    }>,
    isValid: boolean                     // Overall validation result
}
```

### Rule Result Structure

Individual rule results follow the `RuleResult` interface:

```typescript
interface RuleResult {
    ruleName: string;
    passed: boolean;
    message: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    category: 'security' | 'performance' | 'compliance' | 'data-integrity';
}
```

## Implementation Notes

### Validation-Only Architecture

The Edge Agent's validation system is **validation-only**:
- Does not modify `DelegationResult` objects
- Does not contain business logic
- Only evaluates and reports on result quality
- All validation is based on metadata provided by delegation modules

### DelegationResult Metadata Requirements

For validation to work correctly, delegation modules must populate:

```typescript
result.metadata = {
    module: string,                     // Module name
    timestamp: Date,                    // Processing timestamp
    securityValidated: boolean,         // Required for 'security' rule
    dataIntegrity: boolean,             // Required for 'integrity' rule
    performanceMetrics: {               // Required for 'performance' rule
        latency: number,               // Must be < 1000 for pass
        memoryUsage: number,
        cpuUsage: number
    }
}
```

### Error Handling

If a validation rule throws an error:
- The rule is marked as failed
- Error message is captured in validation history
- Overall validation fails (`isValid: false`)
- Validation continues with remaining rules

## References

- **ValidationCoordinator**: `src/edge-agent/core/ValidationCoordinator.ts`
- **ValidationInterface**: `src/edge-agent/interfaces/core/ValidationInterface.ts`
- **DelegationResult**: `src/edge-agent/interfaces/core/DelegationInterface.ts`
- **Edge Agent Architecture**: `docs/architecture/edge-agent-architecture.md`
