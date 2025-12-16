import * as vscode from 'vscode';
import { MMMEngineUIComponent } from './UIComponent';
import { MMMEngineData } from './types';

export class MMMEngineUIComponentManager implements vscode.Disposable {
    private webviewPanel: vscode.WebviewPanel | undefined;
    private uiComponent: MMMEngineUIComponent;

    constructor() {
        this.uiComponent = new MMMEngineUIComponent();
    }

    public showMMMEngineDashboard(data?: MMMEngineData): void {
        // CR-064: Add error boundary for UI rendering
        try {
            if (this.webviewPanel) {
                this.webviewPanel.reveal(vscode.ViewColumn.One);
                return;
            }

            this.webviewPanel = vscode.window.createWebviewPanel(
                'zerouiMMMEngine',
                'ZeroUI MMM Engine Dashboard',
                vscode.ViewColumn.One,
                {
                    enableScripts: true,
                    retainContextWhenHidden: true
                }
            );

            this.webviewPanel.webview.html = this.uiComponent.renderDashboard(data);

            this.webviewPanel.onDidDispose(() => {
                this.webviewPanel = undefined;
            });
        } catch (error) {
            console.error('Failed to show MMM Engine dashboard:', error);
            vscode.window.showErrorMessage('Failed to display MMM Engine dashboard');
            // CR-062: Ensure cleanup on error
            if (this.webviewPanel) {
                this.webviewPanel.dispose();
                this.webviewPanel = undefined;
            }
        }
    }

    public updateMMMEngineData(data: MMMEngineData): void {
        // CR-064: Add error boundary for UI updates
        try {
            if (this.webviewPanel) {
                this.webviewPanel.webview.html = this.uiComponent.renderDashboard(data);
            }
        } catch (error) {
            console.error('Failed to update MMM Engine data:', error);
            // Don't show error to user for background updates
        }
    }

    // CR-062: Ensure proper disposal pattern implementation
    public dispose(): void {
        try {
            if (this.webviewPanel) {
                this.webviewPanel.dispose();
                this.webviewPanel = undefined;
            }
        } catch (error) {
            console.error('Error disposing MMM Engine UI Component Manager:', error);
        }
    }
}
