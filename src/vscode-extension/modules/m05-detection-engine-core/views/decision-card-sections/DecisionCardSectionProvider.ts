/**
 * Detection Engine Core Decision Card Section Provider
 * 
 * Implements decision card sections per PRD Section 3.8
 */

import * as vscode from 'vscode';
import { ReceiptStorageReader } from '../../../../shared/storage/ReceiptStorageReader';
import { DecisionReceipt, EvidenceHandle } from '../../../../shared/receipt-parser/ReceiptParser';

export interface CoreDeps {
    context: vscode.ExtensionContext;
    receiptReader?: ReceiptStorageReader;
    ipcClient?: any;
}

export class DecisionCardSectionProvider {
    private receiptReader?: ReceiptStorageReader;

    async initialize(deps: CoreDeps): Promise<void> {
        if (deps.receiptReader) {
            this.receiptReader = deps.receiptReader;
        } else {
            const zuRoot = vscode.workspace.getConfiguration('zeroui').get<string>('zuRoot') || 
                          process.env.ZU_ROOT || 
                          undefined;
            this.receiptReader = new ReceiptStorageReader(zuRoot);
        }
    }

    private getWorkspaceRepoId(): string {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            return 'default-repo';
        }
        return workspaceFolder.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    }

    private async getLatestReceipt(): Promise<DecisionReceipt | null> {
        try {
            if (!this.receiptReader) {
                return null;
            }

            const repoId = this.getWorkspaceRepoId();
            const now = new Date();
            const year = now.getFullYear();
            const month = now.getMonth() + 1;
            
            const receipts = await this.receiptReader.readReceipts(repoId, year, month);
            
            const latestReceipt = receipts
                .filter(r => this.isDetectionEngineReceipt(r))
                .sort((a, b) => {
                    const aTime = (a as any).timestamp_utc || '';
                    const bTime = (b as any).timestamp_utc || '';
                    return bTime.localeCompare(aTime);
                })[0] as DecisionReceipt | undefined;

            return latestReceipt || null;
        } catch (error) {
            console.error('Error getting latest receipt:', error);
            return null;
        }
    }

    private isDetectionEngineReceipt(receipt: any): boolean {
        return receipt &&
               typeof receipt === 'object' &&
               'evaluation_point' in receipt &&
               'gate_id' in receipt &&
               (receipt.gate_id?.includes('detection-engine') || 
                receipt.gate_id?.includes('m05') ||
                receipt.policy_version_ids?.some((id: string) => id.includes('M05') || id.includes('PM-4')));
    }

    async renderOverview(webview: vscode.Webview, panel: vscode.WebviewPanel): Promise<void> {
        const receipt = await this.getLatestReceipt();
        
        const html = `
            <div id="zeroui-section-m05-overview">
                <h3>Detection Engine Core - Overview</h3>
                ${receipt ? `
                    <div class="decision-status">
                        <strong>Status:</strong> <span class="status-${receipt.decision.status}">${receipt.decision.status}</span>
                    </div>
                    <div class="decision-rationale">
                        <strong>Rationale:</strong> ${this.escapeHtml(receipt.decision.rationale || 'No rationale provided')}
                    </div>
                    <div class="evaluation-point">
                        <strong>Evaluation Point:</strong> ${receipt.evaluation_point}
                    </div>
                    <div class="timestamp">
                        <strong>Timestamp:</strong> ${receipt.timestamp_utc}
                    </div>
                ` : `
                    <p>No recent detection decisions available.</p>
                `}
            </div>
            <style>
                #zeroui-section-m05-overview {
                    padding: 1em;
                }
                .status-pass { color: green; }
                .status-warn { color: orange; }
                .status-soft_block { color: #ff6b00; }
                .status-hard_block { color: red; }
            </style>
        `;

        await webview.postMessage({
            type: 'render-section',
            moduleId: 'm05',
            sectionId: 'overview',
            html: html
        });
    }

    async renderDetails(webview: vscode.Webview, panel: vscode.WebviewPanel): Promise<void> {
        const receipt = await this.getLatestReceipt();
        
        const html = `
            <div id="zeroui-section-m05-details">
                <h3>Detection Engine Core - Details</h3>
                ${receipt ? `
                    <div class="receipt-details">
                        <div><strong>Receipt ID:</strong> ${receipt.receipt_id}</div>
                        <div><strong>Gate ID:</strong> ${receipt.gate_id}</div>
                        <div><strong>Policy Versions:</strong> ${receipt.policy_version_ids.join(', ')}</div>
                        <div><strong>Snapshot Hash:</strong> ${receipt.snapshot_hash.substring(0, 16)}...</div>
                        <div><strong>Actor:</strong> ${receipt.actor.repo_id}${receipt.actor.type ? ` (${receipt.actor.type})` : ''}</div>
                        ${receipt.context ? `
                            <div><strong>Context:</strong> ${receipt.context.surface || 'N/A'}</div>
                            ${receipt.context.branch ? `<div><strong>Branch:</strong> ${receipt.context.branch}</div>` : `<div><strong>Branch:</strong> N/A</div>`}
                            ${receipt.context.commit ? `<div><strong>Commit:</strong> ${receipt.context.commit.substring(0, 8)}</div>` : `<div><strong>Commit:</strong> N/A</div>`}
                        ` : ''}
                        ${receipt.override ? `
                            <div class="override-info">
                                <strong>Override:</strong> ${receipt.override.reason} (by ${receipt.override.approver})
                            </div>
                        ` : ''}
                        <div><strong>Degraded Mode:</strong> ${receipt.degraded ? 'Yes' : 'No'}</div>
                    </div>
                ` : `
                    <p>No receipt details available.</p>
                `}
            </div>
            <style>
                #zeroui-section-m05-details {
                    padding: 1em;
                }
                .override-info {
                    background-color: #fff3cd;
                    padding: 0.5em;
                    border-radius: 4px;
                    margin-top: 0.5em;
                }
            </style>
        `;

        await webview.postMessage({
            type: 'render-section',
            moduleId: 'm05',
            sectionId: 'details',
            html: html
        });
    }

    async listEvidenceItems(): Promise<readonly { label: string; open: () => Promise<void> }[]> {
        const receipt = await this.getLatestReceipt();
        
        if (!receipt || !receipt.evidence_handles || receipt.evidence_handles.length === 0) {
            return [];
        }

        return receipt.evidence_handles.map((handle: EvidenceHandle, index: number) => ({
            label: handle.description || `Evidence ${index + 1}`,
            open: async () => {
                if (handle.url) {
                    await vscode.env.openExternal(vscode.Uri.parse(handle.url));
                } else {
                    await vscode.window.showInformationMessage(`Evidence: ${handle.description || 'No description'}`);
                }
            }
        }));
    }

    private escapeHtml(text: string): string {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
}

