/**
 * LocalGpuPool
 *
 * Local simulation implementation of GpuPoolPort.
 * Simulates queue/capacity with metrics for pending/running.
 * Uses Promise-based completion delay.
 */
import { GpuPoolPort, GpuAllocationRequest, GpuInstance, GpuInstanceStatus, GpuPoolStats } from '../../ports/GpuPoolPort';
export declare class LocalGpuPool implements GpuPoolPort {
    private instances;
    private totalGpus;
    private availableGpus;
    private gpuTypes;
    private defaultGpuType;
    private defaultMemoryGB;
    private defaultCompletionDelay;
    constructor(totalGpus?: number, gpuTypes?: string[], defaultGpuType?: string, defaultMemoryGB?: number, defaultCompletionDelay?: number);
    allocate(request: GpuAllocationRequest): Promise<GpuInstance>;
    release(instanceId: string): Promise<void>;
    getStatus(instanceId: string): Promise<GpuInstanceStatus>;
    getPoolStats(): Promise<GpuPoolStats>;
    private simulateCompletion;
    private generateInstanceId;
    private sleep;
}
//# sourceMappingURL=LocalGpuPool.d.ts.map