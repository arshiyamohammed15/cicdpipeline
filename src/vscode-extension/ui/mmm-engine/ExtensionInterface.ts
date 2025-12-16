import * as vscode from 'vscode';
import { MMMEngineUIComponentManager } from './UIComponentManager';

export class MMMEngineExtensionInterface implements vscode.Disposable {
    private uiManager: MMMEngineUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new MMMEngineUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        // Register MMM Engine specific commands
        // CR-064: Add error boundary for command registration
        const showMMMDashboard = vscode.commands.registerCommand('zeroui.mmm.showDashboard', () => {
            try {
                this.uiManager.showMMMEngineDashboard();
            } catch (error) {
                console.error('Failed to show MMM Engine dashboard:', error);
                vscode.window.showErrorMessage('Failed to show MMM Engine dashboard');
            }
        });

        const refreshMMMData = vscode.commands.registerCommand('zeroui.mmm.refresh', () => {
            // CR-063: Use proper type instead of unsafe type casting
            // CR-064: Add error boundary
            try {
                const emptyData: import('./types').MMMEngineData = {
                    metricsCollected: 0,
                    measurements: 0,
                    monitoringStatus: 'inactive',
                    metricsTrend: '',
                    measurementsTrend: '',
                    lastUpdate: new Date().toISOString()
                };
                this.uiManager.updateMMMEngineData(emptyData);
            } catch (error) {
                console.error('Failed to refresh MMM Engine data:', error);
                vscode.window.showErrorMessage('Failed to refresh MMM Engine data');
            }
        });

        const exportMMMReport = vscode.commands.registerCommand('zeroui.mmm.exportReport', () => {
            // CR-064: Add error boundary
            try {
                this.exportMMMReport();
            } catch (error) {
                console.error('Failed to export MMM Engine report:', error);
                vscode.window.showErrorMessage('Failed to export MMM Engine report');
            }
        });

        this.disposables.push(showMMMDashboard, refreshMMMData, exportMMMReport);
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        // Register MMM Engine specific views
        // CR-064: Add error boundary for tree view creation
        try {
            const mmmTreeProvider = new MMMTreeDataProvider();
            const mmmTreeView = vscode.window.createTreeView('zerouiMMMEngine', {
                treeDataProvider: mmmTreeProvider,
                showCollapseAll: true
            });

            this.disposables.push(mmmTreeView);
            context.subscriptions.push(...this.disposables);
        } catch (error) {
            console.error('Failed to register MMM Engine views:', error);
            vscode.window.showErrorMessage('Failed to initialize MMM Engine views');
        }
    }

    private exportMMMReport(): void {
        vscode.window.showInformationMessage('MMM Engine report export functionality');
    }

    public dispose(): void {
        this.disposables.forEach(d => d.dispose());
        this.uiManager.dispose();
    }
}

class MMMTreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.mmm.showDashboard',
            title: 'Show MMM Dashboard'
        };
        return treeItem;
    }

    getChildren(element?: any): any[] {
        return [
            { label: 'Metrics Overview' },
            { label: 'Measurements' },
            { label: 'Monitoring Status' }
        ];
    }

    refresh(): void {
        this._onDidChangeTreeData.fire(undefined);
    }
}
