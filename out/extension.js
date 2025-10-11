"use strict";
/**
 * ZEROUI 2.0 Constitution Validator Extension
 * Following Constitution Rules:
 * - Rule 1: Do Exactly What's Asked
 * - Rule 4: Use Settings Files, Not Hardcoded Numbers
 * - Rule 5: Keep Good Records + Keep Good Logs
 * - Rule 8: Make Things Fast + Respect People's Time
 * - Rule 10: Be Honest About AI Decisions + Explain Clearly
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = require("vscode");
const constitutionValidator_1 = require("./constitutionValidator");
const decisionPanel_1 = require("./decisionPanel");
const statusBarManager_1 = require("./statusBarManager");
const configManager_1 = require("./configManager");
function activate(context) {
    // Rule 5: Keep Good Records + Logs
    console.log('ZEROUI 2.0 Constitution Validator extension is now active!');
    // Rule 4: Use Settings Files, Not Hardcoded Numbers
    const configManager = new configManager_1.ConfigManager();
    // Initialize components with configuration
    const validator = new constitutionValidator_1.ConstitutionValidator(configManager);
    const decisionPanel = new decisionPanel_1.DecisionPanel(validator, configManager);
    const statusBarManager = new statusBarManager_1.StatusBarManager(decisionPanel, configManager);
    // Register commands
    const showDecisionPanelCommand = vscode.commands.registerCommand('zeroui.showDecisionPanel', () => {
        decisionPanel.show();
    });
    const validateFileCommand = vscode.commands.registerCommand('zeroui.validateFile', () => {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            validator.validateFile(editor.document);
        }
        else {
            vscode.window.showWarningMessage('No active editor found');
        }
    });
    const validateWorkspaceCommand = vscode.commands.registerCommand('zeroui.validateWorkspace', () => {
        validator.validateWorkspace();
    });
    // Rule 8: Make Things Fast - Auto-validate on save if enabled
    const onSaveListener = vscode.workspace.onDidSaveTextDocument((document) => {
        const autoValidate = configManager.getConfig('runtime_config', 'auto_validate', 'false');
        if (autoValidate === 'true') {
            validator.validateFile(document);
        }
    });
    // Update status bar when active editor changes
    const onActiveEditorChange = vscode.window.onDidChangeActiveTextEditor((editor) => {
        if (editor) {
            statusBarManager.updateStatus(editor.document);
        }
    });
    // Initialize status bar
    statusBarManager.initialize();
    // Add to subscriptions
    context.subscriptions.push(showDecisionPanelCommand, validateFileCommand, validateWorkspaceCommand, onSaveListener, onActiveEditorChange, statusBarManager);
}
exports.activate = activate;
function deactivate() {
    // Rule 5: Keep Good Records + Logs
    console.log('ZEROUI 2.0 Constitution Validator extension is now deactivated');
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map