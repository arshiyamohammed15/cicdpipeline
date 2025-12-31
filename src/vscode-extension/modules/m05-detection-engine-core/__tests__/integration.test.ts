/**
 * Integration Tests for Detection Engine Core Module (PM-4)
 * 
 * Tests end-to-end workflows per PRD §3.8, §3.9
 * Coverage: Critical integration paths
 */

import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as crypto from 'crypto';
import * as vscode from 'vscode';
import { registerModule } from '../index';
import { registerCommands, resetReceiptReader } from '../commands';
import { DetectionEngineStatusPillProvider } from '../providers/status-pill';
import { DetectionEngineDiagnosticsProvider } from '../providers/diagnostics';
import { DecisionCardSectionProvider } from '../views/decision-card-sections/DecisionCardSectionProvider';
import { ReceiptStorageReader } from '../../../shared/storage/ReceiptStorageReader';
import { ReceiptStorageService } from '../../../../edge-agent/shared/storage/ReceiptStorageService';
import { ReceiptGenerator } from '../../../../edge-agent/shared/storage/ReceiptGenerator';
import { DecisionReceipt } from '../../../shared/receipt-parser/ReceiptParser';

// Mock vscode
jest.mock('vscode', () => ({
    commands: {
        executeCommand: jest.fn(),
        registerCommand: jest.fn()
    },
    window: {
        showInformationMessage: jest.fn(),
        showErrorMessage: jest.fn(),
        createWebviewPanel: jest.fn(() => ({
            webview: {
                postMessage: jest.fn()
            },
            reveal: jest.fn(),
            dispose: jest.fn()
        }))
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
    },
    ExtensionContext: jest.fn(),
    DiagnosticSeverity: {
        Error: 0,
        Warning: 1,
        Information: 2,
        Hint: 3
    },
    Range: jest.fn((startLine, startChar, endLine, endChar) => ({
        start: { line: startLine, character: startChar },
        end: { line: endLine, character: endChar }
    })),
    Diagnostic: jest.fn((range, message, severity) => ({
        range,
        message,
        severity
    })),
    Location: jest.fn(),
    DiagnosticRelatedInformation: jest.fn(),
    Uri: {
        parse: jest.fn((uri) => ({ fsPath: uri }))
    }
}));

