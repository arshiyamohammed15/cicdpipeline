"use strict";
/**
 * Status Bar Manager for ZEROUI Extension
 * Following Constitution Rules:
 * - Rule 1: Do Exactly What's Asked (status bar with WARN message)
 * - Rule 4: Use Settings Files, Not Hardcoded Numbers
 * - Rule 8: Make Things Fast + Respect People's Time
 * - Rule 10: Be Honest About AI Decisions + Explain Clearly
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.StatusBarManager = void 0;
const vscode = require("vscode");
class StatusBarManager {
    constructor(decisionPanel, configManager) {
        this.decisionPanel = decisionPanel;
        this.configManager = configManager;
        // Rule 4: Get configuration from settings, not hardcoded
        const priority = this.configManager.getConfig('runtime_config', 'status_bar_priority', '100');
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, parseInt(priority));
    }
    initialize() {
        // Rule 1: Do Exactly What's Asked - Show WARN message
        this.updateStatus();
        // Set click handler to open decision panel
        this.statusBarItem.command = 'zeroui.showDecisionPanel';
        // Rule 4: Get tooltip from configuration
        const tooltip = this.configManager.getConfig('runtime_config', 'status_bar_tooltip', 'ZEROUI 2.0 Constitution Validator - Click for details');
        this.statusBarItem.tooltip = tooltip;
        // Show the status bar item
        this.statusBarItem.show();
    }
    updateStatus(document) {
        // Rule 4: Check if status bar should be shown from configuration
        const showStatusBar = this.configManager.getConfig('runtime_config', 'show_status_bar', 'true');
        if (showStatusBar !== 'true') {
            this.statusBarItem.hide();
            return;
        }
        // Rule 1: Do Exactly What's Asked - Always show WARN status
        // Rule 4: Get status text from configuration
        const statusText = this.configManager.getConfig('runtime_config', 'status_bar_text', '$(warning) ZEROUI WARN');
        this.statusBarItem.text = statusText;
        // Rule 4: Get colors from configuration
        const backgroundColor = this.configManager.getConfig('runtime_config', 'status_bar_background_color', 'statusBarItem.warningBackground');
        const textColor = this.configManager.getConfig('runtime_config', 'status_bar_text_color', 'statusBarItem.warningForeground');
        this.statusBarItem.backgroundColor = new vscode.ThemeColor(backgroundColor);
        this.statusBarItem.color = new vscode.ThemeColor(textColor);
        // Update tooltip with more details
        if (document) {
            const detailedTooltip = this.configManager.getConfig('runtime_config', 'status_bar_detailed_tooltip', `ZEROUI 2.0 Constitution Validator\nFile: ${document.fileName}\nStatus: WARN - Click for details`);
            this.statusBarItem.tooltip = detailedTooltip.replace('${fileName}', document.fileName);
        }
        else {
            this.statusBarItem.tooltip = this.configManager.getConfig('runtime_config', 'status_bar_tooltip', 'ZEROUI 2.0 Constitution Validator\nStatus: WARN - Click for details');
        }
    }
    dispose() {
        this.statusBarItem.dispose();
    }
}
exports.StatusBarManager = StatusBarManager;
//# sourceMappingURL=statusBarManager.js.map