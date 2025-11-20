/**
 * WorkloadRouter
 *
 * Routes workloads based on neutral infra configuration (routing.default, cost_profiles).
 * Maps BuildPlan.cost_profile to appropriate adapters.
 */
/// <reference types="node" />
/// <reference types="node" />
import { InfraConfig } from '../../../config/InfraConfig';
import { QueuePort } from '../ports/QueuePort';
import { ServerlessPort } from '../ports/ServerlessPort';
import { GpuPoolPort } from '../ports/GpuPoolPort';
import { ObservabilityPort } from '../ports/ObservabilityPort';
/**
 * BuildPlan interface (minimal subset needed for routing)
 */
export interface BuildPlan {
    cost_profile?: string;
    [key: string]: unknown;
}
/**
 * Routing decision result
 */
export interface RoutingDecision {
    route: 'serverless' | 'gpu-queue' | 'batch';
    adapter: 'serverless' | 'queue' | 'gpu-pool';
    queueName?: string;
}
/**
 * Adapter registry for singleton instances
 */
declare class AdapterRegistry {
    private queue;
    private dlq;
    private serverless;
    private gpuPool;
    private observability;
    private baseDir;
    private infraConfig;
    constructor(baseDir: string);
    /**
     * Initialize adapters based on feature flags
     */
    initialize(infraConfig: InfraConfig): void;
    getQueue(): QueuePort | null;
    getServerless(): ServerlessPort | null;
    getGpuPool(): GpuPoolPort | null;
    getObservability(): ObservabilityPort | null;
    isEnabled(): boolean;
}
/**
 * WorkloadRouter
 *
 * Routes workloads based on BuildPlan.cost_profile and InfraConfig.routing
 */
export declare class WorkloadRouter {
    private registry;
    private envName;
    constructor(baseDir: string, envName?: string);
    /**
     * Decide routing based on BuildPlan.cost_profile and InfraConfig.routing
     */
    decide(buildPlan: BuildPlan): RoutingDecision;
    /**
     * Route workload based on BuildPlan
     */
    route(buildPlan: BuildPlan, payload: string | Buffer | Record<string, unknown>): Promise<void>;
    /**
     * Map route to adapter type
     */
    private mapRouteToAdapter;
    /**
     * Extract function name from BuildPlan (if available)
     */
    private extractFunctionName;
    /**
     * Get adapter registry (for testing)
     */
    getRegistry(): AdapterRegistry;
}
export {};
//# sourceMappingURL=WorkloadRouter.d.ts.map