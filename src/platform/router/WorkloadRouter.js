"use strict";
/**
 * WorkloadRouter
 *
 * Routes workloads based on neutral infra configuration (routing.default, cost_profiles).
 * Maps BuildPlan.cost_profile to appropriate adapters.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.WorkloadRouter = void 0;
const InfraConfig_1 = require("../../../config/InfraConfig");
const local_1 = require("../adapters/local");
/**
 * Adapter registry for singleton instances
 */
class AdapterRegistry {
    constructor(baseDir) {
        this.queue = null;
        this.dlq = null;
        this.serverless = null;
        this.gpuPool = null;
        this.observability = null;
        this.infraConfig = null;
        this.baseDir = baseDir;
    }
    /**
     * Initialize adapters based on feature flags
     */
    initialize(infraConfig) {
        this.infraConfig = infraConfig;
        if (!infraConfig.feature_flags.infra_enabled || !infraConfig.feature_flags.local_adapters_enabled) {
            return; // Adapters disabled
        }
        // Initialize observability first (used by all adapters)
        this.observability = new local_1.LocalObservability(this.baseDir);
        // Initialize DLQ (used by queue)
        this.dlq = new local_1.LocalDLQ(this.baseDir);
        // Initialize queue
        this.queue = new local_1.LocalQueue(this.baseDir, this.dlq);
        // Initialize serverless
        const functionsDir = `${this.baseDir}/functions`;
        const logsFile = `${this.baseDir}/logs/executions.ndjson`;
        this.serverless = new local_1.LocalServerless(functionsDir, logsFile);
        // Initialize GPU pool
        this.gpuPool = new local_1.LocalGpuPool(infraConfig.compute.min_baseline || 8, ['t4', 'v100'], 't4', 16, 5000);
    }
    getQueue() {
        return this.queue;
    }
    getServerless() {
        return this.serverless;
    }
    getGpuPool() {
        return this.gpuPool;
    }
    getObservability() {
        return this.observability;
    }
    isEnabled() {
        return (this.infraConfig !== null &&
            this.infraConfig.feature_flags.infra_enabled &&
            this.infraConfig.feature_flags.local_adapters_enabled);
    }
}
/**
 * WorkloadRouter
 *
 * Routes workloads based on BuildPlan.cost_profile and InfraConfig.routing
 */
class WorkloadRouter {
    constructor(baseDir, envName = 'development') {
        this.registry = new AdapterRegistry(baseDir);
        this.envName = envName;
        // Load infra config and initialize adapters
        const infraResult = (0, InfraConfig_1.loadInfraConfig)(envName);
        this.registry.initialize(infraResult.config);
    }
    /**
     * Decide routing based on BuildPlan.cost_profile and InfraConfig.routing
     */
    decide(buildPlan) {
        const costProfile = buildPlan.cost_profile;
        // If no cost_profile, use routing.default
        if (!costProfile || typeof costProfile !== 'string') {
            const infraResult = (0, InfraConfig_1.loadInfraConfig)(this.envName);
            return {
                route: infraResult.config.routing.default,
                adapter: this.mapRouteToAdapter(infraResult.config.routing.default),
            };
        }
        // Normalize cost_profile
        const normalizedProfile = costProfile.trim().toLowerCase();
        // Map cost_profile to route
        let route;
        if (normalizedProfile === 'light') {
            route = 'serverless';
        }
        else if (normalizedProfile === 'ai-inference') {
            route = 'gpu-queue';
        }
        else if (normalizedProfile === 'batch') {
            route = 'batch';
        }
        else {
            // Fallback to routing.default
            const infraResult = (0, InfraConfig_1.loadInfraConfig)(this.envName);
            route = infraResult.config.routing.default;
        }
        return {
            route,
            adapter: this.mapRouteToAdapter(route),
            queueName: route === 'gpu-queue' ? 'gpu-queue' : route === 'batch' ? 'batch-queue' : undefined,
        };
    }
    /**
     * Route workload based on BuildPlan
     */
    async route(buildPlan, payload) {
        if (!this.registry.isEnabled()) {
            throw new Error('Infrastructure adapters are not enabled. Check feature_flags.');
        }
        const decision = this.decide(buildPlan);
        // Emit routing event
        const observability = this.registry.getObservability();
        if (observability) {
            await observability.emitMetric({
                name: 'workload.router.decision',
                value: 1,
                dimensions: {
                    route: decision.route,
                    adapter: decision.adapter,
                    cost_profile: buildPlan.cost_profile || 'default',
                },
                timestamp: new Date(),
            });
        }
        // Route based on decision
        switch (decision.adapter) {
            case 'serverless': {
                const serverless = this.registry.getServerless();
                if (!serverless) {
                    throw new Error('Serverless adapter not available');
                }
                // For serverless, we need a function name - use a default or extract from buildPlan
                const functionName = this.extractFunctionName(buildPlan) || 'default-handler';
                await serverless.invoke(functionName, payload);
                if (observability) {
                    await observability.emitMetric({
                        name: 'workload.router.executed',
                        value: 1,
                        dimensions: {
                            route: decision.route,
                            adapter: decision.adapter,
                        },
                        timestamp: new Date(),
                    });
                }
                break;
            }
            case 'queue': {
                const queue = this.registry.getQueue();
                if (!queue) {
                    throw new Error('Queue adapter not available');
                }
                const queueName = decision.queueName || 'default-queue';
                const messageBody = typeof payload === 'string' ? payload : JSON.stringify(payload);
                await queue.send(queueName, messageBody);
                if (observability) {
                    await observability.emitMetric({
                        name: 'workload.router.enqueued',
                        value: 1,
                        dimensions: {
                            route: decision.route,
                            adapter: decision.adapter,
                            queue_name: queueName,
                        },
                        timestamp: new Date(),
                    });
                }
                break;
            }
            case 'gpu-pool': {
                // For ai-inference: enqueue to gpu-queue, then GPU pool will consume
                const queue = this.registry.getQueue();
                if (!queue) {
                    throw new Error('Queue adapter not available');
                }
                const queueName = 'gpu-queue';
                const messageBody = typeof payload === 'string' ? payload : JSON.stringify(payload);
                await queue.send(queueName, messageBody);
                // Note: In a real implementation, a separate consumer would process gpu-queue
                // and allocate GPU instances. For now, we just enqueue.
                if (observability) {
                    await observability.emitMetric({
                        name: 'workload.router.enqueued',
                        value: 1,
                        dimensions: {
                            route: decision.route,
                            adapter: decision.adapter,
                            queue_name: queueName,
                        },
                        timestamp: new Date(),
                    });
                }
                break;
            }
            default:
                throw new Error(`Unknown adapter: ${decision.adapter}`);
        }
    }
    /**
     * Map route to adapter type
     */
    mapRouteToAdapter(route) {
        switch (route) {
            case 'serverless':
                return 'serverless';
            case 'gpu-queue':
                return 'gpu-pool';
            case 'batch':
                return 'queue';
            default:
                return 'queue';
        }
    }
    /**
     * Extract function name from BuildPlan (if available)
     */
    extractFunctionName(buildPlan) {
        // Try common fields that might contain function name
        if (typeof buildPlan.artifact_id === 'string') {
            return buildPlan.artifact_id;
        }
        if (typeof buildPlan.function_name === 'string') {
            return buildPlan.function_name;
        }
        return null;
    }
    /**
     * Get adapter registry (for testing)
     */
    getRegistry() {
        return this.registry;
    }
}
exports.WorkloadRouter = WorkloadRouter;
//# sourceMappingURL=WorkloadRouter.js.map