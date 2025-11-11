import * as vscode from 'vscode';
import * as path from 'path';
import { ReceiptStorageReader } from './ReceiptStorageReader';
import { DecisionReceipt } from '../receipt-parser/ReceiptParser';

export type PreCommitStatus = 'pass' | 'warn' | 'soft_block' | 'hard_block' | 'unknown';

export interface MismatchInfo {
    detail: string;
    category: string;
    path?: string;
    expected?: string;
    actual?: string;
}

export interface PreCommitDecisionSnapshot {
    status: PreCommitStatus;
    receipt?: DecisionReceipt;
    policySnapshotId?: string;
    artifactId?: string;
    mismatches: MismatchInfo[];
    diffCandidate?: vscode.Uri;
    labels?: Record<string, unknown>;
}

export class PreCommitDecisionService {
    constructor(
        private readonly receiptReader: ReceiptStorageReader,
        private readonly output: vscode.OutputChannel,
        private readonly workspaceRoot: string | undefined
    ) {}

    public async loadLatest(repoId: string): Promise<PreCommitDecisionSnapshot> {
        try {
            const receipts = await this.receiptReader.readLatestReceipts(repoId, 1);
            const latest = receipts.find(
                (receipt): receipt is DecisionReceipt => receipt && 'decision' in receipt
            );

            if (!latest) {
                this.tailOutput(undefined);
                return {
                    status: 'unknown',
                    mismatches: []
                };
            }

            const status = this.normalizeStatus(latest.decision?.status);
            const inputs = (latest as any).inputs ?? {};
            const labels = inputs.labels as Record<string, unknown> | undefined;
            const policySnapshotId: string | undefined =
                typeof inputs.policy_snapshot_id === 'string'
                    ? inputs.policy_snapshot_id
                    : latest.policy_version_ids?.[0];
            const artifactId: string | undefined =
                typeof inputs.artifact_id === 'string'
                    ? inputs.artifact_id
                    : (labels?.artifact_id as string | undefined);

            const mismatches = this.extractMismatches(inputs.mismatches);
            const diffCandidate = this.resolveDiffCandidate(mismatches);

            this.tailOutput(latest);

            return {
                status,
                receipt: latest,
                policySnapshotId,
                artifactId,
                mismatches,
                diffCandidate,
                labels
            };
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            this.output.clear();
            this.output.appendLine(`Failed to load DecisionReceipt: ${message}`);
            return {
                status: 'unknown',
                mismatches: []
            };
        }
    }

    private extractMismatches(raw: unknown): MismatchInfo[] {
        if (!Array.isArray(raw)) {
            return [];
        }

        return raw
            .map(item => {
                if (typeof item === 'string') {
                    return {
                        detail: item,
                        category: 'unknown',
                        path: this.extractPath(item)
                    } as MismatchInfo;
                }

                if (typeof item === 'object' && item !== null) {
                    const record = item as Record<string, unknown>;
                    const detail = typeof record.detail === 'string' ? record.detail : JSON.stringify(record);
                    const category = typeof record.category === 'string' ? record.category : 'unknown';
                    const candidatePath =
                        typeof record.path === 'string' ? record.path : this.extractPath(detail);

                    return {
                        detail,
                        category,
                        path: candidatePath
                    };
                }

                return undefined;
            })
            .filter((entry): entry is MismatchInfo => Boolean(entry));
    }

    private extractPath(detail: string): string | undefined {
        const hashMatch = detail.match(/Hash mismatch for\s+(.+?):\s+expected/i);
        if (hashMatch?.[1]) {
            return hashMatch[1];
        }

        const missingMatch = detail.match(/File missing:\s+(.+)/i);
        if (missingMatch?.[1]) {
            return missingMatch[1];
        }

        return undefined;
    }

    private resolveDiffCandidate(mismatches: MismatchInfo[]): vscode.Uri | undefined {
        const target = mismatches.find(entry => entry.path)?.path;
        if (!target || !this.workspaceRoot) {
            return undefined;
        }

        const absolutePath = path.isAbsolute(target)
            ? target
            : path.join(this.workspaceRoot, target);

        return vscode.Uri.file(absolutePath);
    }

    private normalizeStatus(status: string | undefined): PreCommitStatus {
        if (!status) {
            return 'unknown';
        }
        if (status === 'pass' || status === 'warn' || status === 'soft_block' || status === 'hard_block') {
            return status;
        }
        return 'unknown';
    }

    private tailOutput(receipt: DecisionReceipt | undefined): void {
        this.output.clear();
        if (receipt) {
            this.output.appendLine(JSON.stringify(receipt, null, 2));
        } else {
            this.output.appendLine('No DecisionReceipt found.');
        }
    }
}

