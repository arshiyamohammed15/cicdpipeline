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
    }

    public updateMMMEngineData(data: MMMEngineData): void {
        if (this.webviewPanel) {
            this.webviewPanel.webview.html = this.uiComponent.renderDashboard(data);
        }
    }

    public dispose(): void {
        if (this.webviewPanel) {
            this.webviewPanel.dispose();
        }
    }
}
