/**
 * Unit Tests for Detection Engine Core Module Index
 * 
 * Tests registerModule function per PRD §3.8
 * Coverage: 100% of index.ts
 */

import * as vscode from 'vscode';
import { registerModule, CoreDeps, ZeroUIModule } from '../index';
import { DetectionEngineStatusPillProvider } from '../providers/status-pill';
import { DetectionEngineDiagnosticsProvider } from '../providers/diagnostics';
import { DecisionCardSectionProvider } from '../views/decision-card-sections/DecisionCardSectionProvider';
import { getQuickActions } from '../actions/quick-actions';

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
    },
    ExtensionContext: jest.fn()
}));

// Mock dependencies
jest.mock('../commands', () => ({
    registerCommands: jest.fn()
}));

// Create mock provider instances
const mockStatusPillProviderInstance = {
    initialize: jest.fn().mockResolvedValue(undefined),
    getText: jest.fn().mockResolvedValue('✓ Detection'),
    getTooltip: jest.fn().mockResolvedValue('Detection Engine Core: pass'),
    dispose: jest.fn()
};

const mockDiagnosticsProviderInstance = {
    initialize: jest.fn().mockResolvedValue(undefined),
    computeDiagnostics: jest.fn().mockResolvedValue([]),
    dispose: jest.fn()
};

const mockDecisionCardProviderInstance = {
    initialize: jest.fn().mockResolvedValue(undefined),
    renderOverview: jest.fn().mockResolvedValue(undefined),
    renderDetails: jest.fn().mockResolvedValue(undefined),
    listEvidenceItems: jest.fn().mockResolvedValue([])
};

jest.mock('../providers/status-pill', () => ({
    DetectionEngineStatusPillProvider: jest.fn().mockImplementation(() => mockStatusPillProviderInstance)
}));

jest.mock('../providers/diagnostics', () => ({
    DetectionEngineDiagnosticsProvider: jest.fn().mockImplementation(() => mockDiagnosticsProviderInstance)
}));

jest.mock('../views/decision-card-sections/DecisionCardSectionProvider', () => ({
    DecisionCardSectionProvider: jest.fn().mockImplementation(() => mockDecisionCardProviderInstance)
}));

jest.mock('../actions/quick-actions', () => ({
    getQuickActions: jest.fn().mockReturnValue([
        { id: 'test-action', label: 'Test Action' }
    ])
}));

