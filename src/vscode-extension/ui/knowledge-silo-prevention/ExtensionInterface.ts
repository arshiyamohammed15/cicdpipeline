import * as vscode from 'vscode';
import { KnowledgeSiloPreventionUIComponentManager } from './UIComponentManager';

export class KnowledgeSiloPreventionExtensionInterface implements vscode.Disposable {
    private uiManager: KnowledgeSiloPreventionUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new KnowledgeSiloPreventionUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.knowledge.silo.prevention.showDashboard', () => {
            this.uiManager.showKnowledgeSiloPreventionDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.knowledge.silo.prevention.refresh', () => {
            this.uiManager.updateKnowledgeSiloPreventionData({} as any);
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new KnowledgeSiloPreventionTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiKnowledgeSiloPrevention', {
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

class KnowledgeSiloPreventionTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.knowledge.silo.prevention.showDashboard',
            title: 'Show KnowledgeSiloPrevention Dashboard'
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
