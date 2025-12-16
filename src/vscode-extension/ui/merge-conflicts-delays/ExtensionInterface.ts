import * as vscode from 'vscode';
import { MergeConflictsDelaysUIComponentManager } from './UIComponentManager';

export class MergeConflictsDelaysExtensionInterface implements vscode.Disposable {
    private uiManager: MergeConflictsDelaysUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new MergeConflictsDelaysUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        // CR-064: Add error boundary
        const showDashboard = vscode.commands.registerCommand('zeroui.merge.conflicts.delays.showDashboard', () => {
            try {
                this.uiManager.showMergeConflictsDelaysDashboard();
            } catch (error) {
                console.error('Failed to show Merge Conflicts Delays dashboard:', error);
                vscode.window.showErrorMessage('Failed to show dashboard');
            }
        });

        // CR-063: Use undefined instead of unsafe type casting
        // CR-064: Add error boundary
        const refresh = vscode.commands.registerCommand('zeroui.merge.conflicts.delays.refresh', () => {
            try {
                this.uiManager.updateMergeConflictsDelaysData(undefined);
            } catch (error) {
                console.error('Failed to refresh Merge Conflicts Delays data:', error);
                vscode.window.showErrorMessage('Failed to refresh data');
            }
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        // CR-064: Add error boundary
        try {
            const treeProvider = new MergeConflictsDelaysTreeDataProvider();
            const treeView = vscode.window.createTreeView('zerouiMergeConflictsDelays', {
                treeDataProvider: treeProvider,
                showCollapseAll: true
            });

            this.disposables.push(treeView);
            context.subscriptions.push(...this.disposables);
        } catch (error) {
            console.error('Failed to register Merge Conflicts Delays views:', error);
            vscode.window.showErrorMessage('Failed to initialize views');
        }
    }

    // CR-062: Ensure proper disposal pattern
    public dispose(): void {
        try {
            this.disposables.forEach(d => {
                try {
                    d.dispose();
                } catch (error) {
                    console.error('Error disposing resource:', error);
                }
            });
            this.disposables = [];
            this.uiManager.dispose();
        } catch (error) {
            console.error('Error disposing Merge Conflicts Delays Extension Interface:', error);
        }
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
        this._onDidChangeTreeData.fire(undefined);
    }
}
