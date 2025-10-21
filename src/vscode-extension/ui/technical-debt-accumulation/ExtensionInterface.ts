import * as vscode from 'vscode';
import { TechnicalDebtAccumulationUIComponentManager } from './UIComponentManager';

export class TechnicalDebtAccumulationExtensionInterface implements vscode.Disposable {
    private uiManager: TechnicalDebtAccumulationUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new TechnicalDebtAccumulationUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.technical.debt.accumulation.showDashboard', () => {
            this.uiManager.showTechnicalDebtAccumulationDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.technical.debt.accumulation.refresh', () => {
            this.uiManager.updateTechnicalDebtAccumulationData({} as any);
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new TechnicalDebtAccumulationTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiTechnicalDebtAccumulation', {
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

class TechnicalDebtAccumulationTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.technical.debt.accumulation.showDashboard',
            title: 'Show TechnicalDebtAccumulation Dashboard'
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
