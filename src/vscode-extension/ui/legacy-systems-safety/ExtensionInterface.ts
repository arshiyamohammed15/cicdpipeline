import * as vscode from 'vscode';
import { LegacySystemsSafetyUIComponentManager } from './UIComponentManager';

export class LegacySystemsSafetyExtensionInterface implements vscode.Disposable {
    private uiManager: LegacySystemsSafetyUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new LegacySystemsSafetyUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.legacy.systems.safety.showDashboard', () => {
            this.uiManager.showLegacySystemsSafetyDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.legacy.systems.safety.refresh', () => {
            this.uiManager.updateLegacySystemsSafetyData({} as any);
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new LegacySystemsSafetyTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiLegacySystemsSafety', {
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
        this._onDidChangeTreeData.fire();
    }
}
