/**
 * Detection Engine Core Diagnostics Provider
 * 
 * Implements diagnostics per PRD Section 3.8
 * Provides diagnostics based on detection engine decisions
 */

import * as vscode from 'vscode';
import { ReceiptStorageReader } from '../../../shared/storage/ReceiptStorageReader';
import { DecisionReceipt } from '../../../shared/receipt-parser/ReceiptParser';

export interface CoreDeps {
    context: vscode.ExtensionContext;
    receiptReader?: ReceiptStorageReader;
    ipcClient?: any;
}

export class DetectionEngineDiagnosticsProvider {
    private receiptReader?: ReceiptStorageReader;
    private diagnostics: vscode.Diagnostic[] = [];

    async initialize(deps: CoreDeps): Promise<void> {
        if (deps.receiptReader) {
            this.receiptReader = deps.receiptReader;
        } else {
            const zuRoot = vscode.workspace.getConfiguration('zeroui').get<string>('zuRoot') || 
                          process.env.ZU_ROOT || 
                          undefined;
            this.receiptReader = new ReceiptStorageReader(zuRoot);
        }
        
        // Initial diagnostics computation
        await this.computeDiagnostics();
        
        // Set up periodic updates (every 60 seconds)
        setInterval(() => {
            void this.computeDiagnostics();
        }, 60000);
    }

    private getWorkspaceRepoId(): string {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            return 'default-repo';
        }
        return workspaceFolder.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
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

    async computeDiagnostics(): Promise<readonly vscode.Diagnostic[]> {
        this.diagnostics = [];

        try {
            const repoId = this.getWorkspaceRepoId();
            const now = new Date();
            const year = now.getFullYear();
            const month = now.getMonth() + 1;
            
            if (!this.receiptReader) {
                return this.diagnostics;
            }

            const receipts = await this.receiptReader.readReceipts(repoId, year, month);
            
            // Filter to detection engine receipts
            const detectionReceipts = receipts
                .filter(r => this.isDetectionEngineReceipt(r))
                .map(r => r as DecisionReceipt);

            // Create diagnostics from receipts with warn, soft_block, or hard_block status
            for (const receipt of detectionReceipts) {
                if (receipt.decision && 
                    (receipt.decision.status === 'warn' || 
                     receipt.decision.status === 'soft_block' || 
                     receipt.decision.status === 'hard_block')) {
                    
                    // Create diagnostic for the decision
                    const severity = receipt.decision.status === 'hard_block' 
                        ? vscode.DiagnosticSeverity.Error
                        : receipt.decision.status === 'soft_block'
                        ? vscode.DiagnosticSeverity.Warning
                        : vscode.DiagnosticSeverity.Information;

                    const diagnostic = new vscode.Diagnostic(
                        new vscode.Range(0, 0, 0, 0), // Global diagnostic
                        `[Detection Engine] ${receipt.decision.rationale || 'Detection issue detected'}`,
                        severity
                    );

                    diagnostic.source = 'Detection Engine Core (M05)';
                    diagnostic.code = {
                        value: `M05-${receipt.decision.status.toUpperCase()}`,
                        target: vscode.Uri.parse(`zeroui://receipt/${receipt.receipt_id}`)
                    };

                    // Add related information
                    if (receipt.evaluation_point) {
                        diagnostic.relatedInformation = [
                            new vscode.DiagnosticRelatedInformation(
                                new vscode.Location(
                                    vscode.Uri.parse(`zeroui://evaluation-point/${receipt.evaluation_point}`),
                                    new vscode.Range(0, 0, 0, 0)
                                ),
                                `Evaluation point: ${receipt.evaluation_point}`
                            )
                        ];
                    }

                    this.diagnostics.push(diagnostic);
                }
            }
        } catch (error) {
            // On error, create a warning diagnostic
            const errorDiagnostic = new vscode.Diagnostic(
                new vscode.Range(0, 0, 0, 0),
                `[Detection Engine] Error reading receipts: ${error instanceof Error ? error.message : 'Unknown error'}`,
                vscode.DiagnosticSeverity.Warning
            );
            errorDiagnostic.source = 'Detection Engine Core (M05)';
            this.diagnostics.push(errorDiagnostic);
        }

        return this.diagnostics;
    }
}

// Legacy export for backward compatibility
export function computeDiagnostics(): vscode.Diagnostic[] {
    return [];
}
