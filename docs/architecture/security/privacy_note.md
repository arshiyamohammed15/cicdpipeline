# Privacy Note

This document describes ZeroUI 2.0's privacy stance and data handling practices.

## Privacy Philosophy

**Metadata-Only by Default**: ZeroUI 2.0 is designed to operate on metadata only. Raw code is not sent to cloud services by default.

## Data Collection

### What We Collect

1. **Receipts**: Decision receipts containing:
   - Gate decisions (pass/warn/block)
   - Decision rationale
   - Policy references
   - Timestamps
   - Repository identifiers (hashed)

2. **Feedback**: User feedback on decisions:
   - Whether decision was helpful
   - Feedback patterns
   - Timestamps

3. **Metrics**: Aggregated metrics:
   - Decision counts
   - Policy usage
   - Performance metrics

### What We Do NOT Collect

1. **Raw Code**: Source code is not sent to cloud services
2. **File Contents**: File contents are not collected
3. **Personal Information**: Minimal PII collected (only necessary identifiers)
4. **Credentials**: Passwords, API keys, tokens are never collected

## Data Processing

### Local Processing

- **Edge Agent**: All processing happens locally on developer machine
- **No Cloud Dependency**: Decisions can be made without cloud connectivity
- **Privacy First**: Sensitive data stays local

### Cloud Processing

- **Metadata Only**: Only metadata sent to cloud
- **Anonymized**: Data anonymized before learning loop
- **Redacted**: PII and code redacted before sharing

## Data Storage

### Local Storage (IDE/Edge Agent)

- **Location**: `{ZU_ROOT}/ide/`
- **Encryption**: Optional local encryption
- **Retention**: User-controlled
- **Access**: Local user only

### Client/Tenant Cloud

- **Location**: Tenant-controlled storage
- **Encryption**: At rest and in transit
- **Retention**: Per tenant policy
- **Access**: Tenant-controlled

### Product Cloud

- **Location**: ZeroUI-controlled storage
- **Encryption**: At rest and in transit
- **Retention**: 7 years (compliance)
- **Access**: ZeroUI security team only

## Data Sharing

### Cross-Plane Sharing

- **Privacy Split**: Data redacted before cross-plane sharing
- **Explicit Consent**: User consent required for code sharing
- **Audit Trail**: All sharing logged

### Third-Party Sharing

- **No Third-Party Sharing**: Data not shared with third parties
- **Compliance**: Sharing only for legal compliance
- **Notification**: Users notified of any sharing

## User Rights

### Access

Users can:
- View their own receipts
- Export their data
- Request data access

### Deletion

Users can:
- Request data deletion
- Delete local receipts
- Request cloud data deletion

### Correction

Users can:
- Correct inaccurate data
- Update preferences
- Revoke consent

## Security Measures

### Encryption

- **At Rest**: All data encrypted at rest
- **In Transit**: All data encrypted in transit (TLS 1.3+)
- **Keys**: Managed by Key Management Service

### Access Controls

- **Role-Based**: Access based on user role
- **Least Privilege**: Minimum required access
- **Audit Logging**: All access logged

### Data Minimization

- **Collect Minimum**: Only collect necessary data
- **Retain Minimum**: Retain only as long as needed
- **Process Minimum**: Process only necessary data

## Compliance

### GDPR

- **Lawful Basis**: Legitimate interest for metadata processing
- **User Rights**: Access, deletion, correction supported
- **Data Protection**: Technical and organizational measures

### SOC 2

- **Privacy Controls**: Privacy controls implemented
- **Access Controls**: Access controls enforced
- **Audit Logging**: Comprehensive audit logging

### CCPA

- **Disclosure**: Privacy practices disclosed
- **User Rights**: Access and deletion supported
- **No Sale**: Data not sold to third parties

## Transparency

### Privacy Policy

- **Location**: Public privacy policy available
- **Updates**: Policy updated as needed
- **Notification**: Users notified of significant changes

### Data Processing

- **Purpose**: Data processing purpose disclosed
- **Legal Basis**: Legal basis for processing disclosed
- **Retention**: Data retention periods disclosed

## Opt-Out

### Local Processing

- **Always Available**: Local processing always available
- **No Opt-Out Needed**: No cloud dependency for decisions

### Cloud Features

- **Optional**: Cloud features are optional
- **Opt-Out**: Users can opt out of cloud features
- **Local Alternative**: Local alternatives available

## Contact

### Privacy Inquiries

- **Email**: privacy@zeroui.com
- **Response Time**: Within 30 days
- **Process**: Privacy inquiry process documented

### Data Protection Officer

- **Role**: Data Protection Officer appointed
- **Contact**: dpo@zeroui.com
- **Responsibilities**: Privacy compliance oversight

## Updates

This privacy note is updated:
- **Quarterly**: Regular review and updates
- **On Changes**: When practices change
- **Notification**: Users notified of significant changes

## Commitment

ZeroUI 2.0 is committed to:
- **Privacy by Design**: Privacy built into architecture
- **Transparency**: Open about data practices
- **User Control**: Users control their data
- **Security**: Strong security measures
- **Compliance**: Compliance with privacy regulations
