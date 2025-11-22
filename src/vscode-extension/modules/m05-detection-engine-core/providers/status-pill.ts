/**
 * Detection Engine Core Status Pill Provider
 * 
 * Implements status pill per PRD Section 3.8
 * Status values: pass, warn, soft_block, hard_block (per GSMD receipts_schema)
 */

import * as vscode from 'vscode';
import { ReceiptStorageReader } from '../../../shared/storage/ReceiptStorageReader';
import { DecisionReceipt } from '../../../shared/receipt-parser/ReceiptParser';

export interface CoreDeps {
    context: vscode.ExtensionContext;
    receiptReader?: ReceiptStorageReader;
    ipcClient?: any;
}

export class DetectionEngineStatusPillProvider {
    private receiptReader?: ReceiptStorageReader;
    private lastStatus: 'pass' | 'warn' | 'soft_block' | 'hard_block' = 'pass';
    private lastTooltip: string = 'Detection Engine Core: No data';

    async initialize(deps: CoreDeps): Promise<void> {
        if (deps.receiptReader) {
            this.receiptReader = deps.receiptReader;
        } else {
            const zuRoot = vscode.workspace.getConfiguration('zeroui').get<string>('zuRoot') || 
                          process.env.ZU_ROOT || 
                          undefined;
            this.receiptReader = new ReceiptStorageReader(zuRoot);
        }
        
        // Initial status update
        await this.updateStatus();
        
        // Set up periodic updates (every 30 seconds)
        setInterval(() => {
            void this.updateStatus();
        }, 30000);
    }

    private async updateStatus(): Promise<void> {
        try {
            const repoId = this.getWorkspaceRepoId();
            const now = new Date();
            const year = now.getFullYear();
            const month = now.getMonth() + 1;
            
            if (!this.receiptReader) {
                return;
            }

            const receipts = await this.receiptReader.readReceipts(repoId, year, month);
            
            // Find latest M05 decision receipt
            const latestReceipt = receipts
                .filter(r => this.isDetectionEngineReceipt(r))
                .sort((a, b) => {
                    const aTime = (a as any).timestamp_utc || '';
                    const bTime = (b as any).timestamp_utc || '';
                    return bTime.localeCompare(aTime);
                })[0] as DecisionReceipt | undefined;

            if (latestReceipt && latestReceipt.decision) {
                this.lastStatus = latestReceipt.decision.status;
                this.lastTooltip = `Detection Engine Core: ${latestReceipt.decision.status}\n${latestReceipt.decision.rationale || 'No rationale'}`;
            } else {
                this.lastStatus = 'pass';
                this.lastTooltip = 'Detection Engine Core: No recent decisions';
            }
        } catch (error) {
            // On error, show degraded status
            this.lastStatus = 'warn';
            this.lastTooltip = `Detection Engine Core: Error reading receipts - ${error instanceof Error ? error.message : 'Unknown error'}`;
        }
    }

    private isDetectionEngineReceipt(receipt: any): boolean {
        return receipt &&
               typeof receipt === 'object' &&
               'evaluation_point' in receipt &&
               'gate_id' in receipt &&
               (receipt.gate_id?.includes('detection-engine') || 
                receipt.gate_id?.includes('m05') ||
                receipt.policy_version_ids?.some((id: string) => id.includes('M05')));
    }

    private getWorkspaceRepoId(): string {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            return 'default-repo';
        }
        return workspaceFolder.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    }

    async getText(): Promise<string> {
        await this.updateStatus();
        
        // Map status to display text per GSMD messages.status_pill
        switch (this.lastStatus) {
            case 'pass':
                return '✓ Detection';
            case 'warn':
                return '⚠ Detection';
            case 'soft_block':
                return '⚠ Detection (Soft)';
            case 'hard_block':
                return '✗ Detection (Blocked)';
            default:
                return '— Detection';
        }
    }

    async getTooltip(): Promise<string> {
        await this.updateStatus();
        return this.lastTooltip;
    }
}

// Legacy export for backward compatibility
export function getStatusPillText(): string {
    return '—';
}

export function getStatusPillTooltip(): string {
    return 'No data yet (skeleton)';
}
