import * as vscode from 'vscode';
import { ClientAdminDashboardUIComponentManager } from './UIComponentManager';

export class ClientAdminDashboardExtensionInterface implements vscode.Disposable {
    private uiManager: ClientAdminDashboardUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new ClientAdminDashboardUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.client.admin.dashboard.showDashboard', () => {
            this.uiManager.showClientAdminDashboardDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.client.admin.dashboard.refresh', () => {
            this.uiManager.updateClientAdminDashboardData({} as any);
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new ClientAdminDashboardTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiClientAdminDashboard', {
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

class ClientAdminDashboardTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.client.admin.dashboard.showDashboard',
            title: 'Show ClientAdminDashboard Dashboard'
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
        this._onDidChangeTreeData.fire(undefined);
    }
}
