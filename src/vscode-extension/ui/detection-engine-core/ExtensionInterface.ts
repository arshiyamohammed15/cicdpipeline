import * as vscode from 'vscode';
import { DetectionEngineCoreUIComponentManager } from './UIComponentManager';

export class DetectionEngineCoreExtensionInterface implements vscode.Disposable {
    private uiManager: DetectionEngineCoreUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new DetectionEngineCoreUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.detection.engine.core.showDashboard', () => {
            this.uiManager.showDetectionEngineCoreDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.detection.engine.core.refresh', () => {
            this.uiManager.updateDetectionEngineCoreData({} as any);
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new DetectionEngineCoreTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiDetectionEngineCore', {
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

class DetectionEngineCoreTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.detection.engine.core.showDashboard',
            title: 'Show DetectionEngineCore Dashboard'
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
