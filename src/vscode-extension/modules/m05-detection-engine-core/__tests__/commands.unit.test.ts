/**
 * Unit Tests for Detection Engine Core Commands
 * 
 * Tests command registration and handlers per PRD §3.8
 * Coverage: 100% of commands.ts
 */

import * as vscode from 'vscode';
import { registerCommands } from '../commands';
import { ReceiptStorageReader } from '../../../shared/storage/ReceiptStorageReader';
import { DecisionCardManager } from '../../../ui/decision-card/DecisionCardManager';
import { ReceiptViewerManager } from '../../../ui/receipt-viewer/ReceiptViewerManager';

// Mock vscode
const mockExecuteCommand = jest.fn();
const mockRegisterCommand = jest.fn();
const mockShowInformationMessage = jest.fn();
const mockShowErrorMessage = jest.fn();
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
    commands: {
        executeCommand: (...args: any[]) => mockExecuteCommand(...args),
        registerCommand: (...args: any[]) => mockRegisterCommand(...args)
    },
    window: {
        showInformationMessage: (...args: any[]) => mockShowInformationMessage(...args),
        showErrorMessage: (...args: any[]) => mockShowErrorMessage(...args)
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
const mockShowReceipt = jest.fn();
jest.mock('../../../ui/receipt-viewer/ReceiptViewerManager', () => {
    return {
        ReceiptViewerManager: jest.fn().mockImplementation(() => ({
            showReceipt: mockShowReceipt
        }))
    };
});

describe('Detection Engine Core Commands - Unit Tests', () => {
    let mockContext: vscode.ExtensionContext;

    beforeEach(() => {
        jest.clearAllMocks();
        mockContext = {
            subscriptions: []
        } as any;
        
        mockGetConfiguration.mockReturnValue({
            get: jest.fn(() => undefined)
        });
        process.env.ZU_ROOT = undefined;
    });

    afterEach(() => {
        delete process.env.ZU_ROOT;
    });

    describe('registerCommands', () => {
        it('should register commands without error', () => {
            expect(() => registerCommands(mockContext)).not.toThrow();
        });

        it('should register showDecisionCard command', () => {
            registerCommands(mockContext);
            expect(mockRegisterCommand).toHaveBeenCalledWith(
                'zeroui.m05.showDecisionCard',
                expect.any(Function)
            );
        });

        it('should register viewReceipt command', () => {
            registerCommands(mockContext);
            expect(mockRegisterCommand).toHaveBeenCalledWith(
                'zeroui.m05.viewReceipt',
                expect.any(Function)
            );
        });

        it('should add commands to context subscriptions', () => {
            registerCommands(mockContext);
            expect(mockContext.subscriptions.length).toBe(2);
        });
    });

    describe('getReceiptReader', () => {
        it('should create ReceiptStorageReader with undefined zuRoot when not configured', () => {
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.showDecisionCard')[1];
            
            // Trigger handler to test getReceiptReader
            void handler();
            
            expect(ReceiptStorageReader).toHaveBeenCalledWith(undefined);
        });

        it('should create ReceiptStorageReader with zuRoot from config', () => {
            mockGetConfiguration.mockReturnValue({
                get: jest.fn((key: string) => {
                    if (key === 'zuRoot') return '/custom/zu/root';
                    return undefined;
                })
            });
            
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.showDecisionCard')[1];
            
            void handler();
            
            expect(ReceiptStorageReader).toHaveBeenCalledWith('/custom/zu/root');
        });

        it('should create ReceiptStorageReader with zuRoot from environment', () => {
            process.env.ZU_ROOT = '/env/zu/root';
            
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.showDecisionCard')[1];
            
            void handler();
            
            expect(ReceiptStorageReader).toHaveBeenCalledWith('/env/zu/root');
        });

        it('should reuse ReceiptStorageReader instance on subsequent calls', () => {
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler1 = calls.find((c: any[]) => c[0] === 'zeroui.m05.showDecisionCard')[1];
            const handler2 = calls.find((c: any[]) => c[0] === 'zeroui.m05.viewReceipt')[1];
            
            jest.clearAllMocks();
            void handler1();
            void handler2();
            
            // Should only create one instance (cached)
            expect(ReceiptStorageReader).toHaveBeenCalledTimes(1);
        });
    });

    describe('getWorkspaceRepoId', () => {
        it('should return default-repo when no workspace folder', () => {
            const originalFolders = mockWorkspaceFolders;
            (vscode.workspace as any).workspaceFolders = undefined;
            
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.showDecisionCard')[1];
            
            mockReadReceipts.mockResolvedValue([]);
            void handler();
            
            expect(mockReadReceipts).toHaveBeenCalledWith('default-repo', expect.any(Number), expect.any(Number));
            
            (vscode.workspace as any).workspaceFolders = originalFolders;
        });

        it('should convert workspace folder name to kebab-case', () => {
            (vscode.workspace as any).workspaceFolders = [
                {
                    name: 'My Test Repo',
                    uri: { fsPath: '/test' }
                }
            ];
            
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.showDecisionCard')[1];
            
            mockReadReceipts.mockResolvedValue([]);
            void handler();
            
            expect(mockReadReceipts).toHaveBeenCalledWith('my-test-repo', expect.any(Number), expect.any(Number));
        });

        it('should handle special characters in workspace folder name', () => {
            (vscode.workspace as any).workspaceFolders = [
                {
                    name: 'My_Test.Repo@123',
                    uri: { fsPath: '/test' }
                }
            ];
            
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.showDecisionCard')[1];
            
            mockReadReceipts.mockResolvedValue([]);
            void handler();
            
            expect(mockReadReceipts).toHaveBeenCalledWith('my-test-repo123', expect.any(Number), expect.any(Number));
        });
    });

    describe('showDecisionCard command handler', () => {
        it('should read receipts for current year and month', async () => {
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.showDecisionCard')[1];
            
            const now = new Date();
            const year = now.getFullYear();
            const month = now.getMonth() + 1;
            
            mockReadReceipts.mockResolvedValue([]);
            await handler();
            
            expect(mockReadReceipts).toHaveBeenCalledWith('test-repo', year, month);
        });

        it('should filter detection engine receipts by gate_id', async () => {
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.showDecisionCard')[1];
            
            const receipts = [
                {
                    gate_id: 'detection-engine-core',
                    evaluation_point: 'pre-commit',
                    timestamp_utc: '2025-01-01T00:00:00Z',
                    decision: { status: 'pass', rationale: 'Test' }
                },
                {
                    gate_id: 'other-gate',
                    evaluation_point: 'pre-commit',
                    timestamp_utc: '2025-01-01T00:00:00Z'
                }
            ];
            
            mockReadReceipts.mockResolvedValue(receipts);
            await handler();
            
            expect(mockShowDecisionCard).toHaveBeenCalled();
            const callArgs = mockShowDecisionCard.mock.calls[0][0];
            expect(callArgs.moduleId).toBe('m05');
        });

        it('should filter detection engine receipts by m05 in gate_id', async () => {
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.showDecisionCard')[1];
            
            const receipts = [
                {
                    gate_id: 'm05-detection',
                    evaluation_point: 'pre-commit',
                    timestamp_utc: '2025-01-01T00:00:00Z',
                    decision: { status: 'pass', rationale: 'Test' }
                }
            ];
            
            mockReadReceipts.mockResolvedValue(receipts);
            await handler();
            
            expect(mockShowDecisionCard).toHaveBeenCalled();
        });

        it('should sort receipts by timestamp descending', async () => {
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.showDecisionCard')[1];
            
            const receipts = [
                {
                    gate_id: 'detection-engine-core',
                    evaluation_point: 'pre-commit',
                    timestamp_utc: '2025-01-01T00:00:00Z',
                    decision: { status: 'pass', rationale: 'Old' }
                },
                {
                    gate_id: 'detection-engine-core',
                    evaluation_point: 'pre-commit',
                    timestamp_utc: '2025-01-02T00:00:00Z',
                    decision: { status: 'warn', rationale: 'New' }
                }
            ];
            
            mockReadReceipts.mockResolvedValue(receipts);
            await handler();
            
            expect(mockShowDecisionCard).toHaveBeenCalled();
            const callArgs = mockShowDecisionCard.mock.calls[0][0];
            expect(callArgs.rationale).toBe('New');
        });

        it('should handle receipt without decision object', async () => {
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.showDecisionCard')[1];
            
            const receipts = [
                {
                    gate_id: 'detection-engine-core',
                    evaluation_point: 'pre-commit',
                    timestamp_utc: '2025-01-01T00:00:00Z'
                }
            ];
            
            mockReadReceipts.mockResolvedValue(receipts);
            await handler();
            
            expect(mockShowDecisionCard).toHaveBeenCalled();
            const callArgs = mockShowDecisionCard.mock.calls[0][0];
            expect(callArgs.status).toBe('pass');
            expect(callArgs.rationale).toBe('No decision data available');
        });

        it('should handle receipt without evidence_handles', async () => {
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.showDecisionCard')[1];
            
            const receipts = [
                {
                    gate_id: 'detection-engine-core',
                    evaluation_point: 'pre-commit',
                    timestamp_utc: '2025-01-01T00:00:00Z',
                    decision: { status: 'pass', rationale: 'Test' }
                }
            ];
            
            mockReadReceipts.mockResolvedValue(receipts);
            await handler();
            
            expect(mockShowDecisionCard).toHaveBeenCalled();
            const callArgs = mockShowDecisionCard.mock.calls[0][0];
            expect(callArgs.evidenceHandles).toEqual([]);
        });

        it('should show message when no receipts found', async () => {
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.showDecisionCard')[1];
            
            mockReadReceipts.mockResolvedValue([]);
            await handler();
            
            expect(mockShowInformationMessage).toHaveBeenCalledWith(
                'No decision receipts found for Detection Engine Core'
            );
            expect(mockShowDecisionCard).not.toHaveBeenCalled();
        });

        it('should handle error when reading receipts fails', async () => {
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.showDecisionCard')[1];
            
            const error = new Error('Read error');
            mockReadReceipts.mockRejectedValue(error);
            await handler();
            
            expect(mockShowErrorMessage).toHaveBeenCalledWith('Failed to show decision card: Read error');
        });

        it('should handle non-Error exception', async () => {
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.showDecisionCard')[1];
            
            mockReadReceipts.mockRejectedValue('String error');
            await handler();
            
            expect(mockShowErrorMessage).toHaveBeenCalledWith('Failed to show decision card: Unknown error');
        });
    });

    describe('viewReceipt command handler', () => {
        it('should read receipts for current year and month', async () => {
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.viewReceipt')[1];
            
            const now = new Date();
            const year = now.getFullYear();
            const month = now.getMonth() + 1;
            
            mockReadReceipts.mockResolvedValue([]);
            await handler();
            
            expect(mockReadReceipts).toHaveBeenCalledWith('test-repo', year, month);
        });

        it('should filter and show latest detection engine receipt', async () => {
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.viewReceipt')[1];
            
            const receipts = [
                {
                    gate_id: 'detection-engine-core',
                    evaluation_point: 'pre-commit',
                    timestamp_utc: '2025-01-01T00:00:00Z'
                }
            ];
            
            mockReadReceipts.mockResolvedValue(receipts);
            await handler();
            
            expect(mockShowReceipt).toHaveBeenCalledWith(receipts[0]);
        });

        it('should show message when no receipts found', async () => {
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.viewReceipt')[1];
            
            mockReadReceipts.mockResolvedValue([]);
            await handler();
            
            expect(mockShowInformationMessage).toHaveBeenCalledWith(
                'No decision receipts found for Detection Engine Core'
            );
            expect(mockShowReceipt).not.toHaveBeenCalled();
        });

        it('should handle error when reading receipts fails', async () => {
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.viewReceipt')[1];
            
            const error = new Error('Read error');
            mockReadReceipts.mockRejectedValue(error);
            await handler();
            
            expect(mockShowErrorMessage).toHaveBeenCalledWith('Failed to view receipt: Read error');
        });

        it('should handle non-Error exception', async () => {
            registerCommands(mockContext);
            const calls = mockRegisterCommand.mock.calls;
            const handler = calls.find((c: any[]) => c[0] === 'zeroui.m05.viewReceipt')[1];
            
            mockReadReceipts.mockRejectedValue('String error');
            await handler();
            
            expect(mockShowErrorMessage).toHaveBeenCalledWith('Failed to view receipt: Unknown error');
        });
    });
});

