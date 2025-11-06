# VS Code Extension Storage Module

## Overview

Storage integration for VS Code Extension following 4-Plane Storage Architecture rules.

## Components

### StoragePathResolver
Resolves storage paths using ZU_ROOT (from environment variable or VS Code configuration).

**Usage**:
```typescript
import { StoragePathResolver } from './shared/storage/StoragePathResolver';

const resolver = new StoragePathResolver(); 
// Uses: process.env.ZU_ROOT or vscode.workspace.getConfiguration('zeroui').get('zuRoot')

const receiptPath = resolver.resolveReceiptPath('my-repo', 2025, 10);
```

### ReceiptStorageReader
Reads receipts from IDE Plane storage.

**Usage**:
```typescript
import { ReceiptStorageReader } from './shared/storage/ReceiptStorageReader';

const reader = new ReceiptStorageReader();

// Read receipts for a specific month
const receipts = await reader.readReceipts('my-repo', 2025, 10);

// Read latest receipts
const latest = await reader.readLatestReceipts('my-repo', 10);

// Read receipts in date range
const rangeReceipts = await reader.readReceiptsInRange(
    new Date('2025-01-01'),
    new Date('2025-01-31')
);
```

## Configuration

### VS Code Settings

Add to `package.json` configuration:
```json
{
  "zeroui.zuRoot": {
    "type": "string",
    "default": "",
    "description": "ZU_ROOT path for storage operations"
  },
  "zeroui.repoId": {
    "type": "string",
    "default": "",
    "description": "Repository identifier for receipt storage"
  }
}
```

### Environment Variables

- `ZU_ROOT`: Base path for storage operations (if not set in configuration)

## Storage Compliance

### Rules Enforced

- **Rule 219**: JSONL receipts (newline-delimited)
- **Rule 223**: Path resolution via ZU_ROOT
- **Rule 224**: Receipt signature validation

### Storage Paths

- **Receipts**: `{ZU_ROOT}/ide/receipts/{repo-id}/{yyyy}/{mm}/receipts.jsonl`

## Integration

### ReceiptViewerManager

The `ReceiptViewerManager` automatically loads receipts from storage when showing the receipt viewer.

```typescript
import { ReceiptViewerManager } from './ui/receipt-viewer/ReceiptViewerManager';

const manager = new ReceiptViewerManager();
await manager.showReceiptViewer(); // Automatically loads latest receipt
```

## Error Handling

Storage operations handle errors gracefully:
- Missing ZU_ROOT: Shows warning message
- Missing receipts: Returns empty array
- Invalid receipts: Logs error and skips

## Dependencies

- VS Code API (`vscode` module)
- Node.js `fs` module
- Node.js `path` module
- ReceiptParser (for receipt validation)

