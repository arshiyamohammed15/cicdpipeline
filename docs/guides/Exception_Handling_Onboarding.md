# Exception Handling Onboarding Guide

This guide helps new developers implement proper exception handling following Rules 150-181 from the ZeroUI 2.0 Constitution.

## First Error Handling Task

### Step 1: Fix 3 `any` Types in Existing Code

**Goal**: Replace `any` types with proper TypeScript types.

**Example**:
```typescript
// Before (Rule 182 violation)
function processData(data: any): any {
    return data.someProperty;
}

// After (Rule 182 compliant)
interface DataItem {
    someProperty: string;
    id: number;
}

function processData(data: DataItem): string {
    return data.someProperty;
}
```

**Checklist**:
- [ ] Find 3 functions using `any` type
- [ ] Define proper interfaces or types
- [ ] Replace `any` with specific types
- [ ] Test the changes
- [ ] Verify no new TypeScript errors

### Step 2: Add Proper Error Handling to One Async Function

**Goal**: Implement central error handling for async operations.

**Example**:
```typescript
// Before (Rule 195 violation)
async function fetchUserData(userId: string) {
    const response = await fetch(`/api/users/${userId}`);
    return response.json();
}

// After (Rules 195, 196, 197, 198 compliant)
async function fetchUserData(userId: string): Promise<UserData> {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);

        const response = await fetch(`/api/users/${userId}`, {
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        // Map to canonical error code (Rule 198)
        if ((error as Error).name === 'AbortError') {
            throw new Error('TIMEOUT: Request timed out after 5 seconds');
        }

        // Provide user-friendly message (Rule 197)
        throw new Error('DEPENDENCY_FAILED: Unable to fetch user data. Please try again.');
    }
}
```

**Checklist**:
- [ ] Identify one async function without error handling
- [ ] Add try/catch block
- [ ] Add timeout handling (Rule 196)
- [ ] Map errors to canonical codes (Rule 198)
- [ ] Provide user-friendly error messages (Rule 197)
- [ ] Test error scenarios

### Step 3: Write Tests for the Fixed Function

**Goal**: Ensure error handling works correctly.

**Example**:
```typescript
describe('fetchUserData', () => {
    it('should return user data on success', async () => {
        // Mock successful response
        global.fetch = jest.fn().mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ id: 1, name: 'Test User' })
        });

        const result = await fetchUserData('1');
        expect(result).toEqual({ id: 1, name: 'Test User' });
    });

    it('should handle timeout errors', async () => {
        // Mock timeout
        global.fetch = jest.fn().mockImplementation(() =>
            new Promise((_, reject) => {
                setTimeout(() => reject(new Error('AbortError')), 100);
            })
        );

        await expect(fetchUserData('1')).rejects.toThrow('TIMEOUT');
    });

    it('should handle network errors', async () => {
        // Mock network error
        global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

        await expect(fetchUserData('1')).rejects.toThrow('DEPENDENCY_FAILED');
    });
});
```

**Checklist**:
- [ ] Write test for happy path
- [ ] Write test for timeout scenario
- [ ] Write test for network error scenario
- [ ] Write test for invalid response scenario
- [ ] Run tests and verify they pass

### Step 4: Review One AI-Generated TypeScript File

**Goal**: Ensure AI-generated code follows TypeScript standards.

**Review Checklist**:
- [ ] No `any` types used (Rule 182)
- [ ] Proper null/undefined handling (Rule 183)
- [ ] Functions are small and clear (Rule 184)
- [ ] Consistent naming conventions (Rule 185)
- [ ] Clear interfaces defined (Rule 186)
- [ ] No redundant type annotations (Rule 187)
- [ ] Clean import statements (Rule 188)
- [ ] Proper error handling (Rules 195-199)
- [ ] No secrets in code (Rule 208)
- [ ] Input validation present (Rule 209)

**Example Review**:
```typescript
// AI-generated code (needs review)
function processUserData(userData: any): any {
    const result = userData.name.toUpperCase();
    return { processed: result };
}

// Reviewed and improved code
interface UserData {
    name: string;
    email: string;
    id: number;
}

interface ProcessedUserData {
    processed: string;
    originalId: number;
}

function processUserData(userData: UserData): ProcessedUserData {
    if (!userData?.name) {
        throw new Error('VALIDATION_ERROR: User name is required');
    }

    const result = userData.name.toUpperCase();
    return {
        processed: result,
        originalId: userData.id
    };
}
```

### Step 5: Verify No New Lint Warnings

**Goal**: Maintain code quality standards.

