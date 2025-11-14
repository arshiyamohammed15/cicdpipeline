/**
 * UI Component Manager for Configuration & Policy Management.
 *
 * Per PRD: Manages webview panels and receipt data updates.
 * All rendering is receipt-driven with no business logic.
 */

import * as vscode from 'vscode';
import { ConfigurationPolicyManagementUIComponent } from './UIComponent';
import {
    PolicyLifecycleReceipt,
    ConfigurationChangeReceipt,
    ComplianceCheckReceipt
} from './types';

export class ConfigurationPolicyManagementUIComponentManager {
    private dashboardPanel: vscode.WebviewPanel | undefined;
    private policyManagementPanel: vscode.WebviewPanel | undefined;
    private configurationManagementPanel: vscode.WebviewPanel | undefined;
    private complianceReportingPanel: vscode.WebviewPanel | undefined;
    private lastReceiptData: unknown;

    constructor() {
        this.lastReceiptData = undefined;
    }

    /**
     * Show dashboard view per PRD.
     */
    public showDashboard(): void {
        if (this.dashboardPanel) {
            this.dashboardPanel.reveal();
            return;
        }

        this.dashboardPanel = vscode.window.createWebviewPanel(
            'configurationPolicyManagementDashboard',
            'Configuration & Policy Management Dashboard',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        this.dashboardPanel.webview.html = ConfigurationPolicyManagementUIComponent.renderDashboard(this.lastReceiptData);

        this.dashboardPanel.onDidDispose(() => {
            this.dashboardPanel = undefined;
        });
    }

    /**
     * Show policy management view per PRD.
     */
    public showPolicyManagement(receipt?: PolicyLifecycleReceipt): void {
        if (this.policyManagementPanel) {
            this.policyManagementPanel.reveal();
            if (receipt) {
                this.updatePolicyManagementData(receipt);
            }
            return;
        }

        this.policyManagementPanel = vscode.window.createWebviewPanel(
            'configurationPolicyManagementPolicy',
            'Policy Management',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        this.policyManagementPanel.webview.html = ConfigurationPolicyManagementUIComponent.renderPolicyManagement(receipt);

        this.policyManagementPanel.onDidDispose(() => {
            this.policyManagementPanel = undefined;
        });
    }

    /**
     * Show configuration management view per PRD.
     */
    public showConfigurationManagement(receipt?: ConfigurationChangeReceipt): void {
        if (this.configurationManagementPanel) {
            this.configurationManagementPanel.reveal();
            if (receipt) {
                this.updateConfigurationManagementData(receipt);
            }
            return;
        }

        this.configurationManagementPanel = vscode.window.createWebviewPanel(
            'configurationPolicyManagementConfig',
            'Configuration Management',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        this.configurationManagementPanel.webview.html = ConfigurationPolicyManagementUIComponent.renderConfigurationManagement(receipt);

        this.configurationManagementPanel.onDidDispose(() => {
            this.configurationManagementPanel = undefined;
        });
    }

    /**
     * Show compliance reporting view per PRD.
     */
    public showComplianceReporting(receipt?: ComplianceCheckReceipt): void {
        if (this.complianceReportingPanel) {
            this.complianceReportingPanel.reveal();
            if (receipt) {
                this.updateComplianceReportingData(receipt);
            }
            return;
        }

        this.complianceReportingPanel = vscode.window.createWebviewPanel(
            'configurationPolicyManagementCompliance',
            'Compliance Reporting',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        this.complianceReportingPanel.webview.html = ConfigurationPolicyManagementUIComponent.renderComplianceReporting(receipt);

        this.complianceReportingPanel.onDidDispose(() => {
            this.complianceReportingPanel = undefined;
        });
    }

    /**
     * Update policy management data from receipt.
     *
     * @param receipt Policy lifecycle receipt from Tier 3
     */
    public updatePolicyManagementData(receipt: PolicyLifecycleReceipt): void {
        this.lastReceiptData = receipt;
        if (this.policyManagementPanel) {
            this.policyManagementPanel.webview.html = ConfigurationPolicyManagementUIComponent.renderPolicyManagement(receipt);
        }
    }

    /**
     * Update configuration management data from receipt.
     *
     * @param receipt Configuration change receipt from Tier 3
     */
    public updateConfigurationManagementData(receipt: ConfigurationChangeReceipt): void {
        this.lastReceiptData = receipt;
        if (this.configurationManagementPanel) {
            this.configurationManagementPanel.webview.html = ConfigurationPolicyManagementUIComponent.renderConfigurationManagement(receipt);
        }
    }

    /**
     * Update compliance reporting data from receipt.
     *
     * @param receipt Compliance check receipt from Tier 3
     */
    public updateComplianceReportingData(receipt: ComplianceCheckReceipt): void {
        this.lastReceiptData = receipt;
        if (this.complianceReportingPanel) {
            this.complianceReportingPanel.webview.html = ConfigurationPolicyManagementUIComponent.renderComplianceReporting(receipt);
        }
    }

    /**
     * Handle degraded mode gracefully per PRD.
     */
    public handleDegradedMode(): void {
        // In degraded mode, show placeholder or cached data
        if (this.dashboardPanel) {
            this.dashboardPanel.webview.html = ConfigurationPolicyManagementUIComponent.renderDashboard();
        }
    }

    public dispose(): void {
        this.dashboardPanel?.dispose();
        this.policyManagementPanel?.dispose();
        this.configurationManagementPanel?.dispose();
        this.complianceReportingPanel?.dispose();
        this.lastReceiptData = undefined;
    }
}