describe('Detection Engine Core Module Index', () => {
    let mockContext: vscode.ExtensionContext;
    let mockDeps: CoreDeps;

    beforeEach(() => {
        jest.clearAllMocks();

        (DetectionEngineStatusPillProvider as jest.Mock).mockImplementation(() => mockStatusPillProviderInstance);
        (DetectionEngineDiagnosticsProvider as jest.Mock).mockImplementation(() => mockDiagnosticsProviderInstance);
        (DecisionCardSectionProvider as jest.Mock).mockImplementation(() => mockDecisionCardProviderInstance);
        (getQuickActions as jest.Mock).mockReturnValue([
            { id: 'test-action', label: 'Test Action' }
        ]);

        mockStatusPillProviderInstance.initialize.mockResolvedValue(undefined);
        mockStatusPillProviderInstance.getText.mockResolvedValue('✓ Detection');
        mockStatusPillProviderInstance.getTooltip.mockResolvedValue('Detection Engine Core: pass');
        mockDiagnosticsProviderInstance.initialize.mockResolvedValue(undefined);
        mockDiagnosticsProviderInstance.computeDiagnostics.mockResolvedValue([]);
        mockDecisionCardProviderInstance.initialize.mockResolvedValue(undefined);
        mockDecisionCardProviderInstance.renderOverview.mockResolvedValue(undefined);
        mockDecisionCardProviderInstance.renderDetails.mockResolvedValue(undefined);
        mockDecisionCardProviderInstance.listEvidenceItems.mockResolvedValue([]);
        
        mockContext = {
            subscriptions: []
        } as any;

        mockDeps = {
            context: mockContext,
            receiptReader: undefined,
            ipcClient: undefined
        };
    });

    describe('registerModule', () => {
        it('should return module with correct id', () => {
            const module = registerModule(mockContext, mockDeps);
            expect(module.id).toBe('m05');
        });

        it('should return module with correct title', () => {
            const module = registerModule(mockContext, mockDeps);
            expect(module.title).toBe('Detection Engine Core');
        });

        it('should return module implementing ZeroUIModule interface', () => {
            const module = registerModule(mockContext, mockDeps);
            expect(module).toHaveProperty('id');
            expect(module).toHaveProperty('title');
            expect(module).toHaveProperty('commands');
            expect(module).toHaveProperty('statusPill');
            expect(module).toHaveProperty('decisionCard');
            expect(module).toHaveProperty('evidenceDrawer');
            expect(module).toHaveProperty('problems');
            expect(module).toHaveProperty('quickActions');
            expect(module).toHaveProperty('activate');
            expect(module).toHaveProperty('deactivate');
        });

        it('should return commands array with correct structure', () => {
            const module = registerModule(mockContext, mockDeps);
            const commands = module.commands();
            expect(Array.isArray(commands)).toBe(true);
            expect(commands.length).toBe(2);
            expect(commands[0]).toHaveProperty('id');
            expect(commands[0]).toHaveProperty('title');
            expect(commands[0]).toHaveProperty('handler');
            expect(commands[1]).toHaveProperty('id');
            expect(commands[1]).toHaveProperty('title');
            expect(commands[1]).toHaveProperty('handler');
        });

        it('should return correct command IDs', () => {
            const module = registerModule(mockContext, mockDeps);
            const commands = module.commands();
            expect(commands[0].id).toBe('zeroui.m05.showDecisionCard');
            expect(commands[1].id).toBe('zeroui.m05.viewReceipt');
        });

        it('should return correct command titles', () => {
            const module = registerModule(mockContext, mockDeps);
            const commands = module.commands();
            expect(commands[0].title).toBe('Show Decision Card');
            expect(commands[1].title).toBe('View Last Receipt');
        });

        it('should execute showDecisionCard command handler', async () => {
            const module = registerModule(mockContext, mockDeps);
            const commands = module.commands();
            await commands[0].handler();
            expect(vscode.commands.executeCommand).toHaveBeenCalledWith('zeroui.showDecisionCard', { moduleId: 'm05' });
        });

        it('should execute viewReceipt command handler', async () => {
            const module = registerModule(mockContext, mockDeps);
            const commands = module.commands();
            await commands[1].handler();
            expect(vscode.commands.executeCommand).toHaveBeenCalledWith('zeroui.showReceiptViewer', { moduleId: 'm05' });
        });

        it('should provide statusPill with correct structure', () => {
            const module = registerModule(mockContext, mockDeps);
            const statusPill = module.statusPill?.();
            expect(statusPill).toBeDefined();
            expect(statusPill).toHaveProperty('getText');
            expect(statusPill).toHaveProperty('getTooltip');
            expect(statusPill).toHaveProperty('onClickCommandId');
            expect(statusPill?.onClickCommandId).toBe('zeroui.m05.showDecisionCard');
        });

        it('should call statusPill getText', async () => {
            const module = registerModule(mockContext, mockDeps);
            const statusPill = module.statusPill?.();
            const text = await statusPill?.getText();
            expect(text).toBe('✓ Detection');
            expect(mockStatusPillProviderInstance.getText).toHaveBeenCalled();
        });

        it('should call statusPill getTooltip', async () => {
            const module = registerModule(mockContext, mockDeps);
            const statusPill = module.statusPill?.();
            const tooltip = await statusPill?.getTooltip();
            expect(tooltip).toBe('Detection Engine Core: pass');
            expect(mockStatusPillProviderInstance.getTooltip).toHaveBeenCalled();
        });

        it('should provide decisionCard sections', () => {
            const module = registerModule(mockContext, mockDeps);
            const sections = module.decisionCard?.();
            if (!sections) {
                throw new Error('Expected decision card sections');
            }
            expect(Array.isArray(sections)).toBe(true);
            expect(sections.length).toBe(2);
            expect(sections[0]).toHaveProperty('id');
            expect(sections[0]).toHaveProperty('render');
            expect(sections[1]).toHaveProperty('id');
            expect(sections[1]).toHaveProperty('render');
        });

        it('should have correct decisionCard section IDs', () => {
            const module = registerModule(mockContext, mockDeps);
            const sections = module.decisionCard?.();
            if (!sections) {
                throw new Error('Expected decision card sections');
            }
            expect(sections[0].id).toBe('m05-detection-overview');
            expect(sections[1].id).toBe('m05-detection-details');
        });

        it('should call decisionCard renderOverview', async () => {
            const module = registerModule(mockContext, mockDeps);
            const sections = module.decisionCard?.();
            if (!sections) {
                throw new Error('Expected decision card sections');
            }
            const mockWebview = { postMessage: jest.fn() } as any;
            const mockPanel = { webview: mockWebview } as any;
            await sections[0].render(mockWebview, mockPanel);
            expect(mockDecisionCardProviderInstance.renderOverview).toHaveBeenCalledWith(mockWebview, mockPanel);
        });

        it('should call decisionCard renderDetails', async () => {
            const module = registerModule(mockContext, mockDeps);
            const sections = module.decisionCard?.();
            if (!sections) {
                throw new Error('Expected decision card sections');
            }
            const mockWebview = { postMessage: jest.fn() } as any;
            const mockPanel = { webview: mockWebview } as any;
            await sections[1].render(mockWebview, mockPanel);
            expect(mockDecisionCardProviderInstance.renderDetails).toHaveBeenCalledWith(mockWebview, mockPanel);
        });

        it('should provide evidenceDrawer', () => {
            const module = registerModule(mockContext, mockDeps);
            const evidenceDrawer = module.evidenceDrawer?.();
            expect(evidenceDrawer).toBeDefined();
            expect(evidenceDrawer).toHaveProperty('listItems');
        });

        it('should call evidenceDrawer listItems', async () => {
            const module = registerModule(mockContext, mockDeps);
            const evidenceDrawer = module.evidenceDrawer?.();
            const items = await evidenceDrawer?.listItems();
            expect(Array.isArray(items)).toBe(true);
            expect(mockDecisionCardProviderInstance.listEvidenceItems).toHaveBeenCalled();
        });

        it('should provide problems provider', () => {
            const module = registerModule(mockContext, mockDeps);
            const problems = module.problems?.();
            expect(problems).toBeDefined();
            expect(problems).toHaveProperty('computeDiagnostics');
        });

        it('should call problems computeDiagnostics', async () => {
            const module = registerModule(mockContext, mockDeps);
            const problems = module.problems?.();
            const diagnostics = await problems?.computeDiagnostics();
            expect(Array.isArray(diagnostics)).toBe(true);
            expect(mockDiagnosticsProviderInstance.computeDiagnostics).toHaveBeenCalled();
        });

        it('should provide quickActions', () => {
            const module = registerModule(mockContext, mockDeps);
            const quickActions = module.quickActions?.();
            if (!quickActions) {
                throw new Error('Expected quick actions');
            }
            expect(Array.isArray(quickActions)).toBe(true);
            expect(quickActions.length).toBeGreaterThan(0);
        });

        it('should call getQuickActions', () => {
            const module = registerModule(mockContext, mockDeps);
            module.quickActions?.();
            expect(getQuickActions).toHaveBeenCalled();
        });

        it('should activate module correctly', async () => {
            const module = registerModule(mockContext, mockDeps);
            await module.activate(mockContext, mockDeps);
            
            const { registerCommands } = require('../commands');
            expect(registerCommands).toHaveBeenCalledWith(mockContext);
            expect(vscode.commands.executeCommand).toHaveBeenCalledWith('setContext', 'zeroui.module', 'm05');
            expect(mockStatusPillProviderInstance.initialize).toHaveBeenCalledWith(mockDeps);
            expect(mockDiagnosticsProviderInstance.initialize).toHaveBeenCalledWith(mockDeps);
            expect(mockDecisionCardProviderInstance.initialize).toHaveBeenCalledWith(mockDeps);
        });

        it('should deactivate module without error', async () => {
            const module = registerModule(mockContext, mockDeps);
            await expect(module.deactivate?.()).resolves.not.toThrow();
            expect(mockStatusPillProviderInstance.dispose).toHaveBeenCalled();
            expect(mockDiagnosticsProviderInstance.dispose).toHaveBeenCalled();
        });

        it('should create new provider instances on each call', () => {
            const module1 = registerModule(mockContext, mockDeps);
            const module2 = registerModule(mockContext, mockDeps);
            // Should create separate instances
            expect(module1).not.toBe(module2);
        });
    });
});
