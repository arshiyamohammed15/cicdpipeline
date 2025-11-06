# Role-Based Access Control (RBAC)

This document defines roles and permissions for ZeroUI 2.0.

## Roles

### Administrator

**Description**: Full system access

**Permissions**:
- Create, read, update, delete policies
- Manage users and roles
- Access all system data
- Configure system settings
- Rollback policies
- Emergency overrides

**Use Cases**:
- System configuration
- Policy management
- User management
- Emergency response

### Security Team

**Description**: Security and compliance oversight

**Permissions**:
- Read all policies
- Create security policies
- Access audit logs
- Emergency policy rollback
- Key rotation and revocation
- Security incident response

**Use Cases**:
- Security policy enforcement
- Compliance audits
- Incident response
- Key management

### Policy Administrator

**Description**: Policy management

**Permissions**:
- Create, read, update policies
- Rollback policies (with approval)
- View policy metrics
- Manage gate tables
- Cannot delete policies (requires admin)

**Use Cases**:
- Policy creation and updates
- Gate configuration
- Policy rollback

### Developer

**Description**: Standard developer access

**Permissions**:
- Read policies
- View own receipts
- View own decisions
- Submit feedback
- Cannot modify policies

**Use Cases**:
- View gate decisions
- Understand policy requirements
- Provide feedback

### Viewer

**Description**: Read-only access

**Permissions**:
- Read policies (public only)
- View public metrics
- Cannot access user-specific data

**Use Cases**:
- Public documentation
- System status monitoring

## Permissions Matrix

| Action | Admin | Security | Policy Admin | Developer | Viewer |
|--------|-------|----------|-------------|-----------|--------|
| Create Policy | ✅ | ✅ | ✅ | ❌ | ❌ |
| Update Policy | ✅ | ✅ | ✅ | ❌ | ❌ |
| Delete Policy | ✅ | ❌ | ❌ | ❌ | ❌ |
| Rollback Policy | ✅ | ✅ | ⚠️* | ❌ | ❌ |
| View Policies | ✅ | ✅ | ✅ | ✅ | ⚠️** |
| Manage Users | ✅ | ❌ | ❌ | ❌ | ❌ |
| View Audit Logs | ✅ | ✅ | ⚠️*** | ❌ | ❌ |
| Key Management | ✅ | ✅ | ❌ | ❌ | ❌ |
| Emergency Override | ✅ | ✅ | ❌ | ❌ | ❌ |
| View Own Receipts | ✅ | ✅ | ✅ | ✅ | ❌ |
| View All Receipts | ✅ | ✅ | ⚠️*** | ❌ | ❌ |
| Submit Feedback | ✅ | ✅ | ✅ | ✅ | ❌ |

*With approval  
**Public policies only  
***Own actions only

## Access Control Implementation

### Policy Registry

```python
# Example permission check
def update_policy(policy_id: str, user: User) -> bool:
    if user.role in ['admin', 'policy_admin']:
        return True
    return False
```

### Edge Agent

```typescript
// Example permission check
function canViewReceipt(receipt: Receipt, user: User): boolean {
  if (user.role === 'admin' || user.role === 'security') {
    return true;
  }
  if (user.role === 'developer' && receipt.actor.repo_id === user.repo_id) {
    return true;
  }
  return false;
}
```

## Authentication

### Methods

1. **OAuth2**: For web interfaces
2. **JWT Tokens**: For API access
3. **API Keys**: For service-to-service
4. **SSO**: For enterprise integration

### Token Management

- **Expiration**: Tokens expire after 24 hours
- **Refresh**: Refresh tokens valid for 30 days
- **Revocation**: Tokens can be revoked immediately

## Authorization

### Policy-Based Access

Access is determined by:
1. **User Role**: Primary role assignment
2. **Resource Permissions**: Resource-specific permissions
3. **Context**: Request context (IP, time, etc.)

### Example Authorization Flow

```
User Request
  ↓
Authenticate (verify token)
  ↓
Get User Role
  ↓
Check Resource Permissions
  ↓
Check Context (if applicable)
  ↓
Grant/Deny Access
```

## Audit Logging

All access is logged:
- **Who**: User ID and role
- **What**: Action performed
- **When**: Timestamp
- **Where**: Source IP and user agent
- **Result**: Success or failure

## Best Practices

1. **Least Privilege**: Grant minimum required permissions
2. **Regular Review**: Review permissions quarterly
3. **Separation of Duties**: Critical actions require dual approval
4. **Audit Trail**: All actions logged
5. **Principle of Least Surprise**: Permissions should be intuitive

## Role Assignment

### Process

1. **Request**: User requests role assignment
2. **Approval**: Manager approves request
3. **Assignment**: Admin assigns role
4. **Notification**: User notified of role assignment
5. **Audit**: Assignment logged

### Revocation

Roles can be revoked:
- **Manual**: By administrator
- **Automatic**: On user deactivation
- **Temporary**: Time-limited assignments

## Emergency Access

### Break-Glass Procedure

In emergencies:
1. **Request**: Request emergency access
2. **Approval**: Security team approves
3. **Temporary Role**: Temporary elevated role assigned
4. **Time Limit**: Access expires after 4 hours
5. **Review**: Post-incident review required

## Compliance

### Requirements

- **SOC 2**: Access controls documented and enforced
- **GDPR**: User data access logged
- **HIPAA**: Healthcare data access restricted

### Auditing

- **Quarterly**: Review all role assignments
- **Annually**: Full access control audit
- **On-Demand**: Audit on security incident

