"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ReceiptViewerManager = void 0;
const vscode = __importStar(require("vscode"));
class ReceiptViewerManager {
    constructor() {
        // Initialize receipt viewer manager
    }
    showReceiptViewer(receiptData) {
        if (this.webviewPanel) {
            this.webviewPanel.reveal(vscode.ViewColumn.Three);
            return;
        }
        this.webviewPanel = vscode.window.createWebviewPanel('zerouiReceiptViewer', 'ZeroUI Receipt Viewer', vscode.ViewColumn.Three, {
            enableScripts: true,
            retainContextWhenHidden: true
        });
        this.webviewPanel.webview.html = this.getWebviewContent(receiptData);
        this.webviewPanel.onDidDispose(() => {
            this.webviewPanel = undefined;
        });
    }
    getWebviewContent(receiptData) {
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
    renderReceiptContent(receiptData) {
        if (!receiptData)
            return 'No receipt data available';
        const fields = [
            { label: 'Receipt ID', value: receiptData.receipt_id },
            { label: 'Gate ID', value: receiptData.gate_id },
            { label: 'Policy Version IDs', value: receiptData.policy_version_ids?.join(', ') },
            { label: 'Snapshot Hash', value: receiptData.snapshot_hash },
            { label: 'Timestamp UTC', value: receiptData.timestamp_utc },
            { label: 'Status', value: receiptData.decision?.status },
            { label: 'Rationale', value: receiptData.decision?.rationale },
            { label: 'Badges', value: receiptData.decision?.badges?.join(', ') },
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
    dispose() {
        if (this.webviewPanel) {
            this.webviewPanel.dispose();
        }
    }
}
exports.ReceiptViewerManager = ReceiptViewerManager;
//# sourceMappingURL=ReceiptViewerManager.js.map