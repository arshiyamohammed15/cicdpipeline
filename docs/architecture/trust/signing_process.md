# Signing Process

This document describes who signs policy snapshots and where signing occurs in the ZeroUI architecture.

## Signing Authority

**Product Cloud** is responsible for signing policy snapshots before distribution.

## Signing Location

Signing occurs in the **ZeroUI Product Cloud Plane** during the policy compilation process:

1. Policy Compiler compiles rule changes into a policy snapshot
2. Snapshot is created with hash, KID (Key ID), and version IDs
3. Product Cloud signs the snapshot using Ed25519 private key
4. Signed snapshot is published to Policy Registry (Shared Services Plane)

## Signing Process Flow

```
Policy Compiler (Product Cloud)
  ↓
Generate Snapshot (hash, KID, version_ids)
  ↓
Sign with Ed25519 Private Key
  ↓
Publish to Policy Registry (Shared Services)
  ↓
Distribution to Clients and Laptops
```

## Key Management

- **Private Keys**: Stored securely in Product Cloud Key Management Service
- **Public Keys**: Distributed via Policy Registry and trust store
- **Key Rotation**: Managed through CRL (Certificate Revocation List) - see `crl_rotation.md`

## Signature Format

Signatures use Ed25519 algorithm:
- **Algorithm**: Ed25519
- **Key ID (KID)**: Identifies the signing key
- **Signature**: Base64-encoded Ed25519 signature
- **Verification**: Public key lookup by KID, signature verification

## Verification

Verification occurs at:
1. **Client/Tenant Cloud**: Before caching policy snapshot
2. **IDE/Edge Agent**: Before using policy snapshot for evaluation

See `verify_path.md` for detailed verification process.