describe('Detection Engine Core Integration Tests', () => {
    let zuRoot: string;
    let workspaceRoot: string;
    let repoId: string;
    let mockContext: vscode.ExtensionContext;
    let receiptReader: ReceiptStorageReader;
    let receiptService: ReceiptStorageService;
    let receiptGenerator: ReceiptGenerator;
    let privatePem: string;
    let publicPem: string;
    let keyId: string;

    beforeAll(() => {
        // Generate key pair for signing receipts
        const { privateKey, publicKey } = crypto.generateKeyPairSync('ed25519');
        privatePem = privateKey.export({ format: 'pem', type: 'pkcs8' }).toString();
        publicPem = publicKey.export({ format: 'pem', type: 'spki' }).toString();
        keyId = 'test-integration-kid';
    });

    beforeEach(() => {
        resetReceiptReader();
        // Create temporary directories
        zuRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'zeroui-m05-integration-zu-'));
        workspaceRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'zeroui-m05-integration-ws-'));
        repoId = 'test-repo';
        process.env.ZU_ROOT = zuRoot;
        (vscode.Diagnostic as jest.Mock).mockImplementation((range, message, severity) => ({
            range,
            message,
            severity
        }));
        (vscode.Range as jest.Mock).mockImplementation((startLine, startChar, endLine, endChar) => ({
            start: { line: startLine, character: startChar },
            end: { line: endLine, character: endChar }
        }));
        (vscode.Location as jest.Mock).mockImplementation((uri, range) => ({
            uri,
            range
        }));
        (vscode.DiagnosticRelatedInformation as jest.Mock).mockImplementation((location, message) => ({
            location,
            message
        }));
        (vscode.Uri.parse as jest.Mock).mockImplementation((uri) => ({ fsPath: uri }));

        // Set up trust store with public key
        const trustStoreDir = path.join(zuRoot, 'product', 'policy', 'trust', 'pubkeys');
        fs.mkdirSync(trustStoreDir, { recursive: true });
        fs.writeFileSync(path.join(trustStoreDir, keyId), publicPem);

        // Initialize receipt services
        receiptReader = new ReceiptStorageReader(zuRoot);
        receiptService = new ReceiptStorageService(zuRoot, { verificationKey: publicPem });
        receiptGenerator = new ReceiptGenerator({ privateKey: privatePem, keyId });

        // Mock extension context
        mockContext = {
            subscriptions: []
        } as any;
    });

    afterEach(() => {
        for (const subscription of mockContext.subscriptions) {
            if (subscription && typeof subscription.dispose === 'function') {
                subscription.dispose();
            }
        }
        delete process.env.ZU_ROOT;
        if (fs.existsSync(zuRoot)) {
            fs.rmSync(zuRoot, { recursive: true, force: true });
        }
        if (fs.existsSync(workspaceRoot)) {
            fs.rmSync(workspaceRoot, { recursive: true, force: true });
        }
        jest.clearAllMocks();
    });

    const createTestReceipt = (overrides: Partial<DecisionReceipt> = {}): DecisionReceipt => {
        const receipt = receiptGenerator.generateDecisionReceipt(
            overrides.gate_id || 'detection-engine-core',
            overrides.policy_version_ids || ['POL-INIT'],
            overrides.snapshot_hash || 'sha256:' + '0'.repeat(64),
            overrides.inputs || {
                risk_score: 0.1,
                file_count: 5
            },
            overrides.decision || {
                status: 'pass',
                rationale: 'No significant risks detected',
                badges: ['has-tests']
            },
            overrides.evidence_handles || [],
            overrides.actor || {
                repo_id: repoId
            },
            overrides.degraded !== undefined ? overrides.degraded : false,
            overrides.evaluation_point || 'pre-commit',
            overrides.context,
            overrides.override,
            overrides.data_category,
            overrides.timestamp_utc ? { utc: overrides.timestamp_utc } : undefined
        );
        
        // Apply any remaining overrides that aren't handled by generateDecisionReceipt
        if (overrides.receipt_id) {
            receipt.receipt_id = overrides.receipt_id;
            // Re-sign with new receipt_id
            return receiptGenerator.generateDecisionReceipt(
                receipt.gate_id,
                receipt.policy_version_ids,
                receipt.snapshot_hash,
                receipt.inputs,
                receipt.decision,
                receipt.evidence_handles,
                receipt.actor,
                receipt.degraded,
                receipt.evaluation_point,
                (receipt as any).context,
                (receipt as any).override,
                (receipt as any).data_category,
                { utc: receipt.timestamp_utc, monotonicMs: receipt.timestamp_monotonic_ms }
            );
        }
        
        return receipt;
    };

    const writeReceiptToStorage = async (receipt: DecisionReceipt): Promise<void> => {
        await receiptService.storeDecisionReceipt(receipt, repoId);
    };

    describe('Module Registration Integration', () => {
        it('should register module with correct ID', () => {
            const deps = {
                context: mockContext,
                receiptReader
            };
            const module = registerModule(mockContext, deps);
            expect(module.id).toBe('m05');
            expect(module.title).toBe('Detection Engine Core');
        });

        it('should register all commands', () => {
            const deps = {
                context: mockContext,
                receiptReader
            };
            const module = registerModule(mockContext, deps);
            const commands = module.commands();
            expect(commands.length).toBe(2);
            expect(commands[0].id).toBe('zeroui.m05.showDecisionCard');
            expect(commands[1].id).toBe('zeroui.m05.viewReceipt');
        });

        it('should provide status pill provider', () => {
            const deps = {
                context: mockContext,
                receiptReader
            };
            const module = registerModule(mockContext, deps);
            expect(module.statusPill).toBeDefined();
        });

        it('should provide diagnostics provider', () => {
            const deps = {
                context: mockContext,
                receiptReader
            };
            const module = registerModule(mockContext, deps);
            expect(module.problems).toBeDefined();
        });

        it('should provide decision card sections', () => {
            const deps = {
                context: mockContext,
                receiptReader
            };
            const module = registerModule(mockContext, deps);
            expect(module.decisionCard).toBeDefined();
            const sections = module.decisionCard?.() || [];
            expect(sections.length).toBeGreaterThan(0);
        });
    });

    describe('Command Execution Integration', () => {
        it('should execute showDecisionCard command with receipt', async () => {
            const receipt = createTestReceipt();
            await writeReceiptToStorage(receipt);

            registerCommands(mockContext);
            const calls = (vscode.commands.registerCommand as jest.Mock).mock.calls;
            const showDecisionCardCall = calls.find((call: any[]) => call[0] === 'zeroui.m05.showDecisionCard');
            const handler = showDecisionCardCall[1];

            await handler();

            expect(vscode.window.showInformationMessage).not.toHaveBeenCalledWith(
                'No decision receipts found for Detection Engine Core'
            );
        });

        it('should execute viewReceipt command with receipt', async () => {
            const receipt = createTestReceipt();
            await writeReceiptToStorage(receipt);

            registerCommands(mockContext);
            const calls = (vscode.commands.registerCommand as jest.Mock).mock.calls;
            const viewReceiptCall = calls.find((call: any[]) => call[0] === 'zeroui.m05.viewReceipt');
            const handler = viewReceiptCall[1];

            await handler();

            expect(vscode.window.showInformationMessage).not.toHaveBeenCalledWith(
                'No decision receipts found for Detection Engine Core'
            );
        });
    });

    describe('Status Pill Provider Integration', () => {
        it('should display status from receipt', async () => {
            const receipt = createTestReceipt({
                decision: {
                    status: 'warn',
                    rationale: 'Warning detected',
                    badges: []
                }
            });
            await writeReceiptToStorage(receipt);

            const provider = new DetectionEngineStatusPillProvider();
            await provider.initialize({
                context: mockContext,
                receiptReader
            });

            // getText() calls updateStatus() which reads receipts
            const text = await provider.getText();
            // Should show warn status
            expect(text).toBe('⚠ Detection');
        });

        it('should update status when receipt changes', async () => {
            const receipt1 = createTestReceipt({
                decision: {
                    status: 'pass',
                    rationale: 'All good',
                    badges: []
                }
            });
            await writeReceiptToStorage(receipt1);

            const provider = new DetectionEngineStatusPillProvider();
            await provider.initialize({
                context: mockContext,
                receiptReader
            });

            const text1 = await provider.getText();
            expect(text1).toBe('✓ Detection');

            // Create a new receipt with different status
            const receipt2 = createTestReceipt({
                decision: {
                    status: 'hard_block',
                    rationale: 'Blocked',
                    badges: []
                }
            });
            await writeReceiptToStorage(receipt2);

            // getText() calls updateStatus() which should read the new receipt
            const text2 = await provider.getText();
            expect(text2).not.toBe(text1);
            expect(text2).toBe('✗ Detection (Blocked)');
        });
    });

    describe('Diagnostics Provider Integration', () => {
        it('should create diagnostics from warn receipts', async () => {
            const receipt = createTestReceipt({
                decision: {
                    status: 'warn',
                    rationale: 'Warning detected',
                    badges: []
                }
            });
            await writeReceiptToStorage(receipt);

            const provider = new DetectionEngineDiagnosticsProvider();
            await provider.initialize({
                context: mockContext,
                receiptReader
            });

            // computeDiagnostics reads receipts and creates diagnostics
            // Note: initialize() already calls computeDiagnostics(), so we call it again to ensure we get the latest
            const diagnostics = await provider.computeDiagnostics();
            expect(diagnostics.length).toBeGreaterThanOrEqual(1);
            const warnDiagnostic = diagnostics.find(d => d.message && typeof d.message === 'string' && d.message.includes('Warning detected'));
            expect(warnDiagnostic).toBeDefined();
            if (warnDiagnostic) {
                expect(warnDiagnostic.severity).toBe(vscode.DiagnosticSeverity.Information);
            }
        });

        it('should create error diagnostics from hard_block receipts', async () => {
            const receipt = createTestReceipt({
                decision: {
                    status: 'hard_block',
                    rationale: 'Hard block detected',
                    badges: []
                }
            });
            await writeReceiptToStorage(receipt);

            const provider = new DetectionEngineDiagnosticsProvider();
            await provider.initialize({
                context: mockContext,
                receiptReader
            });

            const diagnostics = await provider.computeDiagnostics();
            expect(diagnostics.length).toBeGreaterThanOrEqual(1);
            const errorDiagnostic = diagnostics.find(d => d.message && typeof d.message === 'string' && d.message.includes('Hard block detected'));
            expect(errorDiagnostic).toBeDefined();
            if (errorDiagnostic) {
                expect(errorDiagnostic.severity).toBe(vscode.DiagnosticSeverity.Error);
            }
        });

        it('should not create diagnostics from pass receipts', async () => {
            const receipt = createTestReceipt({
                decision: {
                    status: 'pass',
                    rationale: 'All good',
                    badges: []
                }
            });
            await writeReceiptToStorage(receipt);

            const provider = new DetectionEngineDiagnosticsProvider();
            await provider.initialize({
                context: mockContext,
                receiptReader
            });

            const diagnostics = await provider.computeDiagnostics();
            expect(diagnostics.length).toBe(0);
        });
    });

    describe('Decision Card Provider Integration', () => {
        it('should render overview section with receipt data', async () => {
            const receipt = createTestReceipt({
                decision: {
                    status: 'warn',
                    rationale: 'Warning detected',
                    badges: ['has-tests']
                }
            });
            await writeReceiptToStorage(receipt);

            const provider = new DecisionCardSectionProvider();
            await provider.initialize({
                context: mockContext,
                receiptReader
            });

            const mockWebview = {
                postMessage: jest.fn()
            } as any;
            const mockPanel = {
                webview: mockWebview,
                reveal: jest.fn(),
                dispose: jest.fn()
            } as any;

            await provider.renderOverview(mockWebview, mockPanel);

            expect(mockWebview.postMessage).toHaveBeenCalled();
            const message = mockWebview.postMessage.mock.calls[0][0];
            expect(message.type).toBe('render-section');
            expect(message.moduleId).toBe('m05');
        });

        it('should list evidence items from receipt', async () => {
            const receipt = createTestReceipt({
                evidence_handles: [
                    {
                        url: 'https://example.com/evidence1',
                        type: 'artifact',
                        description: 'Test evidence 1'
                    },
                    {
                        url: 'https://example.com/evidence2',
                        type: 'log',
                        description: 'Test evidence 2'
                    }
                ]
            });
            await writeReceiptToStorage(receipt);

            const provider = new DecisionCardSectionProvider();
            await provider.initialize({
                context: mockContext,
                receiptReader
            });

            const items = await provider.listEvidenceItems();
            expect(items.length).toBe(2);
            expect(items[0].label).toBe('Test evidence 1');
            expect(items[1].label).toBe('Test evidence 2');
        });
    });

    describe('Receipt Storage Integration', () => {
        it('should read receipts written by service', async () => {
            const receipt = createTestReceipt();
            await writeReceiptToStorage(receipt);

            const now = new Date();
            const year = now.getFullYear();
            const month = now.getMonth() + 1;
            const receipts = await receiptReader.readReceipts(repoId, year, month);

            expect(receipts.length).toBeGreaterThan(0);
            const foundReceipt = receipts.find(r => 
                'receipt_id' in r && (r as DecisionReceipt).receipt_id === receipt.receipt_id
            );
            expect(foundReceipt).toBeDefined();
        });

        it('should filter detection engine receipts correctly', async () => {
            const detectionReceipt = createTestReceipt({
                gate_id: 'detection-engine-core'
            });
            const otherReceipt = createTestReceipt({
                receipt_id: crypto.randomUUID(),
                gate_id: 'other-gate'
            });

            await writeReceiptToStorage(detectionReceipt);
            await writeReceiptToStorage(otherReceipt);

            const now = new Date();
            const year = now.getFullYear();
            const month = now.getMonth() + 1;
            const receipts = await receiptReader.readReceipts(repoId, year, month);

            const detectionReceipts = receipts.filter(r => 
                'gate_id' in r && (r as DecisionReceipt).gate_id === 'detection-engine-core'
            );
            expect(detectionReceipts.length).toBeGreaterThan(0);
        });
    });

    describe('End-to-End Workflow Integration', () => {
        it('should complete full workflow: receipt generation -> storage -> retrieval -> display', async () => {
            // 1. Create receipt
            const receipt = createTestReceipt({
                decision: {
                    status: 'warn',
                    rationale: 'End-to-end test',
                    badges: []
                }
            });

            // 2. Write to storage
            await writeReceiptToStorage(receipt);

            // 3. Initialize providers
            const statusProvider = new DetectionEngineStatusPillProvider();
            await statusProvider.initialize({
                context: mockContext,
                receiptReader
            });

            const diagnosticsProvider = new DetectionEngineDiagnosticsProvider();
            await diagnosticsProvider.initialize({
                context: mockContext,
                receiptReader
            });

            // 4. Verify status pill shows receipt
            const statusText = await statusProvider.getText();
            expect(statusText).toBeTruthy();

            // 5. Verify diagnostics created
            const diagnostics = await diagnosticsProvider.computeDiagnostics();
            expect(diagnostics.length).toBeGreaterThan(0);

            // 6. Verify command can retrieve receipt
            registerCommands(mockContext);
            const calls = (vscode.commands.registerCommand as jest.Mock).mock.calls;
            const showDecisionCardCall = calls.find((call: any[]) => call[0] === 'zeroui.m05.showDecisionCard');
            const handler = showDecisionCardCall[1];

            await handler();

            expect(vscode.window.showInformationMessage).not.toHaveBeenCalledWith(
                'No decision receipts found for Detection Engine Core'
            );
        });
    });

    describe('Error Handling Integration', () => {
        it('should handle missing receipts gracefully', async () => {
            const provider = new DetectionEngineStatusPillProvider();
            await provider.initialize({
                context: mockContext,
                receiptReader
            });

            const text = await provider.getText();
            expect(text).toBeTruthy(); // Should return default text, not throw
        });

        it('should handle storage errors gracefully', async () => {
            // Use invalid zuRoot to cause storage errors
            const invalidReader = new ReceiptStorageReader('/invalid/path');

            const provider = new DetectionEngineStatusPillProvider();
            await provider.initialize({
                context: mockContext,
                receiptReader: invalidReader
            });

            const text = await provider.getText();
            expect(text).toBeTruthy(); // Should handle error gracefully
        });
    });
});
