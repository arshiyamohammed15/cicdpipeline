/**
 * Diagnostics Provider Tests for Detection Engine Core Module (PM-4)
 * 
 * Tests diagnostics provider per PRD §3.8
 * Coverage: 100% of diagnostics functionality
 */

import { DetectionEngineDiagnosticsProvider } from '../providers/diagnostics';
import { ReceiptStorageReader } from '../../../shared/storage/ReceiptStorageReader';
import { DecisionReceipt } from '../../../shared/receipt-parser/ReceiptParser';
import * as vscode from 'vscode';

// Mock vscode
jest.mock('vscode', () => ({
    Diagnostic: jest.fn().mockImplementation((range, message, severity) => ({
        range,
        message,
        severity
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
    Location: jest.fn(),
    DiagnosticRelatedInformation: jest.fn(),
    Uri: {
        parse: jest.fn((uri) => ({ fsPath: uri }))
    },
    workspace: {
        workspaceFolders: [
            {
                name: 'test-repo',
                uri: {
                    fsPath: '/test/repo'
                }
            }
        ],
        getConfiguration: jest.fn(() => ({
            get: jest.fn(() => undefined)
        }))
    }
}));

// Mock ReceiptStorageReader
jest.mock('../../../shared/storage/ReceiptStorageReader', () => {
    return {
        ReceiptStorageReader: jest.fn().mockImplementation(() => ({
            readReceipts: jest.fn()
        }))
    };
});

describe('Detection Engine Diagnostics Provider', () => {
    let provider: DetectionEngineDiagnosticsProvider;
    let mockReceiptReader: jest.Mocked<ReceiptStorageReader>;

    beforeEach(() => {
        jest.clearAllMocks();
        provider = new DetectionEngineDiagnosticsProvider();
        mockReceiptReader = new ReceiptStorageReader() as jest.Mocked<ReceiptStorageReader>;
    });

    describe('initialize', () => {
        it('should initialize without error', async () => {
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await expect(provider.initialize(deps)).resolves.not.toThrow();
        });

        it('should create ReceiptStorageReader if not provided', async () => {
            const deps = {
                context: {} as any
            };
            await expect(provider.initialize(deps)).resolves.not.toThrow();
        });
    });

    describe('computeDiagnostics', () => {
        it('should return empty array when no receipts', async () => {
            (mockReceiptReader.readReceipts as jest.Mock).mockResolvedValue([]);
            
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
            
            const diagnostics = await provider.computeDiagnostics();
            expect(diagnostics).toEqual([]);
        });

        it('should create diagnostic for warn status', async () => {
            const mockReceipt: DecisionReceipt = {
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

            (mockReceiptReader.readReceipts as jest.Mock).mockResolvedValue([mockReceipt]);
            
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
            
            const diagnostics = await provider.computeDiagnostics();
            expect(diagnostics.length).toBeGreaterThan(0);
            expect(diagnostics[0].message).toContain('Warning detected');
        });

        it('should create diagnostic for soft_block status', async () => {
            const mockReceipt: DecisionReceipt = {
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

            (mockReceiptReader.readReceipts as jest.Mock).mockResolvedValue([mockReceipt]);
            
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
            
            const diagnostics = await provider.computeDiagnostics();
            expect(diagnostics.length).toBeGreaterThan(0);
            expect(diagnostics[0].severity).toBe(vscode.DiagnosticSeverity.Warning);
        });

        it('should create diagnostic for hard_block status', async () => {
            const mockReceipt: DecisionReceipt = {
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

            (mockReceiptReader.readReceipts as jest.Mock).mockResolvedValue([mockReceipt]);
            
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
            
            const diagnostics = await provider.computeDiagnostics();
            expect(diagnostics.length).toBeGreaterThan(0);
            expect(diagnostics[0].severity).toBe(vscode.DiagnosticSeverity.Error);
        });

        it('should not create diagnostic for pass status', async () => {
            const mockReceipt: DecisionReceipt = {
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

            (mockReceiptReader.readReceipts as jest.Mock).mockResolvedValue([mockReceipt]);
            
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
            
            const diagnostics = await provider.computeDiagnostics();
            expect(diagnostics.length).toBe(0);
        });

        it('should handle errors gracefully', async () => {
            (mockReceiptReader.readReceipts as jest.Mock).mockRejectedValue(new Error('Test error'));
            
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
            
            const diagnostics = await provider.computeDiagnostics();
            expect(diagnostics.length).toBeGreaterThan(0);
            expect(diagnostics[0].message).toContain('Error');
        });
    });
});
