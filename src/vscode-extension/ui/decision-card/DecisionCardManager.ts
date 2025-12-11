import * as vscode from 'vscode';
import { MismatchInfo, PreCommitStatus } from '../../shared/storage/PreCommitDecisionService';
import { DecisionReceipt } from '../../shared/receipt-parser/ReceiptParser';
import { formatDecisionForDisplay, FormattedDecision } from '../../shared/transparency/TransparencyFormatter';

export interface DecisionCardData {
    status: PreCommitStatus;
    policySnapshotId?: string;
    artifactId?: string;
    rationale?: string;
    evaluationPoint?: string;
    actorType?: string;
    dataCategory?: string;
    context?: {
        surface?: 'ide' | 'pr' | 'ci';
        branch?: string;
        commit?: string;
        pr_id?: string;
    };
    override?: {
        reason: string;
        approver: string;
        timestamp: string;
        override_id?: string;
    };
    mismatches: MismatchInfo[];
    labels?: Record<string, unknown>;
    timestampUtc?: string;
}

export interface DecisionCardActions {
    onShowEvidence?: () => void;
    onShowReceipt?: () => void;
    onRerunPlan?: () => void;
    onOpenDiff?: () => void;
}

export class DecisionCardManager implements vscode.Disposable {
    private webviewPanel: vscode.WebviewPanel | undefined;
    private currentData: DecisionCardData | undefined;
    private currentActions: DecisionCardActions | undefined;
    private disposables: vscode.Disposable[] = [];

