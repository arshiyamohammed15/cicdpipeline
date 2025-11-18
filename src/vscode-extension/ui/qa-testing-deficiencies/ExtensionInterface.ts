import * as vscode from 'vscode';
import { QATestingDeficienciesUIComponentManager } from './UIComponentManager';

export class QATestingDeficienciesExtensionInterface implements vscode.Disposable {
    private readonly uiManager: QATestingDeficienciesUIComponentManager;
    private readonly disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new QATestingDeficienciesUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.qaTesting.showDashboard', () => {
            this.uiManager.showQATestingDeficienciesDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.qaTesting.refresh', () => {
            this.uiManager.updateQATestingDeficienciesData({} as unknown);
        });

        const exportReport = vscode.commands.registerCommand('zeroui.qaTesting.exportReport', () => {
            vscode.window.showInformationMessage('QA Testing report export is not implemented yet.');
        });

        this.disposables.push(showDashboard, refresh, exportReport);
        context.subscriptions.push(showDashboard, refresh, exportReport);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new QATestingDeficienciesTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiQATestingDeficiencies', {
            treeDataProvider: treeProvider,
            showCollapseAll: true
        });

        this.disposables.push(treeView);
        context.subscriptions.push(treeView);
    }

    public dispose(): void {
        this.disposables.forEach(disposable => disposable.dispose());
        this.uiManager.dispose();
    }
}

class QATestingDeficienciesTreeDataProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
    private readonly _onDidChangeTreeData: vscode.EventEmitter<vscode.TreeItem | undefined | null | void> =
        new vscode.EventEmitter();

    readonly onDidChangeTreeData: vscode.Event<vscode.TreeItem | undefined | null | void> =
        this._onDidChangeTreeData.event;

    getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(): vscode.TreeItem[] {
        return [
            new vscode.TreeItem('Test Coverage Status', vscode.TreeItemCollapsibleState.None),
            new vscode.TreeItem('Flaky Test Watchlist', vscode.TreeItemCollapsibleState.None),
            new vscode.TreeItem('Regression Risks', vscode.TreeItemCollapsibleState.None)
        ];
    }

    refresh(): void {
        this._onDidChangeTreeData.fire(undefined);
    }
}
