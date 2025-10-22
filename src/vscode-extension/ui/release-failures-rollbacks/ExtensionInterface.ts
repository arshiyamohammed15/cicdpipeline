import * as vscode from 'vscode';
import { ReleaseFailuresRollbacksUIComponentManager } from './UIComponentManager';

export class ReleaseFailuresRollbacksExtensionInterface implements vscode.Disposable {
    private uiManager: ReleaseFailuresRollbacksUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new ReleaseFailuresRollbacksUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.release.failures.rollbacks.showDashboard', () => {
            this.uiManager.showReleaseFailuresRollbacksDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.release.failures.rollbacks.refresh', () => {
            this.uiManager.updateReleaseFailuresRollbacksData({} as any);
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new ReleaseFailuresRollbacksTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiReleaseFailuresRollbacks', {
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

class ReleaseFailuresRollbacksTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.release.failures.rollbacks.showDashboard',
            title: 'Show ReleaseFailuresRollbacks Dashboard'
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