    public showDecisionCard(decisionData?: DecisionCardData, actions?: DecisionCardActions): void {
        this.currentData = decisionData;
        this.currentActions = actions;

        if (this.webviewPanel) {
            this.webviewPanel.reveal(vscode.ViewColumn.One);
            this.webviewPanel.webview.html = this.getWebviewContent(this.currentData);
            return;
        }

        this.webviewPanel = vscode.window.createWebviewPanel(
            'zerouiDecisionCard',
            'ZeroUI Decision Card',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        this.webviewPanel.webview.html = this.getWebviewContent(this.currentData);

        const messageSubscription = this.webviewPanel.webview.onDidReceiveMessage(message => {
            switch (message.command) {
                case 'showEvidence':
                    this.currentActions?.onShowEvidence?.();
                    break;
                case 'showReceipt':
                    this.currentActions?.onShowReceipt?.();
                    break;
                case 'rerunPlan':
                    this.currentActions?.onRerunPlan?.();
                    break;
                case 'openDiff':
                    this.currentActions?.onOpenDiff?.();
                    break;
                default:
                    break;
            }
        });
        this.disposables.push(messageSubscription);

        this.webviewPanel.onDidDispose(() => {
            this.webviewPanel = undefined;
            this.disposeSubscriptions();
        });
    }

    private getWebviewContent(decisionData?: DecisionCardData): string {
        const statusBadge = this.renderStatusBadge(decisionData?.status);
        // Use transparency formatting if available (TR-2.1.1, TR-2.1.2)
        const formatted = (decisionData as any)?.formatted as FormattedDecision | undefined;
        const decisionContent = decisionData 
            ? this.renderDecisionContentWithTransparency(decisionData, formatted) 
            : 'No decision data available';
        const quickFixButtons = this.renderQuickFixButtons(decisionData);

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
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .decision-content {
            margin-bottom: 12px;
        }
        .decision-actions, .quick-fixes {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 8px;
        }
        .action-button {
            padding: 6px 14px;
            border: 1px solid var(--vscode-button-border);
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border-radius: 4px;
            cursor: pointer;
        }
        .action-button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }
        .status-pill {
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        .status-pass {
            background-color: var(--vscode-testing-iconPassed, #0a8f08);
            color: #ffffff;
        }
        .status-warn {
            background-color: var(--vscode-testing-iconQueued, #b89600);
            color: #ffffff;
        }
        .status-block {
            background-color: var(--vscode-testing-iconFailed, #c13c3c);
            color: #ffffff;
        }
        .field-label {
            font-weight: 600;
        }
        ul {
            margin-top: 4px;
        }
        li {
            margin-bottom: 4px;
        }
        code {
            font-family: var(--vscode-editor-font-family);
        }
    </style>
</head>
<body>
    <div class="decision-card">
        <div class="decision-header">
            <span>ZeroUI Decision Card</span>
            ${statusBadge}
        </div>
        <div class="decision-content">
            ${decisionContent}
        </div>
        <div class="decision-actions">
            <button class="action-button" onclick="showEvidence()">Show Evidence</button>
            <button class="action-button" onclick="showReceipt()">Show Receipt</button>
        </div>
        <div class="quick-fixes">
            ${quickFixButtons}
        </div>
    </div>
    <script>
        const vscode = acquireVsCodeApi();
        function showEvidence() {
            vscode.postMessage({ command: 'showEvidence' });
        }
        function showReceipt() {
            vscode.postMessage({ command: 'showReceipt' });
        }
        function rerunPlan() {
            vscode.postMessage({ command: 'rerunPlan' });
        }
        function openDiff() {
            vscode.postMessage({ command: 'openDiff' });
        }
    </script>
</body>
</html>`;
    }

    private renderStatusBadge(status: PreCommitStatus | undefined): string {
        switch (status) {
            case 'pass':
                return `<span class="status-pill status-pass">PASS</span>`;
            case 'warn':
                return `<span class="status-pill status-warn">WARN</span>`;
            case 'soft_block':
            case 'hard_block':
                return `<span class="status-pill status-block">BLOCK</span>`;
            default:
                return `<span class="status-pill">READY</span>`;
        }
    }

    private renderDecisionContent(decisionData: DecisionCardData): string {
        const mismatches = decisionData.mismatches?.length
            ? `<div><span class="field-label">Mismatches:</span>
                <ul>${decisionData.mismatches
                    .map(
                        entry =>
                            `<li>${entry.path ? `<code>${entry.path}</code> – ` : ''}${entry.detail}</li>`
                    )
                    .join('')}</ul></div>`
            : `<div><span class="field-label">Mismatches:</span> None detected</div>`;

        return `
            <div><span class="field-label">Policy Snapshot:</span> ${decisionData.policySnapshotId ?? 'N/A'}</div>
            <div><span class="field-label">Artifact ID:</span> ${decisionData.artifactId ?? 'N/A'}</div>
            <div><span class="field-label">Status:</span> ${decisionData.status?.toUpperCase() ?? 'Unknown'}</div>
            <div><span class="field-label">Rationale:</span> ${decisionData.rationale ?? 'N/A'}</div>
            ${decisionData.timestampUtc ? `<div><span class="field-label">Timestamp:</span> ${decisionData.timestampUtc}</div>` : ''}
            ${mismatches}
        `;
    }

    /**
     * Show decision card from Decision Receipt (TR-2.1.3)
     * Uses transparency formatting for summary and "Why" explanation
     */
    public showDecisionCardFromReceipt(receipt: DecisionReceipt, actions?: DecisionCardActions): void {
        const formatted = formatDecisionForDisplay(receipt);
        
        // Convert DecisionReceipt to DecisionCardData format
        const decisionData: DecisionCardData = {
            status: receipt.decision.status as PreCommitStatus,
            policySnapshotId: receipt.snapshot_hash,
            rationale: formatted.summary, // Use formatted summary (TR-2.1.1)
            timestampUtc: receipt.timestamp_utc,
            evaluationPoint: receipt.evaluation_point,
            actorType: formatted.actorType,
            dataCategory: formatted.dataCategory,
            context: receipt.context,
            override: receipt.override,
            mismatches: [] // Mismatches would need to be extracted from receipt.inputs if available
        };

        // Store formatted data for display
        (decisionData as any).formatted = formatted;

        this.showDecisionCard(decisionData, actions);
    }

    /**
     * Render decision content with transparency formatting (TR-2.1.1, TR-2.1.2)
     */
    private renderDecisionContentWithTransparency(
        decisionData: DecisionCardData,
        formatted?: FormattedDecision
    ): string {
        // Use formatted summary and explanation if available (TR-2.1.1, TR-2.1.2)
        if (formatted) {
            return `
                <div class="decision-summary">
                    <div><span class="field-label">Summary:</span> ${formatted.summary}</div>
                    <div><span class="field-label">Why:</span> ${formatted.whyExplanation}</div>
                </div>
                <div class="decision-details">
                    <div><span class="field-label">Status:</span> ${formatted.status.toUpperCase()}</div>
                    <div><span class="field-label">Full Rationale:</span> ${formatted.rationale}</div>
                    ${decisionData.policySnapshotId ? `<div><span class="field-label">Policy Snapshot:</span> ${decisionData.policySnapshotId}</div>` : ''}
                    ${decisionData.evaluationPoint ? `<div><span class="field-label">Evaluation Point:</span> ${decisionData.evaluationPoint}</div>` : ''}
                    ${decisionData.actorType ? `<div><span class="field-label">Actor Type:</span> ${decisionData.actorType}</div>` : ''}
                    ${decisionData.dataCategory ? `<div><span class="field-label">Data Category:</span> ${decisionData.dataCategory}</div>` : ''}
                    ${this.renderContext(decisionData.context)}
                    ${this.renderOverride(decisionData.override)}
                    ${decisionData.timestampUtc ? `<div><span class="field-label">Timestamp:</span> ${decisionData.timestampUtc}</div>` : ''}
                </div>
            `;
        }

        // Fallback to original rendering
        return this.renderDecisionContent(decisionData);
    }

    private renderContext(context?: DecisionCardData['context']): string {
        if (!context) {
            return '';
        }

        const parts = [
            context.surface ? `surface=${context.surface}` : undefined,
            context.branch ? `branch=${context.branch}` : undefined,
            context.commit ? `commit=${context.commit}` : undefined,
            context.pr_id ? `pr=${context.pr_id}` : undefined
        ].filter(Boolean);

        if (parts.length === 0) {
            return '';
        }

        return `<div><span class="field-label">Context:</span> ${parts.join(' · ')}</div>`;
    }

    private renderOverride(override?: DecisionCardData['override']): string {
        if (!override) {
            return '';
        }

        return `
            <div><span class="field-label">Override:</span> reason=${override.reason}; approver=${override.approver}; timestamp=${override.timestamp}${override.override_id ? `; id=${override.override_id}` : ''}</div>
        `;
    }

    private renderQuickFixButtons(decisionData?: DecisionCardData): string {
        const rerunButton = `<button class="action-button" onclick="rerunPlan()">Re-run PSCL Plan</button>`;
        const diffButton =
            decisionData?.mismatches?.length
                ? `<button class="action-button" onclick="openDiff()">Open Diff (first mismatch)</button>`
                : '';

        return `${rerunButton}${diffButton}`;
    }

    private disposeSubscriptions(): void {
        this.disposables.forEach(disposable => disposable.dispose());
        this.disposables = [];
    }

    public dispose(): void {
        if (this.webviewPanel) {
            this.webviewPanel.dispose();
        }
        this.disposeSubscriptions();
    }
}
