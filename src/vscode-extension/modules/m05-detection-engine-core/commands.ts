/**
 * Detection Engine Core Commands
 * 
 * Implements commands per PRD Section 3.8:
 * - zeroui.m05.showDecisionCard
 * - zeroui.m05.viewReceipt
 */

import * as vscode from 'vscode';
import { ReceiptStorageReader } from '../../shared/storage/ReceiptStorageReader';
import { DecisionCardManager } from '../../ui/decision-card/DecisionCardManager';
import { ReceiptViewerManager } from '../../ui/receipt-viewer/ReceiptViewerManager';

let receiptReader: ReceiptStorageReader | undefined;

function getReceiptReader(): ReceiptStorageReader {
    if (!receiptReader) {
        const zuRoot = vscode.workspace.getConfiguration('zeroui').get<string>('zuRoot') || 
                      process.env.ZU_ROOT || 
                      undefined;
        receiptReader = new ReceiptStorageReader(zuRoot);
    }
    return receiptReader;
}

function getWorkspaceRepoId(): string {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        return 'default-repo';
    }
    // Extract repo ID from workspace folder name (kebab-case)
    return workspaceFolder.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
}

export function registerCommands(context: vscode.ExtensionContext): void {
    // Command: zeroui.m05.showDecisionCard
    const showDecisionCard = vscode.commands.registerCommand('zeroui.m05.showDecisionCard', async () => {
        try {
            const decisionCardManager = new DecisionCardManager();
            const repoId = getWorkspaceRepoId();
            const reader = getReceiptReader();
            
            // Get current date for receipt lookup
            const now = new Date();
            const year = now.getFullYear();
            const month = now.getMonth() + 1;
            
            // Read latest receipts
            const receipts = await reader.readReceipts(repoId, year, month);
            
            // Find latest PM-4 (Detection Engine Core) decision receipt
            const latestReceipt = receipts
                .filter(r => 'evaluation_point' in r && 'gate_id' in r)
                .filter(r => (r as any).gate_id?.includes('detection-engine') || (r as any).gate_id?.includes('m05'))
                .sort((a, b) => {
                    const aTime = (a as any).timestamp_utc || '';
                    const bTime = (b as any).timestamp_utc || '';
                    return bTime.localeCompare(aTime);
                })[0] as any;

            if (latestReceipt) {
                const decisionData = {
                    status: latestReceipt.decision?.status || 'pass',
                    rationale: latestReceipt.decision?.rationale || 'No decision data available',
                    timestampUtc: latestReceipt.timestamp_utc,
                    moduleId: 'm05',
                    evaluationPoint: latestReceipt.evaluation_point,
                    evidenceHandles: latestReceipt.evidence_handles || []
                };
                
                await decisionCardManager.showDecisionCard(decisionData);
            } else {
                await vscode.window.showInformationMessage('No decision receipts found for Detection Engine Core');
            }
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error';
            await vscode.window.showErrorMessage(`Failed to show decision card: ${message}`);
        }
    });

    // Command: zeroui.m05.viewReceipt
    const viewReceipt = vscode.commands.registerCommand('zeroui.m05.viewReceipt', async () => {
        try {
            const receiptViewerManager = new ReceiptViewerManager();
            const repoId = getWorkspaceRepoId();
            const reader = getReceiptReader();
            
            // Get current date for receipt lookup
            const now = new Date();
            const year = now.getFullYear();
            const month = now.getMonth() + 1;
            
            // Read latest receipts
            const receipts = await reader.readReceipts(repoId, year, month);
            
            // Find latest PM-4 (Detection Engine Core) decision receipt
            const latestReceipt = receipts
                .filter(r => 'evaluation_point' in r && 'gate_id' in r)
                .filter(r => (r as any).gate_id?.includes('detection-engine') || (r as any).gate_id?.includes('m05'))
                .sort((a, b) => {
                    const aTime = (a as any).timestamp_utc || '';
                    const bTime = (b as any).timestamp_utc || '';
                    return bTime.localeCompare(aTime);
                })[0];

            if (latestReceipt) {
                await receiptViewerManager.showReceipt(latestReceipt);
            } else {
                await vscode.window.showInformationMessage('No decision receipts found for Detection Engine Core');
            }
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error';
            await vscode.window.showErrorMessage(`Failed to view receipt: ${message}`);
        }
    });

    context.subscriptions.push(showDecisionCard, viewReceipt);
}
