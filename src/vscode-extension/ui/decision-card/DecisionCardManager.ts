import * as vscode from 'vscode';

export class DecisionCardManager implements vscode.Disposable {
    private webviewPanel: vscode.WebviewPanel | undefined;

    constructor() {
        // Initialize decision card manager
    }

    public showDecisionCard(decisionData?: any): void {
        if (this.webviewPanel) {
            this.webviewPanel.reveal(vscode.ViewColumn.One);
            return;
        }

        this.webviewPanel = vscode.window.createWebviewPanel(
            'zerouiDecisionCard',
            'ZeroUI Decision Card',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        this.webviewPanel.webview.html = this.getWebviewContent(decisionData);

        this.webviewPanel.onDidDispose(() => {
            this.webviewPanel = undefined;
        });
    }

    private getWebviewContent(decisionData?: any): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZeroUI Decision Card</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 20px;
        }
        .decision-card {
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            padding: 16px;
            margin-bottom: 16px;
        }
        .decision-header {
            font-weight: bold;
            margin-bottom: 8px;
        }
        .decision-content {
            margin-bottom: 12px;
        }
        .decision-actions {
            display: flex;
            gap: 8px;
        }
        .action-button {
            padding: 8px 16px;
            border: 1px solid var(--vscode-button-border);
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border-radius: 4px;
            cursor: pointer;
        }
        .action-button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }
    </style>
</head>
<body>
    <div class="decision-card">
        <div class="decision-header">ZeroUI Decision Card</div>
        <div class="decision-content">
            ${decisionData ? this.renderDecisionContent(decisionData) : 'No decision data available'}
        </div>
        <div class="decision-actions">
            <button class="action-button" onclick="showEvidence()">Show Evidence</button>
            <button class="action-button" onclick="showReceipt()">Show Receipt</button>
        </div>
    </div>
    <script>
        function showEvidence() {
            vscode.postMessage({ command: 'showEvidence' });
        }
        function showReceipt() {
            vscode.postMessage({ command: 'showReceipt' });
        }
    </script>
</body>
</html>`;
    }

    private renderDecisionContent(decisionData: any): string {
        if (!decisionData) return 'No decision data available';
        
        return `
            <p><strong>Policy ID:</strong> ${decisionData.policyId || 'N/A'}</p>
            <p><strong>Snapshot Hash:</strong> ${decisionData.snapshotHash || 'N/A'}</p>
            <p><strong>Status:</strong> ${decisionData.status || 'N/A'}</p>
            <p><strong>Rationale:</strong> ${decisionData.rationale || 'N/A'}</p>
        `;
    }

    public dispose(): void {
        if (this.webviewPanel) {
            this.webviewPanel.dispose();
        }
    }
}
