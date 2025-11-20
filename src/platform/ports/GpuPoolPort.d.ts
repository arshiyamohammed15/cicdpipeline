/**
 * GpuPoolPort
 *
 * Cloud-agnostic interface for GPU pool management and allocation.
 * Implemented by local adapters for GPU resource management.
 *
 * @interface GpuPoolPort
 */
export interface GpuPoolPort {
    /**
     * Request GPU allocation from the pool.
     *
     * @param request - GPU allocation request
     * @returns Promise resolving to allocated GPU instance
     */
    allocate(request: GpuAllocationRequest): Promise<GpuInstance>;
    /**
     * Release a GPU instance back to the pool.
     *
     * @param instanceId - GPU instance ID to release
     * @returns Promise resolving when GPU is released
     */
    release(instanceId: string): Promise<void>;
    /**
     * Get status of a GPU instance.
     *
     * @param instanceId - GPU instance ID
     * @returns Promise resolving to GPU instance status
     */
    getStatus(instanceId: string): Promise<GpuInstanceStatus>;
    /**
     * Get pool statistics and availability.
     *
     * @returns Promise resolving to pool statistics
     */
    getPoolStats(): Promise<GpuPoolStats>;
}
/**
 * Request for GPU allocation.
 */
export interface GpuAllocationRequest {
    /** Minimum number of GPUs required */
    minGpus: number;
    /** Maximum number of GPUs desired */
    maxGpus?: number;
    /** GPU type/model requirements */
    gpuType?: string;
    /** Memory requirements per GPU (GB) */
    memoryGB?: number;
    /** Allocation timeout in seconds */
    timeoutSeconds?: number;
}
/**
 * Represents an allocated GPU instance.
 */
export interface GpuInstance {
    /** Unique instance ID */
    id: string;
    /** Number of GPUs allocated */
    gpuCount: number;
    /** GPU type/model */
    gpuType: string;
    /** Memory per GPU (GB) */
    memoryGB: number;
    /** Connection endpoint/address */
    endpoint: string;
    /** Allocation timestamp */
    allocatedAt: Date;
    /** Expiration timestamp */
    expiresAt?: Date;
}
/**
 * Status of a GPU instance.
 */
export interface GpuInstanceStatus {
    /** Instance ID */
    id: string;
    /** Current status */
    status: 'allocated' | 'in-use' | 'idle' | 'released' | 'error';
    /** GPU utilization percentage (0-100) */
    utilization?: number;
    /** Memory usage percentage (0-100) */
    memoryUsage?: number;
    /** Timestamp of last status update */
    lastUpdate: Date;
}
/**
 * GPU pool statistics and availability.
 */
export interface GpuPoolStats {
    /** Total GPUs in pool */
    totalGpus: number;
    /** Available GPUs */
    availableGpus: number;
    /** Allocated GPUs */
    allocatedGpus: number;
    /** GPUs in use */
    inUseGpus: number;
    /** GPU types available */
    gpuTypes: string[];
}
//# sourceMappingURL=GpuPoolPort.d.ts.map