/**
 * TypeScript interfaces for Configuration & Policy Management receipt types.
 *
 * Per PRD: All receipt schemas match PRD lines 654-923 exactly.
 */

export interface EvidenceHandle {
    readonly url: string;
    readonly type: string;
    readonly description: string;
    readonly expires_at?: string;
}

export interface Actor {
    readonly repo_id: string;
    readonly user_id: string;
    readonly machine_fingerprint: string;
}

export interface PolicyLifecycleReceipt {
    readonly receipt_id: string;
    readonly gate_id: string;
    readonly policy_version_ids: readonly string[];
    readonly snapshot_hash: string;
    readonly timestamp_utc: string;
    readonly timestamp_monotonic_ms: number;
    readonly inputs: {
        readonly operation: 'create' | 'update' | 'delete' | 'activate' | 'deprecate';
        readonly policy_id: string;
        readonly policy_name: string;
        readonly policy_type: 'security' | 'compliance' | 'operational' | 'governance';
        readonly status: 'draft' | 'review' | 'approved' | 'active' | 'deprecated';
    };
    readonly decision: {
        readonly status: 'pass' | 'warn' | 'soft_block' | 'hard_block';
        readonly rationale: string;
        readonly badges: readonly string[];
    };
    readonly result: {
        readonly policy_id: string;
        readonly version: string;
        readonly status: string;
        readonly enforcement_level: 'advisory' | 'warning' | 'enforcement';
    };
    readonly evidence_handles: readonly EvidenceHandle[];
    readonly actor: Actor;
    readonly degraded: boolean;
    readonly signature: string;
}

export interface ConfigurationChangeReceipt {
    readonly receipt_id: string;
    readonly gate_id: string;
    readonly policy_version_ids: readonly string[];
    readonly snapshot_hash: string;
    readonly timestamp_utc: string;
    readonly timestamp_monotonic_ms: number;
    readonly inputs: {
        readonly operation: 'create' | 'update' | 'deploy' | 'rollback' | 'drift_detected';
        readonly config_id: string;
        readonly config_name: string;
        readonly config_type: 'security' | 'performance' | 'feature' | 'compliance';
        readonly environment: 'production' | 'staging' | 'development';
        readonly deployment_strategy: 'immediate' | 'canary' | 'blue_green';
    };
    readonly decision: {
        readonly status: 'pass' | 'warn' | 'soft_block' | 'hard_block';
        readonly rationale: string;
        readonly badges: readonly string[];
    };
    readonly result: {
        readonly config_id: string;
        readonly version: string;
        readonly status: 'draft' | 'staging' | 'active' | 'deprecated';
        readonly deployed_at?: string;
        readonly drift_detected: boolean;
    };
    readonly evidence_handles: readonly EvidenceHandle[];
    readonly actor: Actor;
    readonly degraded: boolean;
    readonly signature: string;
}

export interface PolicyEvaluationDecisionReceipt {
    readonly receipt_id: string;
    readonly gate_id: string;
    readonly policy_version_ids: readonly string[];
    readonly snapshot_hash: string;
    readonly timestamp_utc: string;
    readonly timestamp_monotonic_ms: number;
    readonly inputs: {
        readonly policy_id: string;
        readonly context: Record<string, unknown>;
        readonly principal?: Record<string, unknown>;
        readonly resource?: Record<string, unknown>;
        readonly action?: string;
        readonly tenant_id: string;
        readonly environment: 'production' | 'staging' | 'development';
    };
    readonly decision: {
        readonly status: 'pass' | 'warn' | 'soft_block' | 'hard_block';
        readonly rationale: string;
        readonly badges: readonly string[];
        readonly evaluation_result: {
            readonly decision: 'allow' | 'deny' | 'transform';
            readonly reason: string;
            readonly violations: ReadonlyArray<{
                readonly rule_id: string;
                readonly policy_id: string;
                readonly violation_type: string;
                readonly severity: 'high' | 'medium' | 'low';
            }>;
        };
    };
    readonly result: {
        readonly decision: 'allow' | 'deny' | 'transform';
        readonly enforcement_applied: boolean;
        readonly cached: boolean;
        readonly evaluation_time_ms: number;
    };
    readonly evidence_handles: readonly EvidenceHandle[];
    readonly actor: Actor;
    readonly degraded: boolean;
    readonly signature: string;
}

export interface ComplianceCheckReceipt {
    readonly receipt_id: string;
    readonly gate_id: string;
    readonly policy_version_ids: readonly string[];
    readonly snapshot_hash: string;
    readonly timestamp_utc: string;
    readonly timestamp_monotonic_ms: number;
    readonly inputs: {
        readonly framework: 'soc2' | 'gdpr' | 'hipaa' | 'nist' | 'custom';
        readonly context: Record<string, unknown>;
        readonly evidence_required: boolean;
        readonly tenant_id: string;
    };
    readonly decision: {
        readonly status: 'pass' | 'warn' | 'soft_block' | 'hard_block';
        readonly rationale: string;
        readonly badges: readonly string[];
        readonly compliance_result: {
            readonly compliant: boolean;
            readonly score: number;
            readonly missing_controls: readonly string[];
            readonly evidence_gaps: ReadonlyArray<{
                readonly control_id: string;
                readonly evidence_type: string;
                readonly gap_description: string;
            }>;
        };
    };
    readonly result: {
        readonly compliant: boolean;
        readonly score: number;
        readonly framework: string;
        readonly controls_evaluated: number;
        readonly controls_passing: number;
        readonly controls_failing: number;
    };
    readonly evidence_handles: readonly EvidenceHandle[];
    readonly actor: Actor;
    readonly degraded: boolean;
    readonly signature: string;
}

export interface RemediationActionReceipt {
    readonly receipt_id: string;
    readonly gate_id: string;
    readonly policy_version_ids: readonly string[];
    readonly snapshot_hash: string;
    readonly timestamp_utc: string;
    readonly timestamp_monotonic_ms: number;
    readonly inputs: {
        readonly target_type: 'policy' | 'configuration' | 'compliance_violation';
        readonly target_id: string;
        readonly reason: string;
        readonly remediation_type: 'automatic' | 'manual' | 'rollback';
    };
    readonly decision: {
        readonly status: 'pass' | 'warn' | 'soft_block' | 'hard_block';
        readonly rationale: string;
        readonly badges: readonly string[];
    };
    readonly result: {
        readonly remediation_id: string;
        readonly status: 'pending' | 'in_progress' | 'completed' | 'failed';
        readonly target_type: string;
        readonly target_id: string;
        readonly remediation_time_ms?: number;
    };
    readonly evidence_handles: readonly EvidenceHandle[];
    readonly actor: Actor;
    readonly degraded: boolean;
    readonly signature: string;
}
