# ZeroUI Observability Layer - Redaction and Minimisation Policy

## Overview

This document defines the explicit allow/deny rules for telemetry content in the ZeroUI Observability Layer. The objective is to support debugging, evaluation, and forecasting while minimising sensitive content exposure.

**Policy Version**: v1.0  
**Last Updated**: 2026-01-17  
**Status**: Active

## Principles

1. **Privacy by Design**: Redaction runs before any export
2. **Fingerprints After Redaction**: All fingerprints computed after redaction
3. **Explicit Allow/Deny Lists**: Clear rules for what is permitted/forbidden
4. **Versioned Policy**: Policy changes are versioned and tracked

## C.1 Explicit Allow List (Permitted Fields/Content)

The following fields/content are **explicitly permitted** in telemetry:

### Hashes and Fingerprints
- Hashes/fingerprints of inputs, outputs, prompts, and internal state
- **Never raw content** - only fingerprints/hashes
- SHA-256 hashes (32-byte hex strings)

### Counts and Sizes
- Token counts
- Byte sizes
- Item counts
- Queue depth
- Timing metrics (latency_ms)

### Identifiers
- Version identifiers (prompt_version, model/version, policy version IDs, build IDs)
- Event correlation identifiers (event_id, trace_id, span_id, replay_id, audit_id)
- Component identifiers
- Channel identifiers

### Detector Outcomes
- Bias confidence scores (0.0-1.0)
- Relevance scores (0.0-1.0)
- Timeliness scores (0.0-1.0)
- **Without raw text** - scores only

### Allowlisted Environment Variables
- Only explicitly allowlisted environment key/value pairs
- Must be in `env_allowlisted` object
- Required for debugging only

## C.2 Explicit Deny List (MUST NOT Appear)

The following content is **explicitly forbidden** in telemetry:

### Raw Content
- Raw user inputs
- Raw outputs
- Raw internal state snapshots
- Raw error messages (use fingerprints only)
- Raw stack traces (use fingerprints only)

### Secrets and Credentials
- API keys
- Passwords
- Private keys
- Tokens (authentication, authorization)
- Access tokens
- Refresh tokens
- Any credential material

### Environment Data
- Full environment dumps
- Non-allowlisted environment variables
- System environment variables containing secrets

### Personal Identifiers
- Email addresses
- Social Security Numbers (SSN)
- Credit card numbers
- Phone numbers
- Physical addresses
- Any PII not required for monitoring

### Binary and Documents
- Binary attachments
- Full documents
- Code snippets (use fingerprints only)
- File contents (use fingerprints only)

## C.3 Redaction Contract (Required Controls)

### Redaction Timing
- Redaction **MUST** run before any export
- Applies to: edge agent, extension, core services, collectors
- No raw sensitive content leaves the producer

### Fingerprint Computation
- All fingerprints **MUST** be computed **after** redaction
- Ensures sensitive content does not influence deterministic hashes
- Use SHA-256 for all fingerprints

### Redaction Indicators
- Each event **MUST** carry `redaction_applied=true` where applicable
- Boolean or derived attribute indicating redaction was applied
- Required for audit and compliance

### Privacy Audit Events
- `privacy.audit.v1` **MUST** be emitted for workflows touching user data
- Must state encryption and access control signals
- Required for compliance tracking

## Hashing Rules

### Algorithm
- **SHA-256** for all fingerprints
- 32-byte output, hex-encoded (64 characters)
- Deterministic: same input → same hash

### Fingerprint Fields
- `message_fingerprint`: Error message after redaction
- `input_fingerprint`: Inputs after redaction
- `output_fingerprint`: Outputs after redaction
- `internal_state_fingerprint`: Internal state after redaction
- `stack_fingerprint`: Stack trace after redaction
- `query_fingerprint`: Query after redaction
- `comment_fingerprint`: User comment after redaction
- `reason_fingerprint`: Reason text after redaction
- `failure_reason_fingerprint`: Failure reason after redaction

### Fingerprint Format
- Hex-encoded SHA-256 (64 characters)
- Lowercase
- Example: `a3f5e8b2c1d4f6a7e9b1c3d5f7a9b2c4d6e8f0a1b3c5d7e9f1a3b5c7d9e1f3a5`

## Integration Points

### EPC-2 (Data Governance & Privacy)
- Call `/privacy/v1/compliance` endpoint for PII/secrets detection
- Use EPC-2 redaction rules for policy-driven redaction
- Integration via `RedactionEnforcer`

### CCCS SSDRS (Secure Redaction Service)
- Wrapper around `src/shared_libs/cccs/redaction/service.py`
- Applies redaction rules without mutating originals
- Deep-copy payloads before redaction

## Policy Versioning

- Policy changes require version increment
- Breaking changes require major version bump
- Backward-compatible additions allowed in minor versions
- Document all changes in policy changelog

## References

- PRD Section Appendix C: Telemetry Redaction and Minimisation Rules
- EPC-2 Data Governance & Privacy: `src/cloud_services/shared-services/data-governance-privacy/`
- CCCS SSDRS: `src/shared_libs/cccs/redaction/service.py`
