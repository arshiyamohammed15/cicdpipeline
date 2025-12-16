import * as vscode from 'vscode';
import { KnowledgeSiloPreventionUIComponentManager } from './UIComponentManager';

export class KnowledgeSiloPreventionExtensionInterface implements vscode.Disposable {
    private uiManager: KnowledgeSiloPreventionUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new KnowledgeSiloPreventionUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        // CR-064: Add error boundary
        const showDashboard = vscode.commands.registerCommand('zeroui.knowledge.silo.prevention.showDashboard', () => {
            try {
                this.uiManager.showKnowledgeSiloPreventionDashboard();
            } catch (error) {
                console.error('Failed to show Knowledge Silo Prevention dashboard:', error);
                vscode.window.showErrorMessage('Failed to show dashboard');
            }
        });

        // CR-063: Use undefined instead of unsafe type casting
        // CR-064: Add error boundary
        const refresh = vscode.commands.registerCommand('zeroui.knowledge.silo.prevention.refresh', () => {
            try {
                this.uiManager.updateKnowledgeSiloPreventionData(undefined);
            } catch (error) {
                console.error('Failed to refresh Knowledge Silo Prevention data:', error);
                vscode.window.showErrorMessage('Failed to refresh data');
            }
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        // CR-064: Add error boundary
        try {
            const treeProvider = new KnowledgeSiloPreventionTreeDataProvider();
            const treeView = vscode.window.createTreeView('zerouiKnowledgeSiloPrevention', {
                treeDataProvider: treeProvider,
                showCollapseAll: true
            });

            this.disposables.push(treeView);
            context.subscriptions.push(...this.disposables);
        } catch (error) {
            console.error('Failed to register Knowledge Silo Prevention views:', error);
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
            console.error('Error disposing Knowledge Silo Prevention Extension Interface:', error);
        }
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
