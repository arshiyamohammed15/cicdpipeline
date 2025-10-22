import * as vscode from 'vscode';

export class EvidenceDrawerManager implements vscode.Disposable {
    private webviewPanel: vscode.WebviewPanel | undefined;

    constructor() {
        // Initialize evidence drawer manager
    }

    public showEvidenceDrawer(evidenceData?: any): void {
        if (this.webviewPanel) {
            this.webviewPanel.reveal(vscode.ViewColumn.Two);
            return;
        }

        this.webviewPanel = vscode.window.createWebviewPanel(
            'zerouiEvidenceDrawer',
            'ZeroUI Evidence Drawer',
            vscode.ViewColumn.Two,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        this.webviewPanel.webview.html = this.getWebviewContent(evidenceData);

        this.webviewPanel.onDidDispose(() => {
            this.webviewPanel = undefined;
        });
    }

    private getWebviewContent(evidenceData?: any): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZeroUI Evidence Drawer</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 20px;
        }
        .evidence-drawer {
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            padding: 16px;
        }
        .evidence-header {
            font-weight: bold;
            margin-bottom: 16px;
        }
        .evidence-item {
            margin-bottom: 12px;
            padding: 8px;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
        }
        .evidence-link {
            color: var(--vscode-textLink-foreground);
            text-decoration: underline;
            cursor: pointer;
        }
        .evidence-link:hover {
            color: var(--vscode-textLink-activeForeground);
        }
    </style>
</head>
<body>
    <div class="evidence-drawer">
        <div class="evidence-header">ZeroUI Evidence Drawer</div>
        <div class="evidence-content">
            ${evidenceData ? this.renderEvidenceContent(evidenceData) : 'No evidence data available'}
        </div>
    </div>
</body>
</html>`;
    }

    private renderEvidenceContent(evidenceData: any): string {
        if (!evidenceData || !evidenceData.evidenceHandles) {
            return 'No evidence data available';
        }

        return evidenceData.evidenceHandles.map((handle: any, index: number) => `
            <div class="evidence-item">
                <strong>Evidence ${index + 1}:</strong>
                <a href="${handle.url}" class="evidence-link" target="_blank">${handle.description || 'View Evidence'}</a>
                <p><small>Type: ${handle.type || 'Unknown'}</small></p>
            </div>
        `).join('');
    }

    public dispose(): void {
        if (this.webviewPanel) {
            this.webviewPanel.dispose();
        }
    }
}
