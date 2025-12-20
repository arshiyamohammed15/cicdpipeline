"use strict";
/**
 * LocalGpuPool
 *
 * Local simulation implementation of GpuPoolPort.
 * Simulates queue/capacity with metrics for pending/running.
 * Uses Promise-based completion delay.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.LocalGpuPool = void 0;
class LocalGpuPool {
    constructor(totalGpus = 8, gpuTypes = ['t4', 'v100'], defaultGpuType = 't4', defaultMemoryGB = 16, defaultCompletionDelay = 5000) {
        this.instances = new Map();
        this.totalGpus = totalGpus;
        this.availableGpus = totalGpus;
        this.gpuTypes = gpuTypes;
        this.defaultGpuType = defaultGpuType;
        this.defaultMemoryGB = defaultMemoryGB;
        this.defaultCompletionDelay = defaultCompletionDelay;
    }
    async allocate(request) {
        const requestedGpus = request.minGpus;
        const gpuType = request.gpuType || this.defaultGpuType;
        const memoryGB = request.memoryGB || this.defaultMemoryGB;
        if (!this.gpuTypes.includes(gpuType)) {
            throw new Error(`Unsupported GPU type: ${gpuType}`);
        }
        // If not enough GPUs, optionally wait until timeout expires
        if (requestedGpus > this.availableGpus) {
            if (!request.timeoutSeconds) {
                throw new Error(`Insufficient GPUs available. Requested: ${requestedGpus}, Available: ${this.availableGpus}`);
            }
            const timeout = request.timeoutSeconds * 1000;
            const startTime = Date.now();
            while (this.availableGpus < requestedGpus) {
                if (Date.now() - startTime > timeout) {
                    throw new Error('GPU allocation timeout');
                }
                await this.sleep(100); // Wait 100ms and retry
            }
        }
        const instanceId = this.generateInstanceId();
        const endpoint = `localhost:${8000 + this.instances.size}`;
        const allocatedAt = new Date();
        const expiresAt = request.timeoutSeconds
            ? new Date(allocatedAt.getTime() + request.timeoutSeconds * 1000)
            : undefined;
        const instance = {
            id: instanceId,
            gpuCount: requestedGpus,
            gpuType,
            memoryGB,
            endpoint,
            allocatedAt,
            expiresAt,
            status: 'allocated',
        };
        this.instances.set(instanceId, instance);
        this.availableGpus -= requestedGpus;
        // Simulate completion delay (auto-release after delay)
        instance.completionPromise = this.simulateCompletion(instanceId, this.defaultCompletionDelay);
        return {
            id: instanceId,
            gpuCount: requestedGpus,
            gpuType,
            memoryGB,
            endpoint,
            allocatedAt,
            expiresAt,
        };
    }
    async release(instanceId) {
        const instance = this.instances.get(instanceId);
        if (!instance) {
            throw new Error(`GPU instance ${instanceId} not found`);
        }
        this.availableGpus += instance.gpuCount;
        instance.status = 'released';
        this.instances.delete(instanceId);
    }
    async getStatus(instanceId) {
        const instance = this.instances.get(instanceId);
        if (!instance) {
            throw new Error(`GPU instance ${instanceId} not found`);
        }
        // Simulate utilization based on status
        let utilization = 0;
        let memoryUsage = 0;
        if (instance.status === 'in-use') {
            utilization = Math.floor(Math.random() * 40) + 60; // 60-100%
            memoryUsage = Math.floor(Math.random() * 20) + 70; // 70-90%
        }
        else if (instance.status === 'allocated' || instance.status === 'idle') {
            utilization = Math.floor(Math.random() * 10); // 0-10%
            memoryUsage = Math.floor(Math.random() * 10); // 0-10%
        }
        return {
            id: instanceId,
            status: instance.status,
            utilization,
            memoryUsage,
            lastUpdate: new Date(),
        };
    }
    async getPoolStats() {
        let allocatedGpus = 0;
        let inUseGpus = 0;
        for (const instance of this.instances.values()) {
            allocatedGpus += instance.gpuCount;
            if (instance.status === 'in-use') {
                inUseGpus += instance.gpuCount;
            }
        }
        return {
            totalGpus: this.totalGpus,
            availableGpus: this.availableGpus,
            allocatedGpus,
            inUseGpus,
            gpuTypes: this.gpuTypes,
        };
    }
    async simulateCompletion(instanceId, delay) {
        await this.sleep(delay);
        const instance = this.instances.get(instanceId);
        if (instance && instance.status !== 'released') {
            // Auto-release after delay
            await this.release(instanceId);
        }
    }
    generateInstanceId() {
        return `gpu-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
    }
    sleep(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }
}
exports.LocalGpuPool = LocalGpuPool;
//# sourceMappingURL=LocalGpuPool.js.map