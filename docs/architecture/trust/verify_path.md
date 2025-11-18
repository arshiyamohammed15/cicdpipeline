# Verification Path

This document describes how policy snapshot verification happens in each plane of the ZeroUI architecture.

## Verification Points

### 1. Client/Tenant Cloud Plane

**When**: Before caching policy snapshot from Policy Registry

**Process**:
1. Receive signed snapshot from Policy Registry
2. Extract KID (Key ID) from snapshot
3. Lookup public key in trust store using KID
4. Verify signature using Ed25519 public key
5. Verify snapshot hash integrity
6. Cache snapshot only if verification succeeds

**Failure Handling**:
- Reject snapshot if signature invalid
- Reject snapshot if KID not found in trust store
- Reject snapshot if hash mismatch
- Log verification failure for audit

### 2. IDE/Edge Agent Plane

**When**: Before using policy snapshot for evaluation

**Process**:
1. Load cached snapshot from local storage
2. Extract KID from snapshot
3. Lookup public key in local trust store (KID-based)
4. Verify signature using Ed25519 public key
5. Verify snapshot hash integrity
6. Use snapshot only if verification succeeds

**Failure Handling**:
- Reject snapshot if signature invalid
- Reject snapshot if KID not found in local trust store
- Reject snapshot if hash mismatch
- Fall back to previous verified snapshot if available
- Log verification failure locally

## Trust Store Structure

### Client/Tenant Cloud Trust Store

```
trust_store/
├── keys/
│   ├── {kid1}.pub    # Ed25519 public key
│   ├── {kid2}.pub    # Ed25519 public key
│   └── ...
└── crl.json          # Certificate Revocation List
```

### IDE/Edge Agent Trust Store

```
{ZU_ROOT}/ide/trust/
├── keys/
│   ├── {kid1}.pub    # Ed25519 public key
│   ├── {kid2}.pub    # Ed25519 public key
│   └── ...
└── crl.json          # Certificate Revocation List (synced)
```

## Verification Algorithm

1. **Extract KID**: `kid = snapshot.kid`
2. **Lookup Public Key**: `public_key = trust_store.get_key(kid)`
3. **Check CRL**: `if kid in crl.revoked_keys: reject`
4. **Verify Signature**: `ed25519.verify(public_key, snapshot.data, snapshot.signature)`
5. **Verify Hash**: `hash(snapshot.data) == snapshot.snapshot_hash`

## Trust Chain

```
Product Cloud (Signs)
  ↓
Policy Registry (Stores + Distributes)
  ↓
Client/Tenant Cloud (Verifies + Caches)
  ↓
IDE/Edge Agent (Verifies + Uses)
```

## Security Considerations

- **Key Rotation**: See `crl_rotation.md` for rotation process
- **Revocation**: Checked before every verification
- **Offline Verification**: IDE/Edge Agent can verify without network (uses cached keys)
- **Audit Trail**: All verification failures logged
