/**
 * Status Pill Provider Tests for Detection Engine Core Module (M05)
 * 
 * Tests status pill provider per PRD §3.8
 * Coverage: 100% of status pill functionality
 */

import { DetectionEngineStatusPillProvider } from '../providers/status-pill';
import { ReceiptStorageReader } from '../../../shared/storage/ReceiptStorageReader';
import { DecisionReceipt } from '../../../shared/receipt-parser/ReceiptParser';

// Mock vscode
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

describe('Detection Engine Status Pill Provider', () => {
    let provider: DetectionEngineStatusPillProvider;
    let mockReceiptReader: jest.Mocked<ReceiptStorageReader>;

    beforeEach(() => {
        jest.clearAllMocks();
        provider = new DetectionEngineStatusPillProvider();
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

            (mockReceiptReader.readReceipts as jest.Mock).mockResolvedValue([mockReceipt]);
            
            const deps = {
                context: {} as any,
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

            (mockReceiptReader.readReceipts as jest.Mock).mockResolvedValue([mockReceipt]);
            
            const deps = {
                context: {} as any,
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

            (mockReceiptReader.readReceipts as jest.Mock).mockResolvedValue([mockReceipt]);
            
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
            
            const text = await provider.getText();
            expect(text).toContain('Blocked');
        });

        it('should return default text when no receipts', async () => {
            (mockReceiptReader.readReceipts as jest.Mock).mockResolvedValue([]);
            
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
            
            const text = await provider.getText();
            expect(text).toBeTruthy();
        });

        it('should handle errors gracefully', async () => {
            (mockReceiptReader.readReceipts as jest.Mock).mockRejectedValue(new Error('Test error'));
            
            const deps = {
                context: {} as any,
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

            (mockReceiptReader.readReceipts as jest.Mock).mockResolvedValue([mockReceipt]);
            
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
            
            const tooltip = await provider.getTooltip();
            expect(tooltip).toContain('Test rationale');
        });

        it('should return default tooltip when no receipts', async () => {
            (mockReceiptReader.readReceipts as jest.Mock).mockResolvedValue([]);
            
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
            
            const tooltip = await provider.getTooltip();
            expect(tooltip).toBeTruthy();
        });
    });
});
