# Edge Agent Storage Module

## Overview

Storage integration for Edge Agent following 4-Plane Storage Architecture rules.

## Components

### StoragePathResolver
Resolves storage paths using ZU_ROOT environment variable (Rule 223).

**Usage**:
```typescript
import { StoragePathResolver } from './shared/storage/StoragePathResolver';

const resolver = new StoragePathResolver(); // Uses process.env.ZU_ROOT
// Or specify explicitly:
const resolver = new StoragePathResolver('D:\\ZeroUI\\development');

// Resolve receipt path
const receiptPath = resolver.resolveReceiptPath('my-repo', 2025, 10);
// Returns: {ZU_ROOT}/ide/receipts/my-repo/2025/10/
```

### ReceiptStorageService
Stores receipts in IDE Plane (Rule 219: JSONL, append-only, signed).

**Usage**:
```typescript
import { ReceiptStorageService } from './shared/storage/ReceiptStorageService';
import { ReceiptGenerator } from './shared/storage/ReceiptGenerator';
import * as fs from 'fs';

const storage = new ReceiptStorageService();
const privateKeyPem = fs.readFileSync('path/to/ide/trust/private/edge-agent.pem', 'utf-8');
const generator = new ReceiptGenerator({
    privateKey: privateKeyPem,
    keyId: 'edge-agent'
});

// Generate receipt
const receipt = generator.generateDecisionReceipt(...);

// Store receipt
const receiptPath = await storage.storeDecisionReceipt(receipt, 'my-repo');
```

### ReceiptGenerator
Generates signed receipts (Rule 224: receipts must be signed).

**Features**:
- Generates unique receipt IDs
- Signs receipts cryptographically
- Validates receipt structure

### PolicyStorageService
Stores policy snapshots in IDE Plane (cache) and Product Plane (registry).

**Usage**:
```typescript
import { PolicyStorageService } from './shared/storage/PolicyStorageService';

const policyStorage = new PolicyStorageService();

// Cache policy in IDE Plane
await policyStorage.cachePolicy(policySnapshot);

// Read cached policy
const cached = await policyStorage.readCachedPolicy('policy-id', '1.0.0');
```

## Storage Compliance

### Rules Enforced

- **Rule 216**: Kebab-case naming only `[a-z0-9-]`
- **Rule 217**: No code/PII in stores (validated before storage)
- **Rule 219**: JSONL receipts (append-only, newline-delimited, signed)
- **Rule 223**: Path resolution via ZU_ROOT (no hardcoded paths)
- **Rule 224**: Receipts validation (signed, append-only)
- **Rule 228**: Laptop receipts use YYYY/MM month partitioning

### Storage Paths

- **Receipts**: `{ZU_ROOT}/ide/receipts/{repo-id}/{yyyy}/{mm}/receipts.jsonl`
- **Policy Cache**: `{ZU_ROOT}/ide/policy/cache/{policy-id}-{version}.json`
- **Policy Current**: `{ZU_ROOT}/ide/policy/current/{policy-id}.json`

## Error Handling

All storage operations throw errors if:
- ZU_ROOT is not set
- Path components are not kebab-case
- Receipts are missing signatures
- Receipts contain code or PII

## Dependencies

- Node.js `fs` module (file system operations)
- Node.js `path` module (path operations)
- Node.js `crypto` module (signature generation)

## Environment Variables

- `ZU_ROOT`: Required. Base path for storage operations.

## Testing

Storage operations should be tested with:
- Mock file system
- Temporary ZU_ROOT paths
- Signature validation
- Path validation

