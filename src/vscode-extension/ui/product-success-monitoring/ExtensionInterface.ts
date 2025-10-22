import * as vscode from 'vscode';
import { ProductSuccessMonitoringUIComponentManager } from './UIComponentManager';

export class ProductSuccessMonitoringExtensionInterface implements vscode.Disposable {
    private uiManager: ProductSuccessMonitoringUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new ProductSuccessMonitoringUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.product.success.monitoring.showDashboard', () => {
            this.uiManager.showProductSuccessMonitoringDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.product.success.monitoring.refresh', () => {
            this.uiManager.updateProductSuccessMonitoringData({} as any);
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new ProductSuccessMonitoringTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiProductSuccessMonitoring', {
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

class ProductSuccessMonitoringTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.product.success.monitoring.showDashboard',
            title: 'Show ProductSuccessMonitoring Dashboard'
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
