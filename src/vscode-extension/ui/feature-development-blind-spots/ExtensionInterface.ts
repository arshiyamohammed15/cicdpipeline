import * as vscode from 'vscode';
import { FeatureDevelopmentBlindSpotsUIComponentManager } from './UIComponentManager';

export class FeatureDevelopmentBlindSpotsExtensionInterface implements vscode.Disposable {
    private uiManager: FeatureDevelopmentBlindSpotsUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new FeatureDevelopmentBlindSpotsUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        // CR-064: Add error boundary
        const showDashboard = vscode.commands.registerCommand('zeroui.feature.development.blind.spots.showDashboard', () => {
            try {
                this.uiManager.showFeatureDevelopmentBlindSpotsDashboard();
            } catch (error) {
                console.error('Failed to show Feature Development Blind Spots dashboard:', error);
                vscode.window.showErrorMessage('Failed to show dashboard');
            }
        });

        // CR-063: Use undefined instead of unsafe type casting
        // CR-064: Add error boundary
        const refresh = vscode.commands.registerCommand('zeroui.feature.development.blind.spots.refresh', () => {
            try {
                this.uiManager.updateFeatureDevelopmentBlindSpotsData(undefined);
            } catch (error) {
                console.error('Failed to refresh Feature Development Blind Spots data:', error);
                vscode.window.showErrorMessage('Failed to refresh data');
            }
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        // CR-064: Add error boundary
        try {
            const treeProvider = new FeatureDevelopmentBlindSpotsTreeDataProvider();
            const treeView = vscode.window.createTreeView('zerouiFeatureDevelopmentBlindSpots', {
                treeDataProvider: treeProvider,
                showCollapseAll: true
            });

            this.disposables.push(treeView);
            context.subscriptions.push(...this.disposables);
        } catch (error) {
            console.error('Failed to register Feature Development Blind Spots views:', error);
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
            console.error('Error disposing Feature Development Blind Spots Extension Interface:', error);
        }
    }
}

class FeatureDevelopmentBlindSpotsTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.feature.development.blind.spots.showDashboard',
            title: 'Show FeatureDevelopmentBlindSpots Dashboard'
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
