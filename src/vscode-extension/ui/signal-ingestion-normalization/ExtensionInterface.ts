import * as vscode from 'vscode';
import { SignalIngestionNormalizationUIComponentManager } from './UIComponentManager';

export class SignalIngestionNormalizationExtensionInterface implements vscode.Disposable {
    private uiManager: SignalIngestionNormalizationUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new SignalIngestionNormalizationUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.signal.ingestion.normalization.showDashboard', () => {
            this.uiManager.showSignalIngestionNormalizationDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.signal.ingestion.normalization.refresh', () => {
            this.uiManager.updateSignalIngestionNormalizationData({} as any);
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new SignalIngestionNormalizationTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiSignalIngestionNormalization', {
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

class SignalIngestionNormalizationTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.signal.ingestion.normalization.showDashboard',
            title: 'Show SignalIngestionNormalization Dashboard'
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
