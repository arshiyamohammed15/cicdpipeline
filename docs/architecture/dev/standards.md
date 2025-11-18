# Coding Standards

This document defines coding standards for ZeroUI 2.0 development.

## General Principles

1. **Clarity Over Cleverness**: Write clear, readable code
2. **Consistency**: Follow established patterns
3. **Documentation**: Document complex logic
4. **Testing**: Write tests for all code
5. **Security**: Security-first approach

## Language-Specific Standards

### TypeScript (VS Code Extension, Edge Agent)

#### Naming Conventions

- **Files**: `kebab-case.ts` (e.g., `receipt-parser.ts`)
- **Classes**: `PascalCase` (e.g., `ReceiptParser`)
- **Functions**: `camelCase` (e.g., `parseReceipt`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RECEIPT_SIZE`)
- **Interfaces**: `PascalCase` with `I` prefix optional (e.g., `IReceipt` or `Receipt`)

#### Code Style

- **Indentation**: 2 spaces
- **Line Length**: 100 characters max
- **Quotes**: Single quotes for strings
- **Semicolons**: Always use semicolons
- **Trailing Commas**: Use in multi-line objects/arrays

#### Example

```typescript
import { ReceiptParser } from './receipt-parser';

const MAX_RECEIPT_SIZE = 1024 * 1024; // 1MB

export class ReceiptValidator {
  private parser: ReceiptParser;

  constructor(parser: ReceiptParser) {
    this.parser = parser;
  }

  public validate(receiptJson: string): boolean {
    if (receiptJson.length > MAX_RECEIPT_SIZE) {
      return false;
    }
    return this.parser.parse(receiptJson) !== null;
  }
}
```

### Python (Cloud Services)

#### Naming Conventions

- **Files**: `snake_case.py` (e.g., `receipt_validator.py`)
- **Classes**: `PascalCase` (e.g., `ReceiptValidator`)
- **Functions**: `snake_case` (e.g., `validate_receipt`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RECEIPT_SIZE`)
- **Private**: Prefix with `_` (e.g., `_internal_method`)

#### Code Style

- **Style Guide**: PEP 8
- **Line Length**: 100 characters max
- **Indentation**: 4 spaces
- **Imports**: Grouped (stdlib, third-party, local)

#### Example

```python
from typing import Optional
from .receipt_parser import ReceiptParser

MAX_RECEIPT_SIZE = 1024 * 1024  # 1MB

class ReceiptValidator:
    def __init__(self, parser: ReceiptParser):
        self._parser = parser

    def validate(self, receipt_json: str) -> bool:
        if len(receipt_json) > MAX_RECEIPT_SIZE:
            return False
        return self._parser.parse(receipt_json) is not None
```

## File Organization

### TypeScript Projects

```
src/
├── core/              # Core framework
├── modules/           # Feature modules
├── shared/            # Shared utilities
└── types/             # Type definitions
```

### Python Projects

```
src/
├── core/              # Core framework
├── services/          # Service modules
├── shared/            # Shared utilities
└── models/            # Data models
```

## Documentation

### Code Comments

- **Purpose**: Explain "why", not "what"
- **Complex Logic**: Document complex algorithms
- **Public APIs**: Document all public functions/classes

### Example

```typescript
/**
 * Validates a receipt signature using Ed25519 public key.
 *
 * @param receipt - The receipt to validate
 * @param publicKey - The Ed25519 public key (base64-encoded)
 * @returns True if signature is valid, false otherwise
 *
 * @throws {Error} If public key format is invalid
 */
public validateSignature(receipt: Receipt, publicKey: string): boolean {
  // Implementation
}
```

## Testing

### Test Organization

- **Unit Tests**: Test individual functions/classes
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test end-to-end workflows

### Test Naming

- **Files**: `*.test.ts` or `*.spec.ts`
- **Suites**: Describe what is being tested
- **Cases**: Describe expected behavior

### Example

```typescript
describe('ReceiptValidator', () => {
  describe('validate', () => {
    it('should return true for valid receipt', () => {
      // Test implementation
    });

    it('should return false for receipt exceeding size limit', () => {
      // Test implementation
    });
  });
});
```

## Error Handling

### Principles

1. **Fail Fast**: Detect errors early
2. **Clear Messages**: Provide actionable error messages
3. **Logging**: Log errors with context
4. **Recovery**: Implement recovery where possible

### Example

```typescript
try {
  const receipt = await this.loadReceipt(receiptId);
  return receipt;
} catch (error) {
  if (error instanceof FileNotFoundError) {
    this.logger.warn(`Receipt not found: ${receiptId}`);
    return null;
  }
  this.logger.error(`Failed to load receipt: ${receiptId}`, error);
  throw new ReceiptLoadError(`Failed to load receipt: ${receiptId}`, error);
}
```

## Security

### Principles

1. **Input Validation**: Validate all inputs
2. **Output Encoding**: Encode outputs to prevent injection
3. **Secrets Management**: Never commit secrets
4. **Least Privilege**: Use minimum required permissions

### Example

```typescript
// Validate input
if (!receiptId || typeof receiptId !== 'string') {
  throw new ValidationError('Receipt ID must be a non-empty string');
}

// Sanitize output
const sanitizedId = receiptId.replace(/[^a-zA-Z0-9-]/g, '');
```

## Performance

### Principles

1. **Measure First**: Profile before optimizing
2. **Cache Wisely**: Cache expensive operations
3. **Async Operations**: Use async/await for I/O
4. **Lazy Loading**: Load resources on demand

## Git Practices

### Commit Messages

- **Format**: `<type>: <subject>`
- **Types**: feat, fix, docs, style, refactor, test, chore
- **Length**: Subject < 50 characters, body < 72 characters per line

### Branch Naming

- **Feature**: `feature/<name>`
- **Fix**: `fix/<name>`
- **Hotfix**: `hotfix/<name>`

## Code Review

### Review Checklist

- [ ] Code follows style guide
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No security issues
- [ ] Performance acceptable
- [ ] Error handling appropriate

### Review Process

1. **Self-Review**: Review your own code first
2. **Create PR**: Create pull request
3. **Address Feedback**: Respond to review comments
4. **Merge**: Merge after approval

## Tools

### Linting

- **TypeScript**: ESLint with TypeScript plugin
- **Python**: pylint, flake8, mypy

### Formatting

- **TypeScript**: Prettier
- **Python**: black

### Testing

- **TypeScript**: Jest, Vitest
- **Python**: pytest

## Continuous Improvement

- **Regular Reviews**: Review and update standards quarterly
- **Team Feedback**: Incorporate team feedback
- **Industry Best Practices**: Stay updated with industry standards
