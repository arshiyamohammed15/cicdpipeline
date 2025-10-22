import * as vscode from 'vscode';
import { IntegrationAdaptersUIComponentManager } from './UIComponentManager';

export class IntegrationAdaptersExtensionInterface implements vscode.Disposable {
    private uiManager: IntegrationAdaptersUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new IntegrationAdaptersUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.integration.adapters.showDashboard', () => {
            this.uiManager.showIntegrationAdaptersDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.integration.adapters.refresh', () => {
            this.uiManager.updateIntegrationAdaptersData({} as any);
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new IntegrationAdaptersTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiIntegrationAdapters', {
            treeDataProvider: treeProvider,
            showCollapseAll: true
        });

        this.disposables.push(treeView);
        context.subscriptions.push(...this.disposables);
    }

    public dispose(): void {
        this.disposables.forEach(d => d.dispose());
        this.uiManager.dispose();
    }
}

class IntegrationAdaptersTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.integration.adapters.showDashboard',
            title: 'Show IntegrationAdapters Dashboard'
        };
        return treeItem;
    }

    getChildren(element?: any): any[] {
        return [
            { label: 'Overview' },
            { label: 'Details' },
            { label: 'Reports' }
        ];
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }
}
