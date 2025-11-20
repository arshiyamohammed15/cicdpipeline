/**
 * LocalIngress
 *
 * Local file-based implementation of IngressPort.
 * Uses route table JSON and TLS config JSON persisted (no keys stored).
 */
import { IngressPort, IngressRule, IngressListOptions, IngressStats } from '../../ports/IngressPort';
export type ComplianceStatus = 'COMPLIANT' | 'NON_COMPLIANT';
export declare class LocalIngress implements IngressPort {
    private baseDir;
    private routeTableFile;
    private tlsConfigFile;
    private globalTlsFile;
    private routeTable;
    private tlsConfig;
    private globalTls;
    private stats;
    private envName;
    constructor(baseDir: string, envName?: string);
    createRule(rule: IngressRule): Promise<string>;
    deleteRule(ruleId: string): Promise<void>;
    getRule(ruleId: string): Promise<IngressRule>;
    listRules(options?: IngressListOptions): Promise<IngressRule[]>;
    getStats(ruleId: string): Promise<IngressStats>;
    /**
     * Record a request (for stats tracking).
     */
    recordRequest(ruleId: string, success: boolean, responseTime?: number): void;
    /**
     * Set global TLS configuration.
     * Persists JSON with certificate and key references (no private keys stored).
     */
    setTls(config: {
        enabled: boolean;
        cert_ref: string;
        key_ref: string;
    }): Promise<void>;
    /**
     * Get compliance status based on infra.network.tls_required and TLS enabled status.
     */
    status(): ComplianceStatus;
    private loadConfigs;
    private saveConfigs;
    private saveGlobalTls;
    private ensureDirectory;
    private generateRuleId;
}
//# sourceMappingURL=LocalIngress.d.ts.map