# ZeroUI Observability Layer - Schema Versioning Policy

## Overview

This document defines the versioning policy for ZeroUI Observability Layer schemas, including the event envelope schema and all event payload schemas.

## Version Format

Schemas use **semantic versioning** (SemVer) format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (incompatible schema changes)
- **MINOR**: Backward-compatible additions (new optional fields)
- **PATCH**: Backward-compatible bug fixes (documentation, validation improvements)

## Current Versions

- **Event Envelope**: `v1` (zero_ui.obsv.event.v1)
- **Event Payloads**: `v1` (e.g., error.captured.v1)

## Versioning Rules

### Major Version Changes (Breaking)

A major version increment is required when:

1. **Removing required fields** from the schema
2. **Changing field types** (e.g., string → number)
3. **Removing enum values** that are in use
4. **Changing field semantics** in a way that breaks existing consumers
5. **Removing optional fields** that are widely used

**Migration Required**: Yes - consumers must update to new schema version

### Minor Version Changes (Backward Compatible)

A minor version increment is allowed when:

1. **Adding optional fields** to the schema
2. **Adding new enum values** (existing values remain valid)
3. **Relaxing validation constraints** (e.g., making a field optional)
4. **Adding new event types** (doesn't affect existing types)

**Migration Required**: No - existing consumers continue to work

### Patch Version Changes (Backward Compatible)

A patch version increment is allowed when:

1. **Fixing validation bugs** (e.g., incorrect regex patterns)
2. **Improving documentation** in schema descriptions
3. **Clarifying field semantics** without changing behavior
4. **Fixing typos** in field names or descriptions

**Migration Required**: No - existing consumers continue to work

## Backward Compatibility Rules

### Required Fields

- **Never remove** required fields in the same major version
- **Never change types** of required fields in the same major version
- **Can add** new required fields only in a new major version (with migration path)

### Optional Fields

- **Can add** optional fields in minor versions
- **Can remove** optional fields only in major versions (with deprecation notice)
- **Can change types** of optional fields only in major versions

### Enums

- **Can add** new enum values in minor versions
- **Cannot remove** enum values in the same major version
- **Cannot change** enum value strings in the same major version

## Migration Guidelines

### For Schema Authors

1. **Deprecation Period**: Deprecate fields/values for at least one minor version before removal
2. **Documentation**: Clearly document breaking changes in migration guides
3. **Validation**: Provide validation tools to detect incompatible schema usage
4. **Testing**: Maintain test fixtures for all supported versions

### For Schema Consumers

1. **Version Detection**: Check schema version before processing events
2. **Graceful Degradation**: Handle missing optional fields gracefully
3. **Validation**: Validate against known schema versions before processing
4. **Migration Testing**: Test migration paths before deploying

## Schema Registry Integration

Future integration with EPC-12 (Contracts & Schema Registry) will:

- Register all schema versions in the registry
- Provide compatibility checking between versions
- Support schema evolution workflows
- Maintain version history and migration paths

## Examples

### Breaking Change (Major Version)

```json
// v1: required field
{
  "required": ["error_code", "error_class"]
}

// v2: removed error_code (BREAKING)
{
  "required": ["error_class"]
}
```

### Backward Compatible Addition (Minor Version)

```json
// v1: optional field
{
  "properties": {
    "error_code": {"type": "string"}
  }
}

// v1.1: added optional field (NON-BREAKING)
{
  "properties": {
    "error_code": {"type": "string"},
    "error_category": {"type": "string"}  // NEW
  }
}
```

### Bug Fix (Patch Version)

```json
// v1.0: incorrect regex
{
  "event_id": {
    "type": "string",
    "pattern": "^[a-z]+$"  // Too restrictive
  }
}

// v1.0.1: fixed regex
{
  "event_id": {
    "type": "string",
    "pattern": "^[a-zA-Z0-9_-]+$"  // FIXED
  }
}
```

## References

- JSON Schema Draft 2020-12: https://json-schema.org/draft/2020-12/schema
- Semantic Versioning: https://semver.org/
- EPC-12 Contracts & Schema Registry: `src/cloud_services/shared-services/contracts-schema-registry/`
