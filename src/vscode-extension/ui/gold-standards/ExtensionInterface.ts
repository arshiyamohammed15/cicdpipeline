import * as vscode from 'vscode';
import { GoldStandardsUIComponentManager } from './UIComponentManager';

export class GoldStandardsExtensionInterface implements vscode.Disposable {
    private uiManager: GoldStandardsUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new GoldStandardsUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.gold.standards.showDashboard', () => {
            this.uiManager.showGoldStandardsDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.gold.standards.refresh', () => {
            this.uiManager.updateGoldStandardsData({} as any);
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new GoldStandardsTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiGoldStandards', {
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

class GoldStandardsTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.gold.standards.showDashboard',
            title: 'Show GoldStandards Dashboard'
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
