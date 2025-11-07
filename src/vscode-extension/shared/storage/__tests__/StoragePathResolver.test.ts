/**
 * StoragePathResolver Test Suite (VS Code Extension)
 * 
 * Tests for VS Code Extension StoragePathResolver
 * Validates ZU_ROOT resolution from environment variable and VS Code configuration
 */

import { StoragePathResolver } from '../StoragePathResolver';
import * as os from 'os';

// Mock vscode module - create manual mock
const mockGet = jest.fn();
const mockGetConfiguration = jest.fn(() => ({
    get: mockGet
}));

jest.mock('vscode', () => {
    // Create mock inside factory to avoid hoisting issues
    const mockGetConfig = jest.fn(() => ({
        get: jest.fn()
    }));
    return {
        workspace: {
            getConfiguration: mockGetConfig
        }
    };
}, { virtual: true });

// Get the mock after jest.mock has run
const vscode = require('vscode');
const actualMockGetConfiguration = vscode.workspace.getConfiguration;

describe('StoragePathResolver (VS Code Extension)', () => {
    const originalEnv = process.env.ZU_ROOT;
    const testZuRoot = os.tmpdir() + '/zeroui-test';

    beforeEach(() => {
        process.env.ZU_ROOT = testZuRoot;
        mockGet.mockReturnValue(undefined);
        actualMockGetConfiguration.mockReturnValue({
            get: mockGet
        });
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

        it('should use VS Code configuration if environment variable not set', () => {
            delete process.env.ZU_ROOT;
            const configZuRoot = '/config/zeroui';
            mockGet.mockReturnValue(configZuRoot);
            actualMockGetConfiguration.mockReturnValue({
                get: mockGet
            });

            const resolver = new StoragePathResolver();
            expect(resolver.getZuRoot()).toBe(configZuRoot);
        });

        it('should prioritize provided parameter over environment variable', () => {
            const customRoot = '/custom/path';
            const resolver = new StoragePathResolver(customRoot);
            expect(resolver.getZuRoot()).toBe(customRoot);
        });

        it('should throw error if ZU_ROOT is not set anywhere', () => {
            delete process.env.ZU_ROOT;
            mockGet.mockReturnValue('');
            actualMockGetConfiguration.mockReturnValue({
                get: mockGet
            });

            expect(() => new StoragePathResolver()).toThrow('ZU_ROOT environment variable or zeroui.zuRoot configuration is required');
        });
    });

    describe('Receipt Path Resolution', () => {
        let resolver: StoragePathResolver;

        beforeEach(() => {
            resolver = new StoragePathResolver(testZuRoot);
        });

        it('should resolve receipt path with YYYY/MM partitioning', () => {
            const result = resolver.resolveReceiptPath('my-repo', 2025, 10);
            expect(result).toContain('/ide/receipts/my-repo/2025/10');
        });

        it('should validate kebab-case repo-id', () => {
            expect(() => resolver.resolveReceiptPath('Invalid_Repo', 2025, 10)).toThrow('Must be kebab-case');
        });

        it('should validate year range', () => {
            expect(() => resolver.resolveReceiptPath('my-repo', 1999, 10)).toThrow('Invalid year');
            expect(() => resolver.resolveReceiptPath('my-repo', 10000, 10)).toThrow('Invalid year');
        });

        it('should validate month range', () => {
            expect(() => resolver.resolveReceiptPath('my-repo', 2025, 0)).toThrow('Invalid month');
            expect(() => resolver.resolveReceiptPath('my-repo', 2025, 13)).toThrow('Invalid month');
        });
    });

    describe('Path Normalization', () => {
        it('should normalize Windows paths', () => {
            if (os.platform() === 'win32') {
                const resolver = new StoragePathResolver('D:\\Test\\ZeroUI');
                expect(resolver.getZuRoot()).toBe('D:/Test/ZeroUI');
            }
        });

        it('should normalize multiple slashes', () => {
            const resolver = new StoragePathResolver(`${testZuRoot}//sub//path`);
            expect(resolver.getZuRoot()).not.toMatch(/\/{2,}/);
        });
    });
});

