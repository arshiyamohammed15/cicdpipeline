"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MMMEngineUIComponent = void 0;
class MMMEngineUIComponent {
    renderDashboard(data) {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZeroUI MMM Engine Dashboard</title>
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
        .metric-card {
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            padding: 12px;
            margin-bottom: 12px;
            background-color: var(--vscode-textBlockQuote-background);
        }
        .metric-label {
            font-weight: bold;
            margin-bottom: 4px;
        }
        .metric-value {
            font-size: 1.2em;
            color: var(--vscode-textLink-foreground);
        }
        .metric-trend {
            font-size: 0.9em;
            color: var(--vscode-descriptionForeground);
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="dashboard-header">ZeroUI MMM Engine Dashboard</div>
        <div class="dashboard-content">
            ${data ? this.renderMMMEngineContent(data) : 'No MMM Engine data available'}
        </div>
    </div>
</body>
</html>`;
    }
    renderMMMEngineContent(data) {
        return `
            <div class="metric-card">
                <div class="metric-label">Metrics Collected</div>
                <div class="metric-value">${data.metricsCollected || 0}</div>
                <div class="metric-trend">Trend: ${data.metricsTrend || 'N/A'}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Measurements</div>
                <div class="metric-value">${data.measurements || 0}</div>
                <div class="metric-trend">Trend: ${data.measurementsTrend || 'N/A'}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Monitoring Status</div>
                <div class="metric-value">${data.monitoringStatus || 'Unknown'}</div>
                <div class="metric-trend">Last Update: ${data.lastUpdate || 'N/A'}</div>
            </div>
        `;
    }
}
exports.MMMEngineUIComponent = MMMEngineUIComponent;
//# sourceMappingURL=UIComponent.js.map