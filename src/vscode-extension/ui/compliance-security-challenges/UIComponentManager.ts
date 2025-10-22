import * as vscode from 'vscode';
import { ComplianceSecurityUIComponent } from './UIComponent';
import { ComplianceSecurityData } from './types';

export class ComplianceSecurityUIComponentManager implements vscode.Disposable {
    private webviewPanel: vscode.WebviewPanel | undefined;
    private uiComponent: ComplianceSecurityUIComponent;

    constructor() {
        this.uiComponent = new ComplianceSecurityUIComponent();
    }

    public showComplianceSecurityDashboard(data?: ComplianceSecurityData): void {
        if (this.webviewPanel) {
            this.webviewPanel.reveal(vscode.ViewColumn.One);
            return;
        }

        this.webviewPanel = vscode.window.createWebviewPanel(
            'zerouiComplianceSecurity',
            'ZeroUI Compliance & Security Dashboard',
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

    public updateComplianceSecurityData(data: ComplianceSecurityData): void {
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
