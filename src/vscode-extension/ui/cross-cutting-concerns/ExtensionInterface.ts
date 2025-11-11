import * as vscode from 'vscode';
import { CrossCuttingConcernsUIComponentManager } from './UIComponentManager';

export class CrossCuttingConcernsExtensionInterface implements vscode.Disposable {
    private uiManager: CrossCuttingConcernsUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new CrossCuttingConcernsUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.cross.cutting.concerns.showDashboard', () => {
            this.uiManager.showCrossCuttingConcernsDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.cross.cutting.concerns.refresh', () => {
            this.uiManager.updateCrossCuttingConcernsData({} as any);
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new CrossCuttingConcernsTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiCrossCuttingConcerns', {
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
