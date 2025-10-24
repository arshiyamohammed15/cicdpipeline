export interface DecisionReceipt {
    receipt_id: string;
    gate_id: string;
    policy_version_ids: string[];
    snapshot_hash: string;
    timestamp_utc: string;
    timestamp_monotonic_ms: number;
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
export declare class ReceiptParser {
    parseDecisionReceipt(receiptJson: string): DecisionReceipt | null;
    parseFeedbackReceipt(receiptJson: string): FeedbackReceipt | null;
    private validateDecisionReceipt;
    private validateFeedbackReceipt;
    extractReceiptId(receipt: DecisionReceipt | FeedbackReceipt): string;
    isDecisionReceipt(receipt: any): receipt is DecisionReceipt;
    isFeedbackReceipt(receipt: any): receipt is FeedbackReceipt;
}
//# sourceMappingURL=ReceiptParser.d.ts.map