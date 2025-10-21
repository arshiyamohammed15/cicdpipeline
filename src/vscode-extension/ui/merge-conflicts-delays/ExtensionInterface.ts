import * as vscode from 'vscode';
import { MergeConflictsDelaysUIComponentManager } from './UIComponentManager';

export class MergeConflictsDelaysExtensionInterface implements vscode.Disposable {
    private uiManager: MergeConflictsDelaysUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new MergeConflictsDelaysUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.merge.conflicts.delays.showDashboard', () => {
            this.uiManager.showMergeConflictsDelaysDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.merge.conflicts.delays.refresh', () => {
            this.uiManager.updateMergeConflictsDelaysData({} as any);
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new MergeConflictsDelaysTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiMergeConflictsDelays', {
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

class MergeConflictsDelaysTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.merge.conflicts.delays.showDashboard',
            title: 'Show MergeConflictsDelays Dashboard'
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
