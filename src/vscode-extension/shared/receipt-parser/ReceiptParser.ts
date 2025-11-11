export interface DecisionReceipt {
    receipt_id: string;
    gate_id: string;
    policy_version_ids: string[];
    snapshot_hash: string;
    timestamp_utc: string;
    timestamp_monotonic_ms: number;
    evaluation_point: 'pre-commit' | 'pre-merge' | 'pre-deploy' | 'post-deploy';
    inputs: Record<string, any>;
    decision: {
        status: 'pass' | 'warn' | 'soft_block' | 'hard_block';
        rationale: string;
        badges: string[];
    };
    evidence_handles: EvidenceHandle[];
    actor: {
        repo_id: string;
        machine_fingerprint?: string;
    };
    degraded: boolean;
    signature: string;
}

export interface FeedbackReceipt {
    feedback_id: string;
    decision_receipt_id: string;
    pattern_id: 'FB-01' | 'FB-02' | 'FB-03' | 'FB-04';
    choice: 'worked' | 'partly' | 'didnt';
    tags: string[];
    actor: {
        repo_id: string;
        machine_fingerprint?: string;
    };
    timestamp_utc: string;
    signature: string;
}

export interface EvidenceHandle {
    url: string;
    type: string;
    description: string;
    expires_at?: string;
}

export class ReceiptParser {
    public parseDecisionReceipt(receiptJson: string): DecisionReceipt | null {
        try {
            const receipt = JSON.parse(receiptJson);
            return this.validateDecisionReceipt(receipt) ? receipt : null;
        } catch (error) {
            console.error('Failed to parse decision receipt:', error);
            return null;
        }
    }

    public parseFeedbackReceipt(receiptJson: string): FeedbackReceipt | null {
        try {
            const receipt = JSON.parse(receiptJson);
            return this.validateFeedbackReceipt(receipt) ? receipt : null;
        } catch (error) {
            console.error('Failed to parse feedback receipt:', error);
            return null;
        }
    }

    private validateDecisionReceipt(receipt: any): receipt is DecisionReceipt {
        return (
            typeof receipt.receipt_id === 'string' &&
            typeof receipt.gate_id === 'string' &&
            Array.isArray(receipt.policy_version_ids) &&
            typeof receipt.snapshot_hash === 'string' &&
            typeof receipt.timestamp_utc === 'string' &&
            typeof receipt.timestamp_monotonic_ms === 'number' &&
            typeof receipt.evaluation_point === 'string' &&
            ['pre-commit', 'pre-merge', 'pre-deploy', 'post-deploy'].includes(receipt.evaluation_point) &&
            typeof receipt.inputs === 'object' &&
            typeof receipt.decision === 'object' &&
            typeof receipt.decision.status === 'string' &&
            typeof receipt.decision.rationale === 'string' &&
            Array.isArray(receipt.decision.badges) &&
            Array.isArray(receipt.evidence_handles) &&
            typeof receipt.actor === 'object' &&
            typeof receipt.actor.repo_id === 'string' &&
            typeof receipt.degraded === 'boolean' &&
            typeof receipt.signature === 'string'
        );
    }

    private validateFeedbackReceipt(receipt: any): receipt is FeedbackReceipt {
        return (
            typeof receipt.feedback_id === 'string' &&
            typeof receipt.decision_receipt_id === 'string' &&
            typeof receipt.pattern_id === 'string' &&
            ['FB-01', 'FB-02', 'FB-03', 'FB-04'].includes(receipt.pattern_id) &&
            typeof receipt.choice === 'string' &&
            ['worked', 'partly', 'didnt'].includes(receipt.choice) &&
            Array.isArray(receipt.tags) &&
            typeof receipt.actor === 'object' &&
            typeof receipt.actor.repo_id === 'string' &&
            typeof receipt.timestamp_utc === 'string' &&
            typeof receipt.signature === 'string'
        );
    }

    public extractReceiptId(receipt: DecisionReceipt | FeedbackReceipt): string {
        return 'receipt_id' in receipt ? receipt.receipt_id : receipt.feedback_id;
    }

    public isDecisionReceipt(receipt: any): receipt is DecisionReceipt {
        return 'gate_id' in receipt;
    }

    public isFeedbackReceipt(receipt: any): receipt is FeedbackReceipt {
        return 'pattern_id' in receipt;
    }
}
