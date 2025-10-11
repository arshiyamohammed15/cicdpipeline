/**
 * ZEROUI 2.0 Constitution Validator Extension
 * Following Constitution Rules:
 * - Rule 1: Do Exactly What's Asked
 * - Rule 4: Use Settings Files, Not Hardcoded Numbers
 * - Rule 5: Keep Good Records + Keep Good Logs
 * - Rule 8: Make Things Fast + Respect People's Time
 * - Rule 10: Be Honest About AI Decisions + Explain Clearly
 */

import * as vscode from 'vscode';
import { ConstitutionValidator } from './constitutionValidator';
import { DecisionPanel } from './decisionPanel';
import { StatusBarManager } from './statusBarManager';
import { ConfigManager } from './configManager';

export function activate(context: vscode.ExtensionContext) {
    // Rule 5: Keep Good Records + Logs
    console.log('ZEROUI 2.0 Constitution Validator extension is now active!');
    
    // Rule 4: Use Settings Files, Not Hardcoded Numbers
    const configManager = new ConfigManager();
    
    // Initialize components with configuration
    const validator = new ConstitutionValidator(configManager);
    const decisionPanel = new DecisionPanel(validator, configManager);
    const statusBarManager = new StatusBarManager(decisionPanel, configManager);

    // Register commands
    const showDecisionPanelCommand = vscode.commands.registerCommand('zeroui.showDecisionPanel', () => {
        decisionPanel.show();
    });

    const validateFileCommand = vscode.commands.registerCommand('zeroui.validateFile', () => {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            validator.validateFile(editor.document);
        } else {
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
    context.subscriptions.push(
        showDecisionPanelCommand,
        validateFileCommand,
        validateWorkspaceCommand,
        onSaveListener,
        onActiveEditorChange,
        statusBarManager
    );
}

export function deactivate() {
    // Rule 5: Keep Good Records + Logs
    console.log('ZEROUI 2.0 Constitution Validator extension is now deactivated');
}
