/**
 * Detection Engine Core Module (PM-4)
 * 
 * Implements the Detection Engine Core module per PRD v1.0
 * Module ID: m05 (lowercase per architecture contract)
 */

import * as vscode from 'vscode';
import { registerCommands } from './commands';
import { DetectionEngineStatusPillProvider } from './providers/status-pill';
import { DetectionEngineDiagnosticsProvider } from './providers/diagnostics';
import { getQuickActions } from './actions/quick-actions';
import { DecisionCardSectionProvider } from './views/decision-card-sections/DecisionCardSectionProvider';

export interface CoreDeps {
    context: vscode.ExtensionContext;
    receiptReader?: any;
    ipcClient?: any;
}

export interface ZeroUIModule {
    id: 'm05';
    title: string;
    commands(): Array<{ id: string; title: string; handler: () => void | Promise<void> }>;
    statusPill?(): { getText: () => Promise<string>; getTooltip: () => Promise<string>; onClickCommandId?: string };
    decisionCard?(): Array<{ id: string; render: (webview: vscode.Webview, panel: vscode.WebviewPanel) => Promise<void> }>;
    evidenceDrawer?(): { listItems: () => Promise<readonly { label: string; open: () => Promise<void> }[]> };
    problems?(): { computeDiagnostics: () => Promise<readonly vscode.Diagnostic[]> };
    quickActions?(): Array<{ id: string; label: string }>;
    activate(context: vscode.ExtensionContext, deps: CoreDeps): Promise<void>;
    deactivate?(): Promise<void>;
}

export function registerModule(context: vscode.ExtensionContext, deps: CoreDeps): ZeroUIModule {
    const statusPillProvider = new DetectionEngineStatusPillProvider();
    const diagnosticsProvider = new DetectionEngineDiagnosticsProvider();
    const decisionCardProvider = new DecisionCardSectionProvider();

    const module: ZeroUIModule = {
        id: 'm05', // Lowercase per architecture contract (PRD Section 2, line 32)
        title: 'Detection Engine Core',
        
        commands: () => [
            {
                id: 'zeroui.m05.showDecisionCard',
                title: 'Show Decision Card',
                handler: async () => {
                    await vscode.commands.executeCommand('zeroui.showDecisionCard', { moduleId: 'm05' });
                }
            },
            {
                id: 'zeroui.m05.viewReceipt',
                title: 'View Last Receipt',
                handler: async () => {
                    await vscode.commands.executeCommand('zeroui.showReceiptViewer', { moduleId: 'm05' });
                }
            }
        ],

        statusPill: () => ({
            getText: async () => statusPillProvider.getText(),
            getTooltip: async () => statusPillProvider.getTooltip(),
            onClickCommandId: 'zeroui.m05.showDecisionCard'
        }),

        decisionCard: () => [
            {
                id: 'm05-detection-overview',
                render: async (webview, panel) => decisionCardProvider.renderOverview(webview, panel)
            },
            {
                id: 'm05-detection-details',
                render: async (webview, panel) => decisionCardProvider.renderDetails(webview, panel)
            }
        ],

        evidenceDrawer: () => ({
            listItems: async () => decisionCardProvider.listEvidenceItems()
        }),

        problems: () => ({
            computeDiagnostics: async () => diagnosticsProvider.computeDiagnostics()
        }),

        quickActions: () => {
            const actions = getQuickActions();
            return actions ? actions.map(action => ({ id: action.id, label: action.label })) : [];
        },

        activate: async (ctx: vscode.ExtensionContext, deps: CoreDeps) => {
            // Register commands
            registerCommands(ctx);
            
            // Set context key
            await vscode.commands.executeCommand('setContext', 'zeroui.module', 'm05');
            
            // Initialize providers
            await statusPillProvider.initialize(deps);
            await diagnosticsProvider.initialize(deps);
            await decisionCardProvider.initialize(deps);
        },

        deactivate: async () => {
            statusPillProvider.dispose();
            diagnosticsProvider.dispose();
        }
    };

    return module;
}
