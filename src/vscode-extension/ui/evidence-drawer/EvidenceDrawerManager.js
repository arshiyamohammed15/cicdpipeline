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
exports.EvidenceDrawerManager = void 0;
const vscode = __importStar(require("vscode"));
class EvidenceDrawerManager {
    constructor() {
        // Initialize evidence drawer manager
    }
    showEvidenceDrawer(evidenceData) {
        if (this.webviewPanel) {
            this.webviewPanel.reveal(vscode.ViewColumn.Two);
            return;
        }
        this.webviewPanel = vscode.window.createWebviewPanel('zerouiEvidenceDrawer', 'ZeroUI Evidence Drawer', vscode.ViewColumn.Two, {
            enableScripts: true,
            retainContextWhenHidden: true
        });
        this.webviewPanel.webview.html = this.getWebviewContent(evidenceData);
        this.webviewPanel.onDidDispose(() => {
            this.webviewPanel = undefined;
        });
    }
    getWebviewContent(evidenceData) {
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
    renderEvidenceContent(evidenceData) {
        if (!evidenceData || !evidenceData.evidenceHandles) {
            return 'No evidence data available';
        }
        return evidenceData.evidenceHandles.map((handle, index) => `
            <div class="evidence-item">
                <strong>Evidence ${index + 1}:</strong>
                <a href="${handle.url}" class="evidence-link" target="_blank">${handle.description || 'View Evidence'}</a>
                <p><small>Type: ${handle.type || 'Unknown'}</small></p>
            </div>
        `).join('');
    }
    dispose() {
        if (this.webviewPanel) {
            this.webviewPanel.dispose();
        }
    }
}
exports.EvidenceDrawerManager = EvidenceDrawerManager;
//# sourceMappingURL=EvidenceDrawerManager.js.map