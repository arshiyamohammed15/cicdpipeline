/**
 * IngressPort
 *
 * Cloud-agnostic interface for ingress/load balancer operations.
 * Implemented by local adapters for traffic routing and load balancing.
 *
 * @interface IngressPort
 */
export interface IngressPort {
    /**
     * Create or update an ingress rule.
     *
     * @param rule - Ingress rule configuration
     * @returns Promise resolving to ingress rule ID
     */
    createRule(rule: IngressRule): Promise<string>;
    /**
     * Delete an ingress rule.
     *
     * @param ruleId - Ingress rule ID to delete
     * @returns Promise resolving when rule is deleted
     */
    deleteRule(ruleId: string): Promise<void>;
    /**
     * Get ingress rule configuration.
     *
     * @param ruleId - Ingress rule ID
     * @returns Promise resolving to ingress rule
     */
    getRule(ruleId: string): Promise<IngressRule>;
    /**
     * List all ingress rules.
     *
     * @param options - Optional filter options
     * @returns Promise resolving to list of ingress rules
     */
    listRules(options?: IngressListOptions): Promise<IngressRule[]>;
    /**
     * Get ingress statistics and health.
     *
     * @param ruleId - Ingress rule ID
     * @returns Promise resolving to ingress statistics
     */
    getStats(ruleId: string): Promise<IngressStats>;
}
/**
 * Ingress rule configuration.
 */
export interface IngressRule {
    /** Rule ID */
    id?: string;
    /** Hostname/domain */
    host: string;
    /** Path pattern */
    path?: string;
    /** Target service/endpoint */
    target: IngressTarget;
    /** TLS/SSL configuration */
    tls?: IngressTLS;
    /** Health check configuration */
    healthCheck?: IngressHealthCheck;
}
/**
 * Ingress target configuration.
 */
export interface IngressTarget {
    /** Target type */
    type: 'service' | 'instance' | 'function';
    /** Target identifier (service name, instance ID, function name) */
    identifier: string;
    /** Target port */
    port?: number;
    /** Load balancing algorithm */
    loadBalancing?: 'round-robin' | 'least-connections' | 'weighted';
}
/**
 * TLS/SSL configuration for ingress.
 */
export interface IngressTLS {
    /** Whether TLS is enabled */
    enabled: boolean;
    /** Certificate identifier */
    certificateId?: string;
    /** Minimum TLS version */
    minVersion?: '1.0' | '1.1' | '1.2' | '1.3';
}
/**
 * Health check configuration for ingress.
 */
export interface IngressHealthCheck {
    /** Health check path */
    path: string;
    /** Health check interval (seconds) */
    intervalSeconds?: number;
    /** Health check timeout (seconds) */
    timeoutSeconds?: number;
    /** Healthy threshold count */
    healthyThreshold?: number;
    /** Unhealthy threshold count */
    unhealthyThreshold?: number;
}
/**
 * Options for listing ingress rules.
 */
export interface IngressListOptions {
    /** Filter by hostname */
    host?: string;
    /** Maximum number of rules to return */
    maxResults?: number;
}
/**
 * Ingress statistics and health metrics.
 */
export interface IngressStats {
    /** Total requests */
    totalRequests: number;
    /** Successful requests */
    successfulRequests: number;
    /** Failed requests */
    failedRequests: number;
    /** Average response time (milliseconds) */
    averageResponseTime?: number;
    /** Active connections */
    activeConnections?: number;
    /** Target health status */
    targetHealth?: 'healthy' | 'unhealthy' | 'degraded';
}
//# sourceMappingURL=IngressPort.d.ts.map