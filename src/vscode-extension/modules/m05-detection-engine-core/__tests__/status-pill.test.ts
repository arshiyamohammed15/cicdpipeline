/**
 * Status Pill Provider Tests for Detection Engine Core Module (PM-4)
 * 
 * Tests status pill provider per PRD §3.8
 * Coverage: 100% of status pill functionality
 */

import type { ExtensionContext } from 'vscode';
import { DetectionEngineStatusPillProvider } from '../providers/status-pill';
import { ReceiptStorageReader } from '../../../shared/storage/ReceiptStorageReader';
import { DecisionReceipt } from '../../../shared/receipt-parser/ReceiptParser';

// Mock vscode
const mockGetConfiguration = jest.fn();
jest.mock('vscode', () => ({
    workspace: {
        workspaceFolders: [
            {
                name: 'test-repo',
                uri: {
                    fsPath: '/test/repo'
                }
            }
        ],
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

describe('Detection Engine Status Pill Provider', () => {
    let provider: DetectionEngineStatusPillProvider;
    let mockReceiptReader: jest.Mocked<ReceiptStorageReader>;
    let mockContext: ExtensionContext;

    beforeEach(() => {
        jest.clearAllMocks();
        mockGetConfiguration.mockReturnValue({
            get: jest.fn(() => undefined)
        });
        mockReadReceipts.mockReset();
        provider = new DetectionEngineStatusPillProvider();
        mockReceiptReader = {
            readReceipts: mockReadReceipts
        } as any;
        mockContext = {
            subscriptions: []
        } as unknown as ExtensionContext;
    });

    afterEach(() => {
        for (const subscription of mockContext.subscriptions) {
            subscription.dispose();
        }
    });

    describe('initialize', () => {
        it('should initialize without error', async () => {
            const deps = {
                context: mockContext,
                receiptReader: mockReceiptReader
            };
            await expect(provider.initialize(deps)).resolves.not.toThrow();
        });

        it('should create ReceiptStorageReader if not provided', async () => {
            mockReadReceipts.mockResolvedValue([]);
            const deps = {
                context: mockContext
            };
            await expect(provider.initialize(deps)).resolves.not.toThrow();
        });
    });

    describe('getText', () => {
        it('should return text for pass status', async () => {
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
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([mockReceipt]);
            
            const deps = {
                context: mockContext,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
            
            const text = await provider.getText();
            expect(text).toContain('Detection');
        });

        it('should return text for warn status', async () => {
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
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([mockReceipt]);
            
            const deps = {
                context: mockContext,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
            
            const text = await provider.getText();
            expect(text).toContain('⚠');
        });

        it('should return text for hard_block status', async () => {
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
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            const deps = {
                context: mockContext,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
            
            // Clear the mock to avoid interference from initialize's updateStatus call
            mockReadReceipts.mockClear();
            mockReadReceipts.mockResolvedValue([mockReceipt]);
            
            const text = await provider.getText();
            expect(text).toContain('Blocked');
        });

        it('should return default text when no receipts', async () => {
            mockReadReceipts.mockResolvedValue([]);
            
            const deps = {
                context: mockContext,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
            
            const text = await provider.getText();
            expect(text).toBeTruthy();
        });

        it('should handle errors gracefully', async () => {
            mockReadReceipts.mockRejectedValue(new Error('Test error'));
            
            const deps = {
                context: mockContext,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
            
            const text = await provider.getText();
            expect(text).toContain('⚠');
        });
    });

    describe('getTooltip', () => {
        it('should return tooltip with rationale', async () => {
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
                    rationale: 'Test rationale',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            const deps = {
                context: mockContext,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
            
            // Clear the mock to avoid interference from initialize's updateStatus call
            mockReadReceipts.mockClear();
            mockReadReceipts.mockResolvedValue([mockReceipt]);
            
            const tooltip = await provider.getTooltip();
            expect(tooltip).toContain('Test rationale');
        });

        it('should return default tooltip when no receipts', async () => {
            mockReadReceipts.mockResolvedValue([]);
            
            const deps = {
                context: mockContext,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
            
            const tooltip = await provider.getTooltip();
            expect(tooltip).toBeTruthy();
        });
    });
});
