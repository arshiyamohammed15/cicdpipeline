import * as vscode from 'vscode';
import { FeatureDevelopmentBlindSpotsUIComponentManager } from './UIComponentManager';

export class FeatureDevelopmentBlindSpotsExtensionInterface implements vscode.Disposable {
    private uiManager: FeatureDevelopmentBlindSpotsUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new FeatureDevelopmentBlindSpotsUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.feature.development.blind.spots.showDashboard', () => {
            this.uiManager.showFeatureDevelopmentBlindSpotsDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.feature.development.blind.spots.refresh', () => {
            this.uiManager.updateFeatureDevelopmentBlindSpotsData({} as any);
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new FeatureDevelopmentBlindSpotsTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiFeatureDevelopmentBlindSpots', {
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
        this._onDidChangeTreeData.fire();
    }
}
