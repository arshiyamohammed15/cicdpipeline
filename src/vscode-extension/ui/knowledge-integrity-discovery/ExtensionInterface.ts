import * as vscode from 'vscode';
import { KnowledgeIntegrityDiscoveryUIComponentManager } from './UIComponentManager';

export class KnowledgeIntegrityDiscoveryExtensionInterface implements vscode.Disposable {
    private uiManager: KnowledgeIntegrityDiscoveryUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new KnowledgeIntegrityDiscoveryUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.knowledge.integrity.discovery.showDashboard', () => {
            this.uiManager.showKnowledgeIntegrityDiscoveryDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.knowledge.integrity.discovery.refresh', () => {
            this.uiManager.updateKnowledgeIntegrityDiscoveryData({} as any);
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new KnowledgeIntegrityDiscoveryTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiKnowledgeIntegrityDiscovery', {
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

class KnowledgeIntegrityDiscoveryTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.knowledge.integrity.discovery.showDashboard',
            title: 'Show KnowledgeIntegrityDiscovery Dashboard'
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
