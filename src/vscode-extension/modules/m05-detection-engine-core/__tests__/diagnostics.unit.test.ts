/**
 * Unit Tests for Detection Engine Core Diagnostics Provider
 * 
 * Tests diagnostics provider per PRD §3.8
 * Coverage: 100% of diagnostics.ts
 */

import * as vscode from 'vscode';
import { DetectionEngineDiagnosticsProvider, computeDiagnostics } from '../providers/diagnostics';
import { ReceiptStorageReader } from '../../../shared/storage/ReceiptStorageReader';
import { DecisionReceipt } from '../../../shared/receipt-parser/ReceiptParser';

// Mock vscode
const mockGetConfiguration = jest.fn();
const mockWorkspaceFolders = [
    {
        name: 'test-repo',
        uri: {
            fsPath: '/test/repo'
        }
    }
];

jest.mock('vscode', () => ({
    Diagnostic: jest.fn().mockImplementation((range, message, severity) => ({
        range,
        message,
        severity,
        source: undefined,
        code: undefined,
        relatedInformation: undefined
    })),
    DiagnosticSeverity: {
        Error: 0,
        Warning: 1,
        Information: 2,
        Hint: 3
    },
    Range: jest.fn().mockImplementation((startLine, startChar, endLine, endChar) => ({
        start: { line: startLine, character: startChar },
        end: { line: endLine, character: endChar }
    })),
    Location: jest.fn().mockImplementation((uri, range) => ({
        uri,
        range
    })),
    DiagnosticRelatedInformation: jest.fn().mockImplementation((location, message) => ({
        location,
        message
    })),
    Uri: {
        parse: jest.fn((uri) => ({ fsPath: uri }))
    },
    workspace: {
        get workspaceFolders() {
            return mockWorkspaceFolders;
        },
        getConfiguration: (...args: any[]) => mockGetConfiguration(...args)
    }
}));

// Mock ReceiptStorageReader
const mockReadReceipts = jest.fn();
jest.mock('../../../shared/storage/ReceiptStorageReader', () => {
    return {
        ReceiptStorageReader: jest.fn().mockImplementation(() => ({
            readReceipts: mockReadReceipts
        }))
    };
});

