/**
 * Commands Tests for Detection Engine Core Module (PM-4)
 * 
 * Tests command handlers per PRD §3.8
 * Coverage: 100% of command handlers
 */

import * as vscode from 'vscode';
import { registerCommands, resetReceiptReader } from '../commands';
import { ReceiptStorageReader } from '../../../shared/storage/ReceiptStorageReader';
import { DecisionCardManager } from '../../../ui/decision-card/DecisionCardManager';
import { ReceiptViewerManager } from '../../../ui/receipt-viewer/ReceiptViewerManager';
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
        getConfiguration: jest.fn((section?: string) => {
            const config = {
                get: jest.fn((key?: string) => {
                    return undefined;
                })
            };
            return config;
        })
    },
    env: {
        openExternal: jest.fn()
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

// Mock DecisionCardManager
const mockShowDecisionCard = jest.fn();
jest.mock('../../../ui/decision-card/DecisionCardManager', () => {
    return {
        DecisionCardManager: jest.fn().mockImplementation(() => ({
            showDecisionCard: mockShowDecisionCard
        }))
    };
});

// Mock ReceiptViewerManager
const mockShowReceiptViewer = jest.fn();
jest.mock('../../../ui/receipt-viewer/ReceiptViewerManager', () => {
    return {
        ReceiptViewerManager: jest.fn().mockImplementation(() => ({
            showReceiptViewer: mockShowReceiptViewer
        }))
    };
});

describe('Detection Engine Core Commands', () => {
    let mockContext: vscode.ExtensionContext;
    let mockReceiptReader: ReceiptStorageReader;

    beforeEach(() => {
        jest.clearAllMocks();
        mockReadReceipts.mockReset();
        resetReceiptReader();

        (ReceiptStorageReader as jest.Mock).mockImplementation(() => ({
            readReceipts: mockReadReceipts
        }));
        (DecisionCardManager as jest.Mock).mockImplementation(() => ({
            showDecisionCard: mockShowDecisionCard
        }));
        (ReceiptViewerManager as jest.Mock).mockImplementation(() => ({
            showReceiptViewer: mockShowReceiptViewer
        }));
        (vscode.workspace.getConfiguration as jest.Mock).mockImplementation(() => ({
            get: jest.fn(() => undefined)
        }));

        mockContext = {
            subscriptions: []
        } as any;

        mockReceiptReader = {
            readReceipts: mockReadReceipts,
            readReceiptsInRange: jest.fn(),
            readLatestReceipts: jest.fn()
        } as unknown as ReceiptStorageReader;
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

            jest.clearAllMocks();
            mockReadReceipts.mockResolvedValue([mockReceipt]);

            registerCommands(mockContext);
            const calls = (vscode.commands.registerCommand as jest.Mock).mock.calls;
            const showDecisionCardCall = calls.find((call: any[]) => call[0] === 'zeroui.m05.showDecisionCard');
            const handler = showDecisionCardCall[1];

            await handler();

            expect(mockReadReceipts).toHaveBeenCalled();
        });

        it('should handle error when reading receipts fails', async () => {
            const error = new Error('Read error');
            mockReadReceipts.mockRejectedValue(error);

            registerCommands(mockContext);
            const calls = (vscode.commands.registerCommand as jest.Mock).mock.calls;
            const showDecisionCardCall = calls.find((call: any[]) => call[0] === 'zeroui.m05.showDecisionCard');
            const handler = showDecisionCardCall[1];

            await handler();

            expect(vscode.window.showErrorMessage).toHaveBeenCalled();
        });

        it('should show message when no receipts found', async () => {
            jest.clearAllMocks();
            mockReadReceipts.mockResolvedValue([]);

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

            jest.clearAllMocks();
            mockReadReceipts.mockResolvedValue([mockReceipt]);

            registerCommands(mockContext);
            const calls = (vscode.commands.registerCommand as jest.Mock).mock.calls;
            const viewReceiptCall = calls.find((call: any[]) => call[0] === 'zeroui.m05.viewReceipt');
            const handler = viewReceiptCall[1];

            await handler();

            expect(mockReadReceipts).toHaveBeenCalled();
        });

        it('should handle error when reading receipts fails', async () => {
            const error = new Error('Read error');
            mockReadReceipts.mockRejectedValue(error);

            registerCommands(mockContext);
            const calls = (vscode.commands.registerCommand as jest.Mock).mock.calls;
            const viewReceiptCall = calls.find((call: any[]) => call[0] === 'zeroui.m05.viewReceipt');
            const handler = viewReceiptCall[1];

            await handler();

            expect(vscode.window.showErrorMessage).toHaveBeenCalled();
        });

        it('should show message when no receipts found', async () => {
            jest.clearAllMocks();
            mockReadReceipts.mockResolvedValue([]);

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
