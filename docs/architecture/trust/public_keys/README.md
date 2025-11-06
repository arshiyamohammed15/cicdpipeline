# Public Keys Trust Store

This directory contains Ed25519 public keys used to verify policy snapshot signatures.

## Key Format

Public keys are stored as:
- **File Name**: `{kid}.pub` where `{kid}` is the Key ID
- **Format**: Base64-encoded Ed25519 public key (32 bytes)
- **Content**: Single line with public key data

## Key Lookup

Keys are looked up by KID (Key ID) which is included in policy snapshots:

```json
{
  "snapshot_id": "...",
  "kid": "ed25519-key-2025-01-20",
  "signature": "...",
  ...
}
```

The KID `ed25519-key-2025-01-20` maps to file `ed25519-key-2025-01-20.pub`.

## Key Distribution

**Note**: This directory is a reference. Actual public keys are:

1. **Stored in Policy Registry** (Shared Services Plane)
   - Authoritative source
   - Served via API: `/trust/keys/{kid}`

2. **Cached in Client/Tenant Cloud**
   - Synced from Policy Registry
   - Cached for offline verification

3. **Cached in IDE/Edge Agent**
   - Synced from Client/Tenant Cloud
   - Stored in `{ZU_ROOT}/ide/trust/keys/`

## Adding Keys

To add a new public key:

1. Receive key from Product Cloud (secure channel)
2. Verify key authenticity (out of band)
3. Store as `{kid}.pub` file
4. Update trust store index
5. Distribute to all clients

## Key Rotation

See `../crl_rotation.md` for key rotation process.

When keys are rotated:
- Old key remains for transition period (7 days)
- New key added with new KID
- Old key eventually revoked via CRL

## Security

- **Read-Only**: Public keys are read-only (no private keys stored)
- **Verification**: Always verify key authenticity before adding
- **Distribution**: Use secure channels for key distribution
- **Revocation**: Check CRL before using any key

## Example Key File

```
ed25519-key-2025-01-20.pub
```

Content:
```
MCowBQYDK2VwAyEA1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ==
```

## Trust Store Location

- **Policy Registry**: `trust_store/keys/{kid}.pub`
- **Client/Tenant**: `trust_store/keys/{kid}.pub`
- **IDE/Edge Agent**: `{ZU_ROOT}/ide/trust/keys/{kid}.pub`

