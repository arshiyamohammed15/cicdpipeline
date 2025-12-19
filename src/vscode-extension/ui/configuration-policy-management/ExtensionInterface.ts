/**
 * Extension Interface for Configuration & Policy Management (EPC-3).
 *
 * Per PRD: Registers VS Code commands and integrates with Edge Agent for receipt consumption.
 */

import * as vscode from 'vscode';
import { ConfigurationPolicyManagementUIComponentManager } from './UIComponentManager';

export class ConfigurationPolicyManagementExtensionInterface implements vscode.Disposable {
    private readonly uiManager: ConfigurationPolicyManagementUIComponentManager;
    private readonly disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new ConfigurationPolicyManagementUIComponentManager();
    }

    /**
     * Register VS Code commands per PRD (lines 177-181).
     *
     * @param context VS Code extension context
     */
    public registerCommands(context: vscode.ExtensionContext): void {
        // Register showDashboard command
        const showDashboard = vscode.commands.registerCommand(
            'zeroui.configuration-policy-management.showDashboard',
            () => {
                this.uiManager.showDashboard();
            }
        );

        // Register showPolicyManagement command
        const showPolicyManagement = vscode.commands.registerCommand(
            'zeroui.configuration-policy-management.showPolicyManagement',
            () => {
                this.uiManager.showPolicyManagement();
            }
        );

        // Register showConfigurationManagement command
        const showConfigurationManagement = vscode.commands.registerCommand(
            'zeroui.configuration-policy-management.showConfigurationManagement',
            () => {
                this.uiManager.showConfigurationManagement();
            }
        );

        // Register showComplianceReporting command
        const showComplianceReporting = vscode.commands.registerCommand(
            'zeroui.configuration-policy-management.showComplianceReporting',
            () => {
                this.uiManager.showComplianceReporting();
            }
        );

        this.disposables.push(
            showDashboard,
            showPolicyManagement,
            showConfigurationManagement,
            showComplianceReporting
        );

        context.subscriptions.push(
            showDashboard,
            showPolicyManagement,
            showConfigurationManagement,
            showComplianceReporting
        );
    }

    /**
     * Register tree view provider per PRD.
     *
     * @param context VS Code extension context
     */
    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new ConfigurationPolicyManagementTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiConfigurationPolicyManagement', {
            treeDataProvider: treeProvider,
            showCollapseAll: true
        });

        this.disposables.push(treeView);
        context.subscriptions.push(treeView);
    }

    /**
     * Integrate with Edge Agent for receipt consumption per PRD.
     *
     * Note: This is a placeholder - actual integration will be implemented
     * when Edge Agent is available.
     */
    public async consumeReceiptFromEdgeAgent(receiptData: unknown): Promise<void> {
        // TODO: Parse receipt and update appropriate UI component
        // Receipts flow from Tier 3 → Tier 2 → Tier 1
        console.log('[Configuration Policy Management] Received receipt from Edge Agent:', receiptData);
    }

    public dispose(): void {
        this.disposables.forEach(disposable => disposable.dispose());
        this.uiManager.dispose();
    }
}

class ConfigurationPolicyManagementTreeDataProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<vscode.TreeItem | undefined | null | void> = new vscode.EventEmitter<vscode.TreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<vscode.TreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: vscode.TreeItem): Thenable<vscode.TreeItem[]> {
        if (!element) {
            return Promise.resolve([
                new vscode.TreeItem('Policy Management', vscode.TreeItemCollapsibleState.None),
                new vscode.TreeItem('Configuration Management', vscode.TreeItemCollapsibleState.None),
                new vscode.TreeItem('Compliance Reporting', vscode.TreeItemCollapsibleState.None)
            ]);
        }
        return Promise.resolve([]);
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }
}
