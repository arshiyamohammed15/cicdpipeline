import * as vscode from 'vscode';
import { LegacySystemsSafetyUIComponentManager } from './UIComponentManager';

export class LegacySystemsSafetyExtensionInterface implements vscode.Disposable {
    private uiManager: LegacySystemsSafetyUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new LegacySystemsSafetyUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        // CR-064: Add error boundary
        const showDashboard = vscode.commands.registerCommand('zeroui.legacy.systems.safety.showDashboard', () => {
            try {
                this.uiManager.showLegacySystemsSafetyDashboard();
            } catch (error) {
                console.error('Failed to show Legacy Systems Safety dashboard:', error);
                vscode.window.showErrorMessage('Failed to show dashboard');
            }
        });

        // CR-063: Use undefined instead of unsafe type casting
        // CR-064: Add error boundary
        const refresh = vscode.commands.registerCommand('zeroui.legacy.systems.safety.refresh', () => {
            try {
                this.uiManager.updateLegacySystemsSafetyData(undefined);
            } catch (error) {
                console.error('Failed to refresh Legacy Systems Safety data:', error);
                vscode.window.showErrorMessage('Failed to refresh data');
            }
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        // CR-064: Add error boundary
        try {
            const treeProvider = new LegacySystemsSafetyTreeDataProvider();
            const treeView = vscode.window.createTreeView('zerouiLegacySystemsSafety', {
                treeDataProvider: treeProvider,
                showCollapseAll: true
            });

            this.disposables.push(treeView);
            context.subscriptions.push(...this.disposables);
        } catch (error) {
            console.error('Failed to register Legacy Systems Safety views:', error);
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
            console.error('Error disposing Legacy Systems Safety Extension Interface:', error);
        }
    }
}

class LegacySystemsSafetyTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.legacy.systems.safety.showDashboard',
            title: 'Show LegacySystemsSafety Dashboard'
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