describe('Detection Engine Diagnostics Provider - Unit Tests', () => {
    let provider: DetectionEngineDiagnosticsProvider;
    let mockReceiptReader: jest.Mocked<ReceiptStorageReader>;

    beforeEach(() => {
        jest.clearAllMocks();
        jest.useFakeTimers();
        provider = new DetectionEngineDiagnosticsProvider();
        mockReceiptReader = new ReceiptStorageReader() as jest.Mocked<ReceiptStorageReader>;
        
        mockGetConfiguration.mockReturnValue({
            get: jest.fn(() => undefined)
        });
        process.env.ZU_ROOT = undefined;
    });

    afterEach(() => {
        jest.useRealTimers();
        delete process.env.ZU_ROOT;
    });

    describe('initialize', () => {
        it('should use provided receiptReader', async () => {
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            
            mockReadReceipts.mockResolvedValue([]);
            await provider.initialize(deps);
            
            expect(ReceiptStorageReader).not.toHaveBeenCalled();
        });

        it('should create ReceiptStorageReader when not provided', async () => {
            const deps = {
                context: {} as any
            };
            
            mockReadReceipts.mockResolvedValue([]);
            await provider.initialize(deps);
            
            expect(ReceiptStorageReader).toHaveBeenCalled();
        });

        it('should call computeDiagnostics on initialization', async () => {
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            
            mockReadReceipts.mockResolvedValue([]);
            await provider.initialize(deps);
            
            expect(mockReadReceipts).toHaveBeenCalled();
        });

        it('should set up periodic updates every 60 seconds', async () => {
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            
            mockReadReceipts.mockResolvedValue([]);
            await provider.initialize(deps);
            
            jest.clearAllMocks();
            jest.advanceTimersByTime(60000);
            
            expect(mockReadReceipts).toHaveBeenCalled();
        });
    });

    describe('getWorkspaceRepoId', () => {
        it('should return default-repo when no workspace folder', () => {
            const originalFolders = mockWorkspaceFolders;
            (vscode.workspace as any).workspaceFolders = undefined;
            
            const repoId = (provider as any).getWorkspaceRepoId();
            expect(repoId).toBe('default-repo');
            
            (vscode.workspace as any).workspaceFolders = originalFolders;
        });

        it('should convert workspace folder name to kebab-case', () => {
            (vscode.workspace as any).workspaceFolders = [
                {
                    name: 'My Test Repo',
                    uri: { fsPath: '/test' }
                }
            ];
            
            const repoId = (provider as any).getWorkspaceRepoId();
            expect(repoId).toBe('my-test-repo');
        });
    });

    describe('isDetectionEngineReceipt', () => {
        it('should return true for receipt with detection-engine in gate_id', () => {
            const receipt = {
                gate_id: 'detection-engine-core',
                evaluation_point: 'pre-commit'
            };
            expect((provider as any).isDetectionEngineReceipt(receipt)).toBe(true);
        });

        it('should return true for receipt with m05 in gate_id', () => {
            const receipt = {
                gate_id: 'm05-detection',
                evaluation_point: 'pre-commit'
            };
            expect((provider as any).isDetectionEngineReceipt(receipt)).toBe(true);
        });

        it('should return true for receipt with M05 in policy_version_ids', () => {
            const receipt = {
                gate_id: 'other-gate',
                evaluation_point: 'pre-commit',
                policy_version_ids: ['POL-M05-001']
            };
            expect((provider as any).isDetectionEngineReceipt(receipt)).toBe(true);
        });

        it('should return false for null receipt', () => {
            expect((provider as any).isDetectionEngineReceipt(null)).toBe(false);
        });

        it('should return false for non-object receipt', () => {
            expect((provider as any).isDetectionEngineReceipt('string')).toBe(false);
        });
    });

    describe('computeDiagnostics', () => {
        beforeEach(async () => {
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
        });

        it('should return empty array when no receipts', async () => {
            mockReadReceipts.mockResolvedValue([]);
            const diagnostics = await provider.computeDiagnostics();
            expect(diagnostics).toEqual([]);
        });

        it('should return empty array when receiptReader is not set', async () => {
            const newProvider = new DetectionEngineDiagnosticsProvider();
            const diagnostics = await newProvider.computeDiagnostics();
            expect(diagnostics).toEqual([]);
        });

        it('should create diagnostic for warn status', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'warn',
                    rationale: 'Warning detected',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const diagnostics = await provider.computeDiagnostics();
            
            expect(diagnostics.length).toBe(1);
            expect(diagnostics[0].severity).toBe(vscode.DiagnosticSeverity.Information);
            expect(diagnostics[0].message).toContain('Warning detected');
        });

        it('should create diagnostic for soft_block status', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'soft_block',
                    rationale: 'Soft block detected',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const diagnostics = await provider.computeDiagnostics();
            
            expect(diagnostics.length).toBe(1);
            expect(diagnostics[0].severity).toBe(vscode.DiagnosticSeverity.Warning);
        });

        it('should create diagnostic for hard_block status', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'hard_block',
                    rationale: 'Hard block detected',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const diagnostics = await provider.computeDiagnostics();
            
            expect(diagnostics.length).toBe(1);
            expect(diagnostics[0].severity).toBe(vscode.DiagnosticSeverity.Error);
        });

        it('should not create diagnostic for pass status', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'pass',
                    rationale: 'All good',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const diagnostics = await provider.computeDiagnostics();
            
            expect(diagnostics.length).toBe(0);
        });

        it('should set diagnostic source', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'warn',
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const diagnostics = await provider.computeDiagnostics();
            
            expect(diagnostics[0].source).toBe('Detection Engine Core (M05)');
        });

        it('should set diagnostic code', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'warn',
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const diagnostics = await provider.computeDiagnostics();
            
            expect(diagnostics[0].code).toBeDefined();
            expect(diagnostics[0].code?.value).toBe('M05-WARN');
        });

        it('should add related information for evaluation_point', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-merge',
                inputs: {},
                decision: {
                    status: 'warn',
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const diagnostics = await provider.computeDiagnostics();
            
            expect(diagnostics[0].relatedInformation).toBeDefined();
            expect(diagnostics[0].relatedInformation?.length).toBe(1);
        });

        it('should handle receipt without rationale', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'warn',
                    rationale: '',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const diagnostics = await provider.computeDiagnostics();
            
            expect(diagnostics[0].message).toContain('Detection issue detected');
        });

        it('should handle receipt without decision', async () => {
            const receipt: any = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                evaluation_point: 'pre-commit',
                timestamp_utc: '2025-01-01T00:00:00Z'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const diagnostics = await provider.computeDiagnostics();
            
            expect(diagnostics.length).toBe(0);
        });

        it('should handle error and create warning diagnostic', async () => {
            mockReadReceipts.mockRejectedValue(new Error('Test error'));
            const diagnostics = await provider.computeDiagnostics();
            
            expect(diagnostics.length).toBe(1);
            expect(diagnostics[0].severity).toBe(vscode.DiagnosticSeverity.Warning);
            expect(diagnostics[0].message).toContain('Error reading receipts');
        });

        it('should handle non-Error exception', async () => {
            mockReadReceipts.mockRejectedValue('String error');
            const diagnostics = await provider.computeDiagnostics();
            
            expect(diagnostics.length).toBe(1);
            expect(diagnostics[0].message).toContain('Unknown error');
        });

        it('should filter non-detection engine receipts', async () => {
            const receipts = [
                {
                    gate_id: 'detection-engine-core',
                    evaluation_point: 'pre-commit',
                    decision: { status: 'warn', rationale: 'Test', badges: [] }
                },
                {
                    gate_id: 'other-gate',
                    evaluation_point: 'pre-commit',
                    decision: { status: 'warn', rationale: 'Test', badges: [] }
                }
            ];

            mockReadReceipts.mockResolvedValue(receipts);
            const diagnostics = await provider.computeDiagnostics();
            
            expect(diagnostics.length).toBe(1);
        });
    });

    describe('Legacy export', () => {
        it('should export computeDiagnostics function', () => {
            expect(typeof computeDiagnostics).toBe('function');
            expect(computeDiagnostics()).toEqual([]);
        });
    });
});