**Commands**:
```bash
# Run TypeScript compiler
npx tsc --noEmit

# Run ESLint
npx eslint src/ --ext .ts,.tsx

# Run Prettier
npx prettier --check src/
```

**Checklist**:
- [ ] No TypeScript compilation errors
- [ ] No ESLint warnings or errors
- [ ] Code formatted with Prettier
- [ ] All tests pass

### Step 6: Check Bundle Size Impact

**Goal**: Ensure changes don't significantly increase bundle size.

**Commands**:
```bash
# Build and analyze bundle
npm run build
npm run analyze

# Check bundle size limits
npm run bundle-size-check
```

**Checklist**:
- [ ] Bundle size within acceptable limits
- [ ] No new large dependencies added
- [ ] Tree-shaking working correctly
- [ ] No circular dependencies

## Error Wrapping Examples

### Basic Error Wrapping (Rule 152)

```typescript
// Wrap low-level errors with context
try {
    const data = JSON.parse(jsonString);
    return data;
} catch (error) {
    // Add context to the error
    throw new Error(`VALIDATION_ERROR: Failed to parse JSON string: ${(error as Error).message}`, {
        cause: error,
        context: { jsonString: jsonString.substring(0, 100) }
    });
}
```

### Central Handler Usage (Rule 154)

```typescript
// Use central error handler
import { handleError } from './error-handler';

async function processFile(filePath: string) {
    try {
        const content = await fs.readFile(filePath, 'utf-8');
        return processContent(content);
    } catch (error) {
        // Central handler maps error to canonical code and provides user message
        return handleError(error, {
            context: { filePath, operation: 'processFile' }
        });
    }
}
```

### Recovery Pattern Examples (Rule 158)

```typescript
// Retry with exponential backoff
async function retryOperation<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    baseDelay: number = 1000
): Promise<T> {
    let lastError: Error;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            return await operation();
        } catch (error) {
            lastError = error as Error;

            if (attempt === maxRetries) {
                break;
            }

            // Exponential backoff with jitter
            const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 100;
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }

    throw new Error(`OPERATION_FAILED: Failed after ${maxRetries + 1} attempts: ${lastError.message}`, {
        cause: lastError
    });
}
```

## Common Patterns

### Timeout Pattern (Rule 161)

```typescript
function withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
    return Promise.race([
        promise,
        new Promise<never>((_, reject) => {
            setTimeout(() => reject(new Error('TIMEOUT_ERROR')), timeoutMs);
        })
    ]);
}

// Usage
const result = await withTimeout(fetchUserData('123'), 5000);
```

### Idempotency Pattern (Rule 164)

```typescript
async function idempotentOperation(id: string, data: any) {
    // Check if operation already completed
    const existing = await getOperationStatus(id);
    if (existing?.status === 'completed') {
        return existing.result;
    }

    // Perform operation
    const result = await performOperation(data);

    // Mark as completed
    await markOperationCompleted(id, result);

    return result;
}
```

### Graceful Degradation (Rule 179)

```typescript
async function getDataWithFallback() {
    try {
        // Try primary data source
        return await fetchFromPrimarySource();
    } catch (error) {
        console.warn('Primary source failed, trying fallback:', error);

        try {
            // Try fallback source
            return await fetchFromFallbackSource();
        } catch (fallbackError) {
            // Return cached data or default values
            return getCachedData() || getDefaultData();
        }
    }
}
```

## Testing Error Scenarios

### Test Error Mapping (Rule 198)

```typescript
describe('Error Mapping', () => {
    it('should map database errors to canonical codes', () => {
        const dbError = new Error('Connection timeout');
        const mapped = mapErrorToCode(dbError);

        expect(mapped.code).toBe('DB_CONNECTION_TIMEOUT');
        expect(mapped.userMessage).toBe('Database connection timed out. Please try again.');
    });
});
```

### Test Recovery Patterns (Rule 158)

```typescript
describe('Recovery Patterns', () => {
    it('should retry failed operations with backoff', async () => {
        let attempts = 0;
        const operation = jest.fn().mockImplementation(() => {
            attempts++;
            if (attempts < 3) {
                throw new Error('Temporary failure');
            }
            return 'success';
        });

        const result = await retryOperation(operation, 3, 100);

        expect(result).toBe('success');
        expect(attempts).toBe(3);
    });
});
```

## Resources

- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Error Handling Best Practices](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Control_flow_and_error_handling)
- [Async/Await Patterns](https://javascript.info/async-await)
- [Testing Async Code](https://jestjs.io/docs/asynchronous)

## Getting Help

- Check existing error handling patterns in the codebase
- Review the central error handler implementation
- Ask team members for code review
- Use the constitution validator to check compliance
