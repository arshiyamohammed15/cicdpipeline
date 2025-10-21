import * as vscode from 'vscode';
import { ReportingUIComponentManager } from './UIComponentManager';

export class ReportingExtensionInterface implements vscode.Disposable {
    private uiManager: ReportingUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new ReportingUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.reporting.showDashboard', () => {
            this.uiManager.showReportingDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.reporting.refresh', () => {
            this.uiManager.updateReportingData({} as any);
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new ReportingTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiReporting', {
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

class ReportingTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.reporting.showDashboard',
            title: 'Show Reporting Dashboard'
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
