import * as vscode from 'vscode';
import { ReceiptStorageReader } from '../../shared/storage/ReceiptStorageReader';
import { ReceiptParser, DecisionReceipt, FeedbackReceipt } from '../../shared/receipt-parser/ReceiptParser';

export class ReceiptViewerManager implements vscode.Disposable {
    private webviewPanel: vscode.WebviewPanel | undefined;
    private receiptReader: ReceiptStorageReader;
    private receiptParser: ReceiptParser;

    constructor() {
        // Initialize receipt storage reader
        const zuRoot = vscode.workspace.getConfiguration('zeroui').get<string>('zuRoot') || process.env.ZU_ROOT || '';
        this.receiptReader = new ReceiptStorageReader(zuRoot || undefined);
        this.receiptParser = new ReceiptParser();
    }

    public async showReceiptViewer(receiptData?: DecisionReceipt | FeedbackReceipt): Promise<void> {
        // If no receipt data provided, try to load latest receipts
        if (!receiptData) {
            receiptData = await this.loadLatestReceipt();
        }

        if (this.webviewPanel) {
            this.webviewPanel.reveal(vscode.ViewColumn.Three);
            if (receiptData) {
                this.webviewPanel.webview.html = this.getWebviewContent(receiptData);
            }
            return;
        }

        this.webviewPanel = vscode.window.createWebviewPanel(
            'zerouiReceiptViewer',
            'ZeroUI Receipt Viewer',
            vscode.ViewColumn.Three,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        this.webviewPanel.webview.html = this.getWebviewContent(receiptData);

        this.webviewPanel.onDidDispose(() => {
            this.webviewPanel = undefined;
        });
    }

    /**
     * Load latest receipt from storage
     */
    private async loadLatestReceipt(): Promise<DecisionReceipt | FeedbackReceipt | undefined> {
        try {
            // Get repo ID from workspace or configuration
            const repoId = vscode.workspace.getConfiguration('zeroui').get<string>('repoId') ||
                          vscode.workspace.name ||
                          'default-repo';

            // Read latest receipts
            const receipts = await this.receiptReader.readLatestReceipts(repoId, 1);

            if (receipts.length > 0) {
                return receipts[0];
            }
        } catch (error) {
            console.error('Failed to load latest receipt:', error);
            vscode.window.showWarningMessage('Failed to load receipt from storage. Ensure ZU_ROOT is configured.');
        }

        return undefined;
    }

    /**
     * Load receipts for a specific date range
     */
    public async loadReceiptsInRange(startDate: Date, endDate: Date): Promise<Array<DecisionReceipt | FeedbackReceipt>> {
        try {
            const repoId = vscode.workspace.getConfiguration('zeroui').get<string>('repoId') ||
                          vscode.workspace.name ||
                          'default-repo';

            return await this.receiptReader.readReceiptsInRange(repoId, startDate, endDate);
        } catch (error) {
            console.error('Failed to load receipts:', error);
            vscode.window.showErrorMessage('Failed to load receipts from storage');
            return [];
        }
    }

    private getWebviewContent(receiptData?: any): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZeroUI Receipt Viewer</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 20px;
        }
        .receipt-viewer {
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            padding: 16px;
        }
        .receipt-header {
            font-weight: bold;
            margin-bottom: 16px;
        }
        .receipt-field {
            margin-bottom: 8px;
            padding: 4px 0;
        }
        .receipt-label {
            font-weight: bold;
            display: inline-block;
            width: 150px;
        }
        .receipt-value {
            font-family: var(--vscode-editor-font-family);
            background-color: var(--vscode-textBlockQuote-background);
            padding: 4px 8px;
            border-radius: 4px;
            word-break: break-all;
        }
        .copy-button {
            padding: 4px 8px;
            border: 1px solid var(--vscode-button-border);
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border-radius: 4px;
            cursor: pointer;
            margin-left: 8px;
        }
        .copy-button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }
    </style>
</head>
<body>
    <div class="receipt-viewer">
        <div class="receipt-header">ZeroUI Receipt Viewer</div>
        <div class="receipt-content">
            ${receiptData ? this.renderReceiptContent(receiptData) : 'No receipt data available'}
        </div>
    </div>
    <script>
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                alert('Copied to clipboard!');
            });
        }
    </script>
</body>
</html>`;
    }

    private renderReceiptContent(receiptData: any): string {
        if (!receiptData) return 'No receipt data available';

        const contextParts = receiptData.context
            ? [
                  receiptData.context.surface ? `surface=${receiptData.context.surface}` : undefined,
                  receiptData.context.branch ? `branch=${receiptData.context.branch}` : undefined,
                  receiptData.context.commit ? `commit=${receiptData.context.commit}` : undefined,
                  receiptData.context.pr_id ? `pr=${receiptData.context.pr_id}` : undefined
              ].filter(Boolean).join(' · ')
            : '';

        const overrideParts = receiptData.override
            ? [
                  receiptData.override.reason ? `reason=${receiptData.override.reason}` : undefined,
                  receiptData.override.approver ? `approver=${receiptData.override.approver}` : undefined,
                  receiptData.override.timestamp ? `timestamp=${receiptData.override.timestamp}` : undefined,
                  receiptData.override.override_id ? `id=${receiptData.override.override_id}` : undefined
              ].filter(Boolean).join(' · ')
            : '';

        const fields = [
            { label: 'Receipt ID', value: receiptData.receipt_id },
            { label: 'Gate ID', value: receiptData.gate_id },
            { label: 'Policy Version IDs', value: receiptData.policy_version_ids?.join(', ') },
            { label: 'Snapshot Hash', value: receiptData.snapshot_hash },
            { label: 'Timestamp UTC', value: receiptData.timestamp_utc },
            { label: 'Status', value: receiptData.decision?.status },
            { label: 'Rationale', value: receiptData.decision?.rationale },
            { label: 'Badges', value: receiptData.decision?.badges?.join(', ') },
            { label: 'Actor', value: receiptData.actor?.repo_id },
            { label: 'Actor Type', value: receiptData.actor?.type },
            { label: 'Data Category', value: receiptData.data_category },
            { label: 'Context', value: contextParts },
            { label: 'Override', value: overrideParts },
            { label: 'Degraded', value: receiptData.degraded?.toString() },
            { label: 'Signature', value: receiptData.signature }
        ];

        return fields.map(field => `
            <div class="receipt-field">
                <span class="receipt-label">${field.label}:</span>
                <span class="receipt-value">${field.value || 'N/A'}</span>
                ${field.value ? `<button class="copy-button" onclick="copyToClipboard('${field.value}')">Copy</button>` : ''}
            </div>
        `).join('');
    }

    public dispose(): void {
        if (this.webviewPanel) {
            this.webviewPanel.dispose();
        }
    }
}
