"use strict";
/**
 * Decision Panel for ZEROUI Extension
 * Following Constitution Rules:
 * - Rule 1: Do Exactly What's Asked (decision panel when status bar clicked)
 * - Rule 4: Use Settings Files, Not Hardcoded Numbers
 * - Rule 5: Keep Good Records + Keep Good Logs
 * - Rule 10: Be Honest About AI Decisions + Explain Clearly
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.DecisionPanel = void 0;
const vscode = require("vscode");
class DecisionPanel {
    constructor(validator, configManager) {
        this.validator = validator;
        this.configManager = configManager;
    }
    show() {
        if (this.panel) {
            this.panel.reveal(vscode.ViewColumn.One);
            return;
        }
        // Rule 4: Get panel configuration from settings
        const panelTitle = this.configManager.getConfig('runtime_config', 'decision_panel_title', 'ZEROUI 2.0 Constitution Decision Panel');
        // Create and show a new webview panel
        this.panel = vscode.window.createWebviewPanel('zerouiDecisionPanel', panelTitle, vscode.ViewColumn.One, {
            enableScripts: true,
            retainContextWhenHidden: true
        });
        // Set the webview's initial html content
        this.panel.webview.html = this.getWebviewContent();
        // Handle messages from the webview
        this.panel.webview.onDidReceiveMessage(message => {
            switch (message.command) {
                case 'validateFile':
                    this.handleValidateFile();
                    break;
                case 'validateWorkspace':
                    this.handleValidateWorkspace();
                    break;
                case 'showRule':
                    this.handleShowRule(message.ruleNumber);
                    break;
                case 'updateConfig':
                    this.handleUpdateConfig(message.key, message.value);
                    break;
            }
        }, undefined, []);
        // Clean up when the panel is closed
        this.panel.onDidDispose(() => {
            this.panel = undefined;
        }, null, []);
    }
    getWebviewContent() {
        // Rule 4: Get configuration values for the webview
        const statusMessage = this.configManager.getConfig('runtime_config', 'decision_panel_status_message', 'Constitution validation detected potential issues. Review the violations below and take appropriate action.');
        const enableValidation = this.configManager.getConfig('runtime_config', 'enable_validation', 'true');
        const autoValidate = this.configManager.getConfig('runtime_config', 'auto_validate', 'false');
        const severityLevel = this.configManager.getConfig('runtime_config', 'severity_level', 'warning');
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZEROUI 2.0 Constitution Decision Panel</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 20px;
            margin: 0;
        }
        .header {
            border-bottom: 1px solid var(--vscode-panel-border);
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .header h1 {
            margin: 0;
            color: var(--vscode-textLink-foreground);
        }
        .status {
            background-color: var(--vscode-inputValidation-warningBackground);
            border: 1px solid var(--vscode-inputValidation-warningBorder);
            color: var(--vscode-inputValidation-warningForeground);
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .actions {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        button {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: var(--vscode-font-size);
        }
        button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }
        .config-section {
            background-color: var(--vscode-editor-background);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .config-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .config-item:last-child {
            margin-bottom: 0;
        }
        .config-label {
            font-weight: bold;
        }
        .config-value {
            color: var(--vscode-descriptionForeground);
        }
        .rules-section {
            margin-top: 20px;
        }
        .rule-item {
            background-color: var(--vscode-editor-background);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            padding: 10px;
            margin-bottom: 10px;
            cursor: pointer;
        }
        .rule-item:hover {
            background-color: var(--vscode-list-hoverBackground);
        }
        .rule-number {
            font-weight: bold;
            color: var(--vscode-textLink-foreground);
        }
        .rule-title {
            margin: 5px 0;
        }
        .rule-description {
            color: var(--vscode-descriptionForeground);
            font-size: 0.9em;
        }
        .violations {
            margin-top: 20px;
        }
        .violation-item {
            background-color: var(--vscode-inputValidation-errorBackground);
            border: 1px solid var(--vscode-inputValidation-errorBorder);
            color: var(--vscode-inputValidation-errorForeground);
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .violation-rule {
            font-weight: bold;
        }
        .violation-message {
            margin: 5px 0;
        }
        .violation-suggestion {
            color: var(--vscode-descriptionForeground);
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>ZEROUI 2.0 Constitution Decision Panel</h1>
    </div>
    
    <div class="status">
        <strong>Status: WARN</strong><br>
        ${statusMessage}
    </div>
    
    <div class="actions">
        <button onclick="validateFile()">Validate Current File</button>
        <button onclick="validateWorkspace()">Validate Workspace</button>
        <button onclick="refreshPanel()">Refresh</button>
    </div>
    
    <div class="config-section">
        <h3>Current Configuration</h3>
        <div class="config-item">
            <span class="config-label">Enable Validation:</span>
            <span class="config-value">${enableValidation}</span>
        </div>
        <div class="config-item">
            <span class="config-label">Auto Validate:</span>
            <span class="config-value">${autoValidate}</span>
        </div>
        <div class="config-item">
            <span class="config-label">Severity Level:</span>
            <span class="config-value">${severityLevel}</span>
        </div>
    </div>
    
    <div class="rules-section">
        <h2>Constitution Rules Overview</h2>
        <div class="rule-item" onclick="showRule(1)">
            <div class="rule-number">Rule 1</div>
            <div class="rule-title">Do Exactly What's Asked</div>
            <div class="rule-description">Follow instructions exactly without adding your own ideas</div>
        </div>
        <div class="rule-item" onclick="showRule(2)">
            <div class="rule-number">Rule 2</div>
            <div class="rule-title">Only Use Information You're Given</div>
            <div class="rule-description">Don't guess or make up amounts - ask for clarification</div>
        </div>
        <div class="rule-item" onclick="showRule(3)">
            <div class="rule-number">Rule 3</div>
            <div class="rule-title">Protect People's Privacy</div>
            <div class="rule-description">Treat personal information like a secret diary</div>
        </div>
        <div class="rule-item" onclick="showRule(4)">
            <div class="rule-number">Rule 4</div>
            <div class="rule-title">Use Settings Files + Easy Undo</div>
            <div class="rule-description">No hardcoded numbers, prefer adding features over changing old ones</div>
        </div>
        <div class="rule-item" onclick="showRule(5)">
            <div class="rule-number">Rule 5</div>
            <div class="rule-title">Keep Good Records + Logs</div>
            <div class="rule-description">Write down what you did, when, and what happened</div>
        </div>
        <div class="rule-item" onclick="showRule(7)">
            <div class="rule-number">Rule 7</div>
            <div class="rule-title">Never Break Things During Updates</div>
            <div class="rule-description">Updates should allow instant rollback if problems occur</div>
        </div>
        <div class="rule-item" onclick="showRule(8)">
            <div class="rule-number">Rule 8</div>
            <div class="rule-title">Make Things Fast + Respect Time</div>
            <div class="rule-description">Programs should start faster than microwaving popcorn</div>
        </div>
        <div class="rule-item" onclick="showRule(10)">
            <div class="rule-number">Rule 10</div>
            <div class="rule-title">Be Honest About AI Decisions</div>
            <div class="rule-description">Show confidence levels, explanations, and model versions</div>
        </div>
    </div>
    
    <div class="violations">
        <h2>Current Violations</h2>
        <div class="violation-item">
            <div class="violation-rule">Rule 4: Use Settings Files</div>
            <div class="violation-message">Hardcoded values detected in configuration</div>
            <div class="violation-suggestion">Move hardcoded values to configuration files</div>
        </div>
        <div class="violation-item">
            <div class="violation-rule">Rule 5: Keep Good Records</div>
            <div class="violation-message">Missing logging patterns detected</div>
            <div class="violation-suggestion">Add proper logging for monitoring and debugging</div>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        
        function validateFile() {
            vscode.postMessage({
                command: 'validateFile'
            });
        }
        
        function validateWorkspace() {
            vscode.postMessage({
                command: 'validateWorkspace'
            });
        }
        
        function showRule(ruleNumber) {
            vscode.postMessage({
                command: 'showRule',
                ruleNumber: ruleNumber
            });
        }
        
        function refreshPanel() {
            location.reload();
        }
    </script>
</body>
</html>`;
    }
    handleValidateFile() {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            this.validator.validateFile(editor.document);
            vscode.window.showInformationMessage('File validation completed');
        }
        else {
            vscode.window.showWarningMessage('No active editor found');
        }
    }
    handleValidateWorkspace() {
        this.validator.validateWorkspace();
        vscode.window.showInformationMessage('Workspace validation completed');
    }
    handleShowRule(ruleNumber) {
        // Open constitution.md and highlight the specific rule
        vscode.workspace.openTextDocument(vscode.Uri.file('constitution.md')).then(doc => {
            vscode.window.showTextDocument(doc).then(editor => {
                // Find the rule in the document
                const text = doc.getText();
                const rulePattern = new RegExp(`### Rule ${ruleNumber}:`);
                const match = text.match(rulePattern);
                if (match) {
                    const position = doc.positionAt(match.index);
                    editor.selection = new vscode.Selection(position, position);
                    editor.revealRange(new vscode.Range(position, position));
                }
            });
        });
    }
    handleUpdateConfig(key, value) {
        // Rule 4: Update configuration through config manager
        this.configManager.setConfig('runtime_config', key, value, 'Updated from decision panel');
        vscode.window.showInformationMessage(`Configuration updated: ${key} = ${value}`);
    }
}
exports.DecisionPanel = DecisionPanel;
//# sourceMappingURL=decisionPanel.js.map