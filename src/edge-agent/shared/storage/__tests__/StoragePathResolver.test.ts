/**
 * StoragePathResolver Test Suite
 *
 * Tests for Edge Agent StoragePathResolver
 * Validates ZU_ROOT path resolution, kebab-case validation, and storage plane paths
 */

import { StoragePathResolver } from '../StoragePathResolver';
import * as path from 'path';
import * as os from 'os';

describe('StoragePathResolver (Edge Agent)', () => {
    const originalEnv = process.env.ZU_ROOT;
    const testZuRoot = os.platform() === 'win32' ? 'D:\\Test\\ZeroUI' : '/tmp/zeroui';

    beforeEach(() => {
        process.env.ZU_ROOT = testZuRoot;
    });

    afterEach(() => {
        if (originalEnv) {
            process.env.ZU_ROOT = originalEnv;
        } else {
            delete process.env.ZU_ROOT;
        }
    });

    describe('Constructor', () => {
        it('should initialize with ZU_ROOT from environment variable', () => {
            const resolver = new StoragePathResolver();
            expect(resolver.getZuRoot()).toBe(testZuRoot.replace(/\\/g, '/'));
        });

        it('should initialize with provided ZU_ROOT parameter', () => {
            const customRoot = os.platform() === 'win32' ? 'C:\\Custom\\Path' : '/custom/path';
            const resolver = new StoragePathResolver(customRoot);
            expect(resolver.getZuRoot()).toBe(customRoot.replace(/\\/g, '/'));
        });

        it('should throw error if ZU_ROOT is not set', () => {
            delete process.env.ZU_ROOT;
            expect(() => new StoragePathResolver()).toThrow('ZU_ROOT environment variable is required');
        });

        it('should normalize Windows paths to forward slashes', () => {
            const windowsPath = 'D:\\Test\\ZeroUI';
            const resolver = new StoragePathResolver(windowsPath);
            expect(resolver.getZuRoot()).toBe('D:/Test/ZeroUI');
        });

        it('should normalize Unix paths correctly', () => {
            const unixPath = '/tmp/zeroui';
            const resolver = new StoragePathResolver(unixPath);
            expect(resolver.getZuRoot()).toBe('/tmp/zeroui');
        });
    });

    describe('Plane Path Resolution', () => {
        let resolver: StoragePathResolver;

        beforeEach(() => {
            resolver = new StoragePathResolver(testZuRoot);
        });

        it('should resolve IDE plane path', () => {
            const result = resolver.resolveIdePath('receipts/repo-id/2025/10/');
            // normalizePath removes trailing slashes
            expect(result).toBe(`${testZuRoot.replace(/\\/g, '/')}/ide/receipts/repo-id/2025/10`);
        });

        it('should resolve Tenant plane path', () => {
            const result = resolver.resolveTenantPath('evidence/data/');
            expect(result).toBe(`${testZuRoot.replace(/\\/g, '/')}/tenant/evidence/data`);
        });

        it('should resolve Product plane path', () => {
            const result = resolver.resolveProductPath('policy/registry/');
            expect(result).toBe(`${testZuRoot.replace(/\\/g, '/')}/product/policy/registry`);
        });

        it('should resolve Shared plane path', () => {
            const result = resolver.resolveSharedPath('pki/');
            expect(result).toBe(`${testZuRoot.replace(/\\/g, '/')}/shared/pki`);
        });

        it('should handle paths with leading/trailing slashes', () => {
            const result1 = resolver.resolveIdePath('/receipts/repo/');
            const result2 = resolver.resolveIdePath('receipts/repo');
            expect(result1).toBe(result2);
        });
    });

    describe('Kebab-Case Validation (Rule 216)', () => {
        let resolver: StoragePathResolver;

        beforeEach(() => {
            resolver = new StoragePathResolver(testZuRoot);
        });

        it('should accept valid kebab-case repo-id', () => {
            expect(() => resolver.resolveReceiptPath('my-repo-123', 2025, 10)).not.toThrow();
        });

        it('should reject repo-id with uppercase letters', () => {
            expect(() => resolver.resolveReceiptPath('My-Repo', 2025, 10)).toThrow('Must be kebab-case');
        });

        it('should reject repo-id with underscores', () => {
            expect(() => resolver.resolveReceiptPath('my_repo', 2025, 10)).toThrow('Must be kebab-case');
        });

        it('should reject repo-id with spaces', () => {
            expect(() => resolver.resolveReceiptPath('my repo', 2025, 10)).toThrow('Must be kebab-case');
        });

        it('should reject repo-id with special characters', () => {
            expect(() => resolver.resolveReceiptPath('my@repo', 2025, 10)).toThrow('Must be kebab-case');
        });

        it('should accept repo-id with numbers', () => {
            expect(() => resolver.resolveReceiptPath('repo-123-456', 2025, 10)).not.toThrow();
        });

        it('should reject invalid plane names', () => {
            // This tests internal validation - we can't directly test it, but we can test path resolution
            expect(() => resolver.resolveIdePath('Invalid/Path')).toThrow('Must be kebab-case');
        });
    });

    describe('Receipt Path Resolution (Rule 228)', () => {
        let resolver: StoragePathResolver;

        beforeEach(() => {
            resolver = new StoragePathResolver(testZuRoot);
        });

        it('should resolve receipt path with YYYY/MM partitioning', () => {
            const result = resolver.resolveReceiptPath('my-repo', 2025, 10);
            expect(result).toBe(`${testZuRoot.replace(/\\/g, '/')}/ide/receipts/my-repo/2025/10`);
        });

        it('should pad month to 2 digits', () => {
            const result = resolver.resolveReceiptPath('my-repo', 2025, 1);
            expect(result).toContain('/2025/01');
        });

        it('should handle month 12', () => {
            const result = resolver.resolveReceiptPath('my-repo', 2025, 12);
            expect(result).toContain('/2025/12');
        });

        it('should reject year less than 2000', () => {
            expect(() => resolver.resolveReceiptPath('my-repo', 1999, 10)).toThrow('Invalid year');
        });

        it('should reject year greater than 9999', () => {
            expect(() => resolver.resolveReceiptPath('my-repo', 10000, 10)).toThrow('Invalid year');
        });

        it('should accept year 2000', () => {
            expect(() => resolver.resolveReceiptPath('my-repo', 2000, 10)).not.toThrow();
        });

        it('should accept year 9999', () => {
            expect(() => resolver.resolveReceiptPath('my-repo', 9999, 10)).not.toThrow();
        });

        it('should reject month less than 1', () => {
            expect(() => resolver.resolveReceiptPath('my-repo', 2025, 0)).toThrow('Invalid month');
        });

        it('should reject month greater than 12', () => {
            expect(() => resolver.resolveReceiptPath('my-repo', 2025, 13)).toThrow('Invalid month');
        });

        it('should accept month 1', () => {
            expect(() => resolver.resolveReceiptPath('my-repo', 2025, 1)).not.toThrow();
        });

        it('should accept month 12', () => {
            expect(() => resolver.resolveReceiptPath('my-repo', 2025, 12)).not.toThrow();
        });
    });

    describe('Policy Path Resolution', () => {
        let resolver: StoragePathResolver;

        beforeEach(() => {
            resolver = new StoragePathResolver(testZuRoot);
        });

        it('should resolve IDE policy cache path', () => {
            const result = resolver.resolvePolicyPath('ide', 'cache/');
            expect(result).toBe(`${testZuRoot.replace(/\\/g, '/')}/ide/policy/cache`);
        });

        it('should resolve IDE policy root path', () => {
            const result = resolver.resolvePolicyPath('ide', '');
            expect(result).toBe(`${testZuRoot.replace(/\\/g, '/')}/ide/policy`);
        });

        it('should resolve Product policy registry path', () => {
            const result = resolver.resolvePolicyPath('product', 'releases/');
            expect(result).toBe(`${testZuRoot.replace(/\\/g, '/')}/product/policy/registry/releases`);
        });

        it('should resolve Product policy registry root path', () => {
            const result = resolver.resolvePolicyPath('product', '');
            expect(result).toBe(`${testZuRoot.replace(/\\/g, '/')}/product/policy/registry`);
        });
    });

    describe('Path Normalization', () => {
        it('should normalize multiple slashes', () => {
            const resolver = new StoragePathResolver(`${testZuRoot}//sub//path`);
            expect(resolver.getZuRoot()).not.toMatch(/\/{2,}/);
        });

        it('should handle mixed separators on Windows', () => {
            if (os.platform() === 'win32') {
                const resolver = new StoragePathResolver('D:\\Test\\ZeroUI/alternate/path');
                const result = resolver.getZuRoot();
                expect(result).not.toContain('\\');
                expect(result).toContain('/');
            }
        });
    });
});
