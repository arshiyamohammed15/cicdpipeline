import * as crypto from 'crypto';
import { DecisionReceipt, FeedbackReceipt } from '../receipt-parser/ReceiptParser';
import { ReceiptSigner } from './ReceiptSigner';

/**
 * Lightweight receipt generator for the VS Code extension tests.
 * Mirrors the behaviour of the Edge Agent implementation so cross-tier
 * validation continues to function without forcing the compiler to include
 * sources outside the extension workspace.
 */
export class ReceiptGenerator {
    constructor(private readonly signer?: ReceiptSigner) {}

    public generateDecisionReceipt(
        gateId: string,
        policyVersionIds: string[],
        snapshotHash: string,
        inputs: Record<string, unknown>,
        decision: {
            status: 'pass' | 'warn' | 'soft_block' | 'hard_block';
            rationale: string;
            badges: string[];
        },
        evidenceHandles: Array<{
            url: string;
            type: string;
            description: string;
            expires_at?: string;
        }>,
        actor: {
            repo_id: string;
            machine_fingerprint?: string;
        },
        degraded: boolean = false,
        evaluationPoint: DecisionReceipt['evaluation_point'] = 'pre-commit'
    ): DecisionReceipt {
        const receipt: Omit<DecisionReceipt, 'signature'> = {
            receipt_id: this.generateReceiptId(),
            gate_id: gateId,
            policy_version_ids: policyVersionIds,
            snapshot_hash: snapshotHash,
            timestamp_utc: new Date().toISOString(),
            timestamp_monotonic_ms: Date.now(),
            evaluation_point: evaluationPoint,
            inputs,
            decision,
            evidence_handles: evidenceHandles,
            actor,
            degraded
        };

        return {
            ...receipt,
            signature: this.signReceipt(receipt)
        };
    }

    public generateFeedbackReceipt(
        decisionReceiptId: string,
        patternId: 'FB-01' | 'FB-02' | 'FB-03' | 'FB-04',
        choice: 'worked' | 'partly' | 'didnt',
        tags: string[],
        actor: {
            repo_id: string;
            machine_fingerprint?: string;
        }
    ): FeedbackReceipt {
        const receipt: Omit<FeedbackReceipt, 'signature'> = {
            feedback_id: this.generateReceiptId(),
            decision_receipt_id: decisionReceiptId,
            pattern_id: patternId,
            choice,
            tags,
            actor,
            timestamp_utc: new Date().toISOString()
        };

        return {
            ...receipt,
            signature: this.signReceipt(receipt)
        };
    }

    private generateReceiptId(): string {
        const timestamp = Date.now();
        const nonce = crypto.randomBytes(8).toString('hex');
        return `receipt-${timestamp}-${nonce}`;
    }

    private signReceipt(receipt: unknown): string {
        if (!this.signer) {
            throw new Error('ReceiptGenerator requires an Ed25519 ReceiptSigner instance.');
        }
        if (typeof receipt !== 'object' || receipt === null || Array.isArray(receipt)) {
            throw new TypeError('Receipt must be an object when signing with ReceiptSigner');
        }
        return this.signer.signReceipt(receipt as Record<string, unknown>);
    }
}
