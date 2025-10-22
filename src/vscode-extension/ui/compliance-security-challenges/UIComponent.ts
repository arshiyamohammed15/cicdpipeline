import { ComplianceSecurityData } from './types';

export class ComplianceSecurityUIComponent {
    public renderDashboard(data?: ComplianceSecurityData): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZeroUI Compliance & Security Dashboard</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 20px;
        }
        .dashboard {
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            padding: 16px;
        }
        .dashboard-header {
            font-weight: bold;
            margin-bottom: 16px;
            color: var(--vscode-textLink-foreground);
        }
        .security-card {
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            padding: 12px;
            margin-bottom: 12px;
            background-color: var(--vscode-textBlockQuote-background);
        }
        .security-label {
            font-weight: bold;
            margin-bottom: 4px;
        }
        .security-value {
            font-size: 1.2em;
            color: var(--vscode-textLink-foreground);
        }
        .security-status {
            font-size: 0.9em;
            color: var(--vscode-descriptionForeground);
        }
        .compliance-item {
            margin-bottom: 8px;
            padding: 8px;
            border-left: 3px solid var(--vscode-textLink-foreground);
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="dashboard-header">ZeroUI Compliance & Security Dashboard</div>
        <div class="dashboard-content">
            ${data ? this.renderComplianceSecurityContent(data) : 'No compliance data available'}
        </div>
    </div>
</body>
</html>`;
    }

    private renderComplianceSecurityContent(data: ComplianceSecurityData): string {
        return `
            <div class="security-card">
                <div class="security-label">Security Score</div>
                <div class="security-value">${data.securityScore || 0}%</div>
                <div class="security-status">Status: ${data.securityStatus || 'Unknown'}</div>
            </div>
            <div class="security-card">
                <div class="security-label">Compliance Level</div>
                <div class="security-value">${data.complianceLevel || 'Unknown'}</div>
                <div class="security-status">Last Check: ${data.lastComplianceCheck || 'N/A'}</div>
            </div>
            <div class="compliance-item">
                <strong>Security Challenges:</strong> ${data.securityChallenges || 'None identified'}
            </div>
            <div class="compliance-item">
                <strong>Compliance Issues:</strong> ${data.complianceIssues || 'None identified'}
            </div>
        `;
    }
}
