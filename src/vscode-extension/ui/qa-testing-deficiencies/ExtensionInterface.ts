import * as vscode from 'vscode';
import { QaTestingDeficienciesUIComponentManager } from './UIComponentManager';

export class QaTestingDeficienciesExtensionInterface implements vscode.Disposable {
    private uiManager: QaTestingDeficienciesUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new QaTestingDeficienciesUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.qa.testing.deficiencies.showDashboard', () => {
            this.uiManager.showQaTestingDeficienciesDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.qa.testing.deficiencies.refresh', () => {
            this.uiManager.updateQaTestingDeficienciesData({} as any);
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new QaTestingDeficienciesTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiQaTestingDeficiencies', {
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

class QaTestingDeficienciesTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.qa.testing.deficiencies.showDashboard',
            title: 'Show QaTestingDeficiencies Dashboard'
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
