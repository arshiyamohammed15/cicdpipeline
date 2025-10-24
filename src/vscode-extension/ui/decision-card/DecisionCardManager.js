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
exports.DecisionCardManager = void 0;
const vscode = __importStar(require("vscode"));
class DecisionCardManager {
    constructor() {
        // Initialize decision card manager
    }
    showDecisionCard(decisionData) {
        if (this.webviewPanel) {
            this.webviewPanel.reveal(vscode.ViewColumn.One);
            return;
        }
        this.webviewPanel = vscode.window.createWebviewPanel('zerouiDecisionCard', 'ZeroUI Decision Card', vscode.ViewColumn.One, {
            enableScripts: true,
            retainContextWhenHidden: true
        });
        this.webviewPanel.webview.html = this.getWebviewContent(decisionData);
        this.webviewPanel.onDidDispose(() => {
            this.webviewPanel = undefined;
        });
    }
    getWebviewContent(decisionData) {
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
    renderDecisionContent(decisionData) {
        if (!decisionData)
            return 'No decision data available';
        return `
            <p><strong>Policy ID:</strong> ${decisionData.policyId || 'N/A'}</p>
            <p><strong>Snapshot Hash:</strong> ${decisionData.snapshotHash || 'N/A'}</p>
            <p><strong>Status:</strong> ${decisionData.status || 'N/A'}</p>
            <p><strong>Rationale:</strong> ${decisionData.rationale || 'N/A'}</p>
        `;
    }
    dispose() {
        if (this.webviewPanel) {
            this.webviewPanel.dispose();
        }
    }
}
exports.DecisionCardManager = DecisionCardManager;
//# sourceMappingURL=DecisionCardManager.js.map