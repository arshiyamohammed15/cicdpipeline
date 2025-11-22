/**
 * Unit Tests for Detection Engine Core Status Pill Provider
 * 
 * Tests status pill provider per PRD §3.8
 * Coverage: 100% of status-pill.ts
 */

import * as vscode from 'vscode';
import { DetectionEngineStatusPillProvider, getStatusPillText, getStatusPillTooltip } from '../providers/status-pill';
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

describe('Detection Engine Status Pill Provider - Unit Tests', () => {
    let provider: DetectionEngineStatusPillProvider;
    let mockReceiptReader: jest.Mocked<ReceiptStorageReader>;

    beforeEach(() => {
        jest.clearAllMocks();
        jest.useFakeTimers();
        provider = new DetectionEngineStatusPillProvider();
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

        it('should create ReceiptStorageReader with zuRoot from config', async () => {
            mockGetConfiguration.mockReturnValue({
                get: jest.fn((key: string) => {
                    if (key === 'zuRoot') return '/config/zu/root';
                    return undefined;
                })
            });
            
            const deps = {
                context: {} as any
            };
            
            mockReadReceipts.mockResolvedValue([]);
            await provider.initialize(deps);
            
            expect(ReceiptStorageReader).toHaveBeenCalledWith('/config/zu/root');
        });

        it('should create ReceiptStorageReader with zuRoot from environment', async () => {
            process.env.ZU_ROOT = '/env/zu/root';
            
            const deps = {
                context: {} as any
            };
            
            mockReadReceipts.mockResolvedValue([]);
            await provider.initialize(deps);
            
            expect(ReceiptStorageReader).toHaveBeenCalledWith('/env/zu/root');
        });

        it('should call updateStatus on initialization', async () => {
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            
            mockReadReceipts.mockResolvedValue([]);
            await provider.initialize(deps);
            
            expect(mockReadReceipts).toHaveBeenCalled();
        });

        it('should set up periodic updates every 30 seconds', async () => {
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            
            mockReadReceipts.mockResolvedValue([]);
            await provider.initialize(deps);
            
            jest.clearAllMocks();
            jest.advanceTimersByTime(30000);
            
            // Should call updateStatus again after 30 seconds
            expect(mockReadReceipts).toHaveBeenCalled();
        });
    });

    describe('updateStatus', () => {
        beforeEach(async () => {
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
        });

        it('should update status from receipt with pass', async () => {
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
            await (provider as any).updateStatus();
            
            const text = await provider.getText();
            expect(text).toBe('✓ Detection');
        });

        it('should update status from receipt with warn', async () => {
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
                    rationale: 'Warning',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            await (provider as any).updateStatus();
            
            const text = await provider.getText();
            expect(text).toBe('⚠ Detection');
        });

        it('should update status from receipt with soft_block', async () => {
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
                    rationale: 'Soft block',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            await (provider as any).updateStatus();
            
            const text = await provider.getText();
            expect(text).toBe('⚠ Detection (Soft)');
        });

        it('should update status from receipt with hard_block', async () => {
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
                    rationale: 'Hard block',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            await (provider as any).updateStatus();
            
            const text = await provider.getText();
            expect(text).toBe('✗ Detection (Blocked)');
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
                    status: 'pass',
                    rationale: '',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            await (provider as any).updateStatus();
            
            const tooltip = await provider.getTooltip();
            expect(tooltip).toContain('No rationale');
        });

        it('should set default status when no receipts', async () => {
            mockReadReceipts.mockResolvedValue([]);
            await (provider as any).updateStatus();
            
            const text = await provider.getText();
            expect(text).toBe('✓ Detection');
        });

        it('should set default status when receipt has no decision', async () => {
            const receipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                evaluation_point: 'pre-commit',
                timestamp_utc: '2025-01-01T00:00:00Z'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            await (provider as any).updateStatus();
            
            const text = await provider.getText();
            expect(text).toBe('✓ Detection');
        });

        it('should handle error and set warn status', async () => {
            mockReadReceipts.mockRejectedValue(new Error('Test error'));
            await (provider as any).updateStatus();
            
            const text = await provider.getText();
            expect(text).toContain('⚠');
        });

        it('should handle non-Error exception', async () => {
            mockReadReceipts.mockRejectedValue('String error');
            await (provider as any).updateStatus();
            
            const tooltip = await provider.getTooltip();
            expect(tooltip).toContain('Unknown error');
        });

        it('should return early if receiptReader is not set', async () => {
            const newProvider = new DetectionEngineStatusPillProvider();
            await (newProvider as any).updateStatus();
            
            // Should not throw, just return early
            const text = await newProvider.getText();
            expect(text).toBeTruthy();
        });
    });

    describe('isDetectionEngineReceipt', () => {
        beforeEach(async () => {
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
        });

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

        it('should return false for non-detection engine receipt', () => {
            const receipt = {
                gate_id: 'other-gate',
                evaluation_point: 'pre-commit',
                policy_version_ids: ['POL-OTHER']
            };
            expect((provider as any).isDetectionEngineReceipt(receipt)).toBe(false);
        });

        it('should return false for null receipt', () => {
            expect((provider as any).isDetectionEngineReceipt(null)).toBe(false);
        });

        it('should return false for non-object receipt', () => {
            expect((provider as any).isDetectionEngineReceipt('string')).toBe(false);
        });

        it('should return false for receipt without evaluation_point', () => {
            const receipt = {
                gate_id: 'detection-engine-core'
            };
            expect((provider as any).isDetectionEngineReceipt(receipt)).toBe(false);
        });

        it('should return false for receipt without gate_id', () => {
            const receipt = {
                evaluation_point: 'pre-commit'
            };
            expect((provider as any).isDetectionEngineReceipt(receipt)).toBe(false);
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

        it('should handle special characters', () => {
            (vscode.workspace as any).workspaceFolders = [
                {
                    name: 'Repo@123_Test',
                    uri: { fsPath: '/test' }
                }
            ];
            
            const repoId = (provider as any).getWorkspaceRepoId();
            expect(repoId).toBe('repo123-test');
        });
    });

    describe('getText', () => {
        beforeEach(async () => {
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
        });

        it('should return text for pass status', async () => {
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
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const text = await provider.getText();
            expect(text).toBe('✓ Detection');
        });

        it('should return text for warn status', async () => {
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
            const text = await provider.getText();
            expect(text).toBe('⚠ Detection');
        });

        it('should return text for soft_block status', async () => {
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
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const text = await provider.getText();
            expect(text).toBe('⚠ Detection (Soft)');
        });

        it('should return text for hard_block status', async () => {
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
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const text = await provider.getText();
            expect(text).toBe('✗ Detection (Blocked)');
        });

        it('should return default text for unknown status', async () => {
            const receipt: any = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'unknown',
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const text = await provider.getText();
            expect(text).toBe('— Detection');
        });
    });

    describe('getTooltip', () => {
        beforeEach(async () => {
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
        });

        it('should return tooltip with status and rationale', async () => {
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
                    rationale: 'Test rationale',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const tooltip = await provider.getTooltip();
            expect(tooltip).toContain('warn');
            expect(tooltip).toContain('Test rationale');
        });

        it('should return default tooltip when no receipts', async () => {
            mockReadReceipts.mockResolvedValue([]);
            const tooltip = await provider.getTooltip();
            expect(tooltip).toContain('No recent decisions');
        });
    });

    describe('Legacy exports', () => {
        it('should export getStatusPillText function', () => {
            expect(typeof getStatusPillText).toBe('function');
            expect(getStatusPillText()).toBe('—');
        });

        it('should export getStatusPillTooltip function', () => {
            expect(typeof getStatusPillTooltip).toBe('function');
            expect(getStatusPillTooltip()).toBe('No data yet (skeleton)');
        });
    });
});

