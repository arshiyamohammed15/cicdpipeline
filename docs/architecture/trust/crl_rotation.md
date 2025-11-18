# CRL (Certificate Revocation List) and Key Rotation

This document describes the key rotation and revocation process for policy snapshot signing keys.

## Key Rotation Process

### Rotation Trigger

Keys are rotated:
- **Scheduled**: Every 90 days (automatic rotation)
- **Emergency**: On key compromise or security incident
- **Manual**: On-demand by security team

### Rotation Steps

1. **Generate New Key Pair**
   - Product Cloud generates new Ed25519 key pair
   - New KID assigned (unique identifier)
   - Private key stored securely in KMS

2. **Update Trust Store**
   - Add new public key to Policy Registry trust store
   - Distribute new public key to all clients
   - Update CRL with old key (mark as rotated, not revoked)

3. **Transition Period**
   - Both old and new keys valid for 7 days
   - New snapshots signed with new key
   - Old snapshots still verifiable with old key

4. **Revocation of Old Key**
   - After 7 days, add old key to CRL as revoked
   - Distribute updated CRL to all clients
   - Old key no longer accepted for new snapshots

## CRL Structure

```json
{
  "version": "1.0",
  "issued_at": "2025-01-27T00:00:00Z",
  "next_update": "2025-01-28T00:00:00Z",
  "revoked_keys": [
    {
      "kid": "ed25519-key-2024-10-01",
      "revoked_at": "2025-01-20T00:00:00Z",
      "reason": "key_rotation"
    }
  ],
  "rotated_keys": [
    {
      "kid": "ed25519-key-2024-10-01",
      "rotated_at": "2025-01-20T00:00:00Z",
      "replaced_by": "ed25519-key-2025-01-20"
    }
  ]
}
```

## Distribution

### Policy Registry (Shared Services)
- Maintains authoritative CRL
- Updates CRL on rotation/revocation
- Serves CRL via API endpoint

### Client/Tenant Cloud
- Fetches CRL from Policy Registry
- Caches CRL locally
- Updates cache every 24 hours or on verification failure

### IDE/Edge Agent
- Receives CRL updates from Client/Tenant Cloud
- Caches CRL locally
- Updates cache on policy snapshot fetch

## Emergency Revocation

If a key is compromised:

1. **Immediate Revocation**
   - Add compromised key to CRL immediately
   - Mark reason as "compromise"
   - Distribute updated CRL urgently

2. **Key Replacement**
   - Generate new key pair immediately
   - Sign all new snapshots with new key
   - Distribute new public key to all clients

3. **Notification**
   - Notify all clients of emergency revocation
   - Require immediate CRL update
   - Block verification with revoked key

## Verification with CRL

Before verifying any signature:

1. Check if KID is in `revoked_keys` → Reject if found
2. Check if KID is in `rotated_keys` → Accept if within transition period
3. Verify signature with public key
4. Verify snapshot hash

## Key Lifecycle

```
Key Generated
  ↓
Active (90 days)
  ↓
Rotation Initiated
  ↓
Transition Period (7 days) - Both keys valid
  ↓
Old Key Revoked
  ↓
New Key Active (90 days)
```

## Public Key Distribution

Public keys are distributed via:
1. **Policy Registry API**: `/trust/keys/{kid}`
2. **Trust Store Sync**: Periodic sync from Policy Registry
3. **Snapshot Metadata**: KID included in snapshot for lookup

## Compliance

- **Audit Trail**: All rotations and revocations logged
- **Retention**: CRL history retained for 1 year
- **Access Control**: Only authorized security team can rotate/revoke keys
