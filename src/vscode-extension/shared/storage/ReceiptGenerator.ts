import * as crypto from 'crypto';
import { DecisionReceipt, FeedbackReceipt } from '../receipt-parser/ReceiptParser';

/**
 * Lightweight receipt generator for the VS Code extension tests.
 * Mirrors the behaviour of the Edge Agent implementation so cross-tier
 * validation continues to function without forcing the compiler to include
 * sources outside the extension workspace.
 */
export class ReceiptGenerator {
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
        degraded: boolean = false
    ): DecisionReceipt {
        const receipt: Omit<DecisionReceipt, 'signature'> = {
            receipt_id: this.generateReceiptId(),
            gate_id: gateId,
            policy_version_ids: policyVersionIds,
            snapshot_hash: snapshotHash,
            timestamp_utc: new Date().toISOString(),
            timestamp_monotonic_ms: Date.now(),
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
        const canonicalJson = this.toCanonicalJson(receipt);
        const hash = crypto.createHash('sha256').update(canonicalJson).digest('hex');
        return `sig-${hash}`;
    }

    private toCanonicalJson(value: unknown): string {
        if (value === null || typeof value !== 'object') {
            return JSON.stringify(value);
        }

        if (Array.isArray(value)) {
            return `[${value.map(item => this.toCanonicalJson(item)).join(',')}]`;
        }

        const entries = Object.keys(value as Record<string, unknown>)
            .sort()
            .map(key => `${JSON.stringify(key)}:${this.toCanonicalJson((value as Record<string, unknown>)[key])}`);

        return `{${entries.join(',')}}`;
    }
}


