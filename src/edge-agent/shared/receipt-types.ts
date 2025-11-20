/**
 * Receipt Types (Edge Agent)
 *
 * Type definitions for receipts, matching VS Code Extension receipt types.
 *
 * @module receipt-types
 */

/**
 * Decision Receipt interface
 * 
 * Normative schema definition per Trust_as_a_Capability_V_0_1.md TR-1.2.1
 * This interface serves as the single source of truth for Decision Receipt structure.
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

/**
 * Feedback Receipt interface
 */
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

/**
 * Evidence Handle interface
 */
export interface EvidenceHandle {
    url: string;
    type: string;
    description: string;
    expires_at?: string;
}
