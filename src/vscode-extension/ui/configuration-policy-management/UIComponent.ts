/**
 * UI Component for Configuration & Policy Management.
 *
 * Per PRD: All UI rendering is receipt-driven with no business logic.
 * Receipts flow from Tier 3 → Tier 2 → Tier 1 for UI rendering.
 */

import * as vscode from 'vscode';
import {
    PolicyLifecycleReceipt,
    ConfigurationChangeReceipt,
    PolicyEvaluationDecisionReceipt,
    ComplianceCheckReceipt,
    RemediationActionReceipt
} from './types';

export class ConfigurationPolicyManagementUIComponent {
    /**
     * Render dashboard view per PRD.
     *
     * @param receiptData Receipt data from Tier 3
     * @returns HTML content for webview
     */
    public static renderDashboard(receiptData?: unknown): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Configuration & Policy Management Dashboard</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 20px;
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .card {
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            padding: 16px;
            background-color: var(--vscode-editor-background);
        }
        .card-title {
            font-weight: bold;
            margin-bottom: 12px;
            font-size: 1.1em;
        }
        .card-content {
            color: var(--vscode-descriptionForeground);
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="card">
            <div class="card-title">Policy Management</div>
            <div class="card-content">View and manage policies</div>
        </div>
        <div class="card">
            <div class="card-title">Configuration Management</div>
            <div class="card-content">View and manage configurations</div>
        </div>
        <div class="card">
            <div class="card-title">Compliance Reporting</div>
            <div class="card-content">View compliance status</div>
        </div>
    </div>
</body>
</html>`;
    }

    /**
     * Render policy management view per PRD.
     *
     * @param receipt Receipt data from Tier 3
     * @returns HTML content for webview
     */
    public static renderPolicyManagement(receipt?: PolicyLifecycleReceipt): string {
        const receiptHtml = receipt ? this.renderPolicyLifecycleReceipt(receipt) : '<p>No policy data available</p>';

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Policy Management</title>
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
    </style>
</head>
<body>
    <div class="receipt-viewer">
        <h2>Policy Management</h2>
        ${receiptHtml}
    </div>
</body>
</html>`;
    }

    /**
     * Render configuration management view per PRD.
     *
     * @param receipt Receipt data from Tier 3
     * @returns HTML content for webview
     */
    public static renderConfigurationManagement(receipt?: ConfigurationChangeReceipt): string {
        const receiptHtml = receipt ? this.renderConfigurationChangeReceipt(receipt) : '<p>No configuration data available</p>';

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Configuration Management</title>
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
    </style>
</head>
<body>
    <div class="receipt-viewer">
        <h2>Configuration Management</h2>
        ${receiptHtml}
    </div>
</body>
</html>`;
    }

    /**
     * Render compliance reporting view per PRD.
     *
     * @param receipt Receipt data from Tier 3
     * @returns HTML content for webview
     */
    public static renderComplianceReporting(receipt?: ComplianceCheckReceipt): string {
        const receiptHtml = receipt ? this.renderComplianceCheckReceipt(receipt) : '<p>No compliance data available</p>';

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Compliance Reporting</title>
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
    </style>
</head>
<body>
    <div class="receipt-viewer">
        <h2>Compliance Reporting</h2>
        ${receiptHtml}
    </div>
</body>
</html>`;
    }

    private static renderPolicyLifecycleReceipt(receipt: PolicyLifecycleReceipt): string {
        return `
            <div class="receipt-field">
                <strong>Policy ID:</strong> ${receipt.result.policy_id}
            </div>
            <div class="receipt-field">
                <strong>Status:</strong> ${receipt.result.status}
            </div>
            <div class="receipt-field">
                <strong>Operation:</strong> ${receipt.inputs.operation}
            </div>
            <div class="receipt-field">
                <strong>Decision:</strong> ${receipt.decision.status}
            </div>
            <div class="receipt-field">
                <strong>Rationale:</strong> ${receipt.decision.rationale}
            </div>
        `;
    }

    private static renderConfigurationChangeReceipt(receipt: ConfigurationChangeReceipt): string {
        return `
            <div class="receipt-field">
                <strong>Config ID:</strong> ${receipt.result.config_id}
            </div>
            <div class="receipt-field">
                <strong>Status:</strong> ${receipt.result.status}
            </div>
            <div class="receipt-field">
                <strong>Operation:</strong> ${receipt.inputs.operation}
            </div>
            <div class="receipt-field">
                <strong>Drift Detected:</strong> ${receipt.result.drift_detected ? 'Yes' : 'No'}
            </div>
        `;
    }

    private static renderComplianceCheckReceipt(receipt: ComplianceCheckReceipt): string {
        return `
            <div class="receipt-field">
                <strong>Framework:</strong> ${receipt.result.framework}
            </div>
            <div class="receipt-field">
                <strong>Compliant:</strong> ${receipt.result.compliant ? 'Yes' : 'No'}
            </div>
            <div class="receipt-field">
                <strong>Score:</strong> ${receipt.result.score}%
            </div>
            <div class="receipt-field">
                <strong>Controls Evaluated:</strong> ${receipt.result.controls_evaluated}
            </div>
            <div class="receipt-field">
                <strong>Controls Passing:</strong> ${receipt.result.controls_passing}
            </div>
            <div class="receipt-field">
                <strong>Controls Failing:</strong> ${receipt.result.controls_failing}
            </div>
        `;
    }
}
