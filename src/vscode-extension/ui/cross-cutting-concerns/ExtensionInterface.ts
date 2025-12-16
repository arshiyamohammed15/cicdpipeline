import * as vscode from 'vscode';
import { CrossCuttingConcernsUIComponentManager } from './UIComponentManager';

export class CrossCuttingConcernsExtensionInterface implements vscode.Disposable {
    private uiManager: CrossCuttingConcernsUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new CrossCuttingConcernsUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        // CR-064: Add error boundary
        const showDashboard = vscode.commands.registerCommand('zeroui.cross.cutting.concerns.showDashboard', () => {
            try {
                this.uiManager.showCrossCuttingConcernsDashboard();
            } catch (error) {
                console.error('Failed to show Cross Cutting Concerns dashboard:', error);
                vscode.window.showErrorMessage('Failed to show dashboard');
            }
        });

        const refresh = vscode.commands.registerCommand('zeroui.cross.cutting.concerns.refresh', () => {
            // CR-063: Use undefined instead of unsafe type casting
            // CR-064: Add error boundary
            try {
                this.uiManager.updateCrossCuttingConcernsData(undefined);
            } catch (error) {
                console.error('Failed to refresh Cross Cutting Concerns data:', error);
                vscode.window.showErrorMessage('Failed to refresh data');
            }
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        // CR-064: Add error boundary
        try {
            const treeProvider = new CrossCuttingConcernsTreeDataProvider();
            const treeView = vscode.window.createTreeView('zerouiCrossCuttingConcerns', {
                treeDataProvider: treeProvider,
                showCollapseAll: true
            });

            this.disposables.push(treeView);
            context.subscriptions.push(...this.disposables);
        } catch (error) {
            console.error('Failed to register Cross Cutting Concerns views:', error);
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
            console.error('Error disposing Cross Cutting Concerns Extension Interface:', error);
        }
    }
}

class CrossCuttingConcernsTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.cross.cutting.concerns.showDashboard',
            title: 'Show CrossCuttingConcerns Dashboard'
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
