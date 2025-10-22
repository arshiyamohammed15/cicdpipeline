import * as vscode from 'vscode';
import { MonitoringObservabilityGapsUIComponentManager } from './UIComponentManager';

export class MonitoringObservabilityGapsExtensionInterface implements vscode.Disposable {
    private uiManager: MonitoringObservabilityGapsUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new MonitoringObservabilityGapsUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showDashboard = vscode.commands.registerCommand('zeroui.monitoring.observability.gaps.showDashboard', () => {
            this.uiManager.showMonitoringObservabilityGapsDashboard();
        });

        const refresh = vscode.commands.registerCommand('zeroui.monitoring.observability.gaps.refresh', () => {
            this.uiManager.updateMonitoringObservabilityGapsData({} as any);
        });

        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const treeProvider = new MonitoringObservabilityGapsTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiMonitoringObservabilityGaps', {
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

class MonitoringObservabilityGapsTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.monitoring.observability.gaps.showDashboard',
            title: 'Show MonitoringObservabilityGaps Dashboard'
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
