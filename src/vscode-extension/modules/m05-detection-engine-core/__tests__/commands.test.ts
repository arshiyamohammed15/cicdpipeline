/**
 * Commands Tests for Detection Engine Core Module (PM-4)
 * 
 * Tests command handlers per PRD §3.8
 * Coverage: 100% of command handlers
 */

import * as vscode from 'vscode';
import { registerCommands } from '../commands';
import { ReceiptStorageReader } from '../../../shared/storage/ReceiptStorageReader';
import { DecisionReceipt } from '../../../shared/receipt-parser/ReceiptParser';

// Mock vscode
jest.mock('vscode', () => ({
    commands: {
        executeCommand: jest.fn(),
        registerCommand: jest.fn()
    },
    window: {
        showInformationMessage: jest.fn(),
        showErrorMessage: jest.fn()
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
    },
    env: {
        openExternal: jest.fn()
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

// Mock DecisionCardManager
jest.mock('../../../ui/decision-card/DecisionCardManager', () => {
    return {
        DecisionCardManager: jest.fn().mockImplementation(() => ({
            showDecisionCard: jest.fn()
        }))
    };
});

// Mock ReceiptViewerManager
jest.mock('../../../ui/receipt-viewer/ReceiptViewerManager', () => {
    return {
        ReceiptViewerManager: jest.fn().mockImplementation(() => ({
            showReceiptViewer: jest.fn()
        }))
    };
});

describe('Detection Engine Core Commands', () => {
    let mockContext: vscode.ExtensionContext;
    let mockReceiptReader: jest.Mocked<ReceiptStorageReader>;

    beforeEach(() => {
        jest.clearAllMocks();
        
        mockContext = {
            subscriptions: []
        } as any;

        mockReceiptReader = new ReceiptStorageReader() as jest.Mocked<ReceiptStorageReader>;
    });

    describe('registerCommands', () => {
        it('should register commands without error', () => {
            expect(() => registerCommands(mockContext)).not.toThrow();
            expect(vscode.commands.registerCommand).toHaveBeenCalled();
        });

        it('should register showDecisionCard command', () => {
            registerCommands(mockContext);
            const calls = (vscode.commands.registerCommand as jest.Mock).mock.calls;
            const showDecisionCardCall = calls.find((call: any[]) => call[0] === 'zeroui.m05.showDecisionCard');
            expect(showDecisionCardCall).toBeDefined();
        });

        it('should register viewReceipt command', () => {
            registerCommands(mockContext);
            const calls = (vscode.commands.registerCommand as jest.Mock).mock.calls;
            const viewReceiptCall = calls.find((call: any[]) => call[0] === 'zeroui.m05.viewReceipt');
            expect(viewReceiptCall).toBeDefined();
        });

        it('should add commands to context subscriptions', () => {
            registerCommands(mockContext);
            expect(mockContext.subscriptions.length).toBeGreaterThan(0);
        });
    });

    describe('showDecisionCard command handler', () => {
        it('should handle command execution successfully', async () => {
            const mockReceipt: DecisionReceipt = {
                receipt_id: 'test-receipt-id',
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
                actor: {
                    repo_id: 'test-repo'
                },
                degraded: false,
                signature: 'test-signature'
            };

            (mockReceiptReader.readReceipts as jest.Mock).mockResolvedValue([mockReceipt]);

            registerCommands(mockContext);
            const calls = (vscode.commands.registerCommand as jest.Mock).mock.calls;
            const showDecisionCardCall = calls.find((call: any[]) => call[0] === 'zeroui.m05.showDecisionCard');
            const handler = showDecisionCardCall[1];

            await handler();

            expect(mockReceiptReader.readReceipts).toHaveBeenCalled();
        });

        it('should handle error when reading receipts fails', async () => {
            const error = new Error('Read error');
            (mockReceiptReader.readReceipts as jest.Mock).mockRejectedValue(error);

            registerCommands(mockContext);
            const calls = (vscode.commands.registerCommand as jest.Mock).mock.calls;
            const showDecisionCardCall = calls.find((call: any[]) => call[0] === 'zeroui.m05.showDecisionCard');
            const handler = showDecisionCardCall[1];

            await handler();

            expect(vscode.window.showErrorMessage).toHaveBeenCalled();
        });

        it('should show message when no receipts found', async () => {
            (mockReceiptReader.readReceipts as jest.Mock).mockResolvedValue([]);

            registerCommands(mockContext);
            const calls = (vscode.commands.registerCommand as jest.Mock).mock.calls;
            const showDecisionCardCall = calls.find((call: any[]) => call[0] === 'zeroui.m05.showDecisionCard');
            const handler = showDecisionCardCall[1];

            await handler();

            expect(vscode.window.showInformationMessage).toHaveBeenCalledWith(
                'No decision receipts found for Detection Engine Core'
            );
        });
    });

    describe('viewReceipt command handler', () => {
        it('should handle command execution successfully', async () => {
            const mockReceipt: DecisionReceipt = {
                receipt_id: 'test-receipt-id',
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
                actor: {
                    repo_id: 'test-repo'
                },
                degraded: false,
                signature: 'test-signature'
            };

            (mockReceiptReader.readReceipts as jest.Mock).mockResolvedValue([mockReceipt]);

            registerCommands(mockContext);
            const calls = (vscode.commands.registerCommand as jest.Mock).mock.calls;
            const viewReceiptCall = calls.find((call: any[]) => call[0] === 'zeroui.m05.viewReceipt');
            const handler = viewReceiptCall[1];

            await handler();

            expect(mockReceiptReader.readReceipts).toHaveBeenCalled();
        });

        it('should handle error when reading receipts fails', async () => {
            const error = new Error('Read error');
            (mockReceiptReader.readReceipts as jest.Mock).mockRejectedValue(error);

            registerCommands(mockContext);
            const calls = (vscode.commands.registerCommand as jest.Mock).mock.calls;
            const viewReceiptCall = calls.find((call: any[]) => call[0] === 'zeroui.m05.viewReceipt');
            const handler = viewReceiptCall[1];

            await handler();

            expect(vscode.window.showErrorMessage).toHaveBeenCalled();
        });

        it('should show message when no receipts found', async () => {
            (mockReceiptReader.readReceipts as jest.Mock).mockResolvedValue([]);

            registerCommands(mockContext);
            const calls = (vscode.commands.registerCommand as jest.Mock).mock.calls;
            const viewReceiptCall = calls.find((call: any[]) => call[0] === 'zeroui.m05.viewReceipt');
            const handler = viewReceiptCall[1];

            await handler();

            expect(vscode.window.showInformationMessage).toHaveBeenCalledWith(
                'No decision receipts found for Detection Engine Core'
            );
        });
    });
});
