/**
 * Decision Receipt interface
 * 
 * Normative schema definition per Trust_as_a_Capability_V_0_1.md TR-1.2.1
 * This interface matches the Edge Agent receipt types for consistency.
 */
export interface DecisionReceipt {
    receipt_id: string;                    // Unique receipt identifier (UUID)
    gate_id: string;                        // Gate identifier (e.g., "edge-agent", "pre-commit-gate")
    policy_version_ids: string[];           // Array of policy version IDs evaluated
    snapshot_hash: string;                 // SHA256 hash of policy snapshot (format: "sha256:hex")
    timestamp_utc: string;                  // ISO 8601 UTC timestamp
    timestamp_monotonic_ms: number;         // Hardware monotonic timestamp in milliseconds
    evaluation_point: 'pre-commit' | 'pre-merge' | 'pre-deploy' | 'post-deploy';
    inputs: Record<string, any>;            // Input signals (metadata only, no raw code/secrets)
    decision: {
        status: 'pass' | 'warn' | 'soft_block' | 'hard_block';
        rationale: string;                  // Human-readable explanation
        badges: string[];                    // Array of badge strings
    };
    evidence_handles: EvidenceHandle[];     // Array of evidence references
    actor: {
        repo_id: string;                    // Repository identifier (kebab-case)
        machine_fingerprint?: string;       // Optional machine fingerprint
        type?: 'human' | 'ai' | 'automated'; // Actor type (TR-6.2.1) - populated when reliable signals exist
    };
    context?: {                             // Optional context information (TR-1.2.3)
        surface?: 'ide' | 'pr' | 'ci';      // Surface where decision was made
        branch?: string;                    // Git branch name (if available)
        commit?: string;                    // Git commit hash (if available)
        pr_id?: string;                     // Pull request identifier (if available)
    };
    override?: {                            // Optional override information (TR-3.2.1) - required if override occurred
        reason: string;                      // Mandatory override reason (TR-3.1)
        approver: string;                   // Identity of approver (TR-3.1)
        timestamp: string;                   // ISO 8601 timestamp of override (TR-3.2)
        override_id?: string;                // Optional override identifier linking to override snapshot
    };
    data_category?: 'public' | 'internal' | 'confidential' | 'restricted'; // Data classification (TR-4.4.1)
    degraded: boolean;                      // Degraded mode flag
    signature: string;                      // Cryptographic signature
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
        // Required fields validation
        const hasRequiredFields = (
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

        if (!hasRequiredFields) {
            return false;
        }

        // Optional fields validation (TR-1.2.1 schema extensions)
        // actor.type (TR-6.2.1)
        if (receipt.actor.type !== undefined) {
            if (!['human', 'ai', 'automated'].includes(receipt.actor.type)) {
                return false;
            }
        }

        // context (TR-1.2.3)
        if (receipt.context !== undefined) {
            if (typeof receipt.context !== 'object') {
                return false;
            }
            if (receipt.context.surface !== undefined && !['ide', 'pr', 'ci'].includes(receipt.context.surface)) {
                return false;
            }
            if (receipt.context.branch !== undefined && typeof receipt.context.branch !== 'string') {
                return false;
            }
            if (receipt.context.commit !== undefined && typeof receipt.context.commit !== 'string') {
                return false;
            }
            if (receipt.context.pr_id !== undefined && typeof receipt.context.pr_id !== 'string') {
                return false;
            }
        }

        // override (TR-3.2.1)
        if (receipt.override !== undefined) {
            if (typeof receipt.override !== 'object') {
                return false;
            }
            if (typeof receipt.override.reason !== 'string' || receipt.override.reason.length === 0) {
                return false; // reason is required if override is present
            }
            if (typeof receipt.override.approver !== 'string' || receipt.override.approver.length === 0) {
                return false; // approver is required if override is present
            }
            if (typeof receipt.override.timestamp !== 'string') {
                return false; // timestamp is required if override is present
            }
            if (receipt.override.override_id !== undefined && typeof receipt.override.override_id !== 'string') {
                return false;
            }
        }

        // data_category (TR-4.4.1)
        if (receipt.data_category !== undefined) {
            if (!['public', 'internal', 'confidential', 'restricted'].includes(receipt.data_category)) {
                return false;
            }
        }

        return true;
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
