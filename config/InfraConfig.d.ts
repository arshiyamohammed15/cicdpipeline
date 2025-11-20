/**
 * InfraConfig.ts
 *
 * Infrastructure configuration loader with strict precedence and vendor-neutral validation.
 *
 * Precedence: defaults (top-level infra) → per-env "infra" override → optional policy overlay
 *
 * Constraints:
 * - No JSON-Schema engine (internal type-guards only)
 * - No placeholder interpolation
 * - Vendor-neutral validation for neutral infra fields only
 * - Returns frozen config object
 */
export interface InfraCompute {
    min_baseline: number;
    allow_spot: boolean;
}
export interface InfraRouting {
    default: 'serverless' | 'gpu-queue' | 'batch';
    cost_profiles: Array<'light' | 'ai-inference' | 'batch'>;
}
export interface InfraStorage {
    object_root: string;
    backups_root: string;
    encryption_at_rest: boolean;
}
export interface InfraNetwork {
    tls_required: boolean;
}
export interface InfraObservability {
    enable_metrics: boolean;
    enable_cost: boolean;
}
export interface InfraDR {
    cross_zone: boolean;
    backup_interval_min: number;
}
export interface InfraFeatureFlags {
    infra_enabled: boolean;
    local_adapters_enabled: boolean;
}
export interface InfraConfig {
    compute: InfraCompute;
    routing: InfraRouting;
    storage: InfraStorage;
    network: InfraNetwork;
    observability: InfraObservability;
    dr: InfraDR;
    feature_flags: InfraFeatureFlags;
}
export interface InfraConfigResult {
    config: Readonly<InfraConfig>;
    isEnabled: boolean;
}
export interface LoadInfraConfigOptions {
    policyOverlayPath?: string;
}
/**
 * Check if infra config is vendor-neutral by scanning only neutral fields
 * Throws with offending key path if vendor identifier found
 */
export declare function isVendorNeutral(infra: InfraConfig): void;
/**
 * Load and merge infrastructure configuration with precedence:
 * defaults (top-level infra) → per-env "infra" override → optional policy overlay
 */
export declare function loadInfraConfig(envName: string, opts?: LoadInfraConfigOptions): InfraConfigResult;
//# sourceMappingURL=InfraConfig.d.ts.map