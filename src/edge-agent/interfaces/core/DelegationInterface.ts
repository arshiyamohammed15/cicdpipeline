export interface DelegationInterface {
    /**
     * Delegate a task to this module
     * @param task The task to delegate
     * @returns Promise<any> The result of the delegation
     */
    delegate(task: any): Promise<any>;

    /**
     * Check if this module can handle the given task
     * @param task The task to check
     * @returns boolean True if this module can handle the task
     */
    canHandle(task: any): boolean;

    /**
     * Get the capabilities of this module
     * @returns string[] Array of capability strings
     */
    getCapabilities(): string[];

    /**
     * Get the current status of this module
     * @returns ModuleStatus The current status
     */
    getStatus(): ModuleStatus;
}

export interface ModuleStatus {
    name: string;
    isActive: boolean;
    isHealthy: boolean;
    lastActivity: Date;
    metrics: {
        tasksProcessed: number;
        averageLatency: number;
        errorRate: number;
    };
}

export interface DelegationTask {
    id: string;
    type: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
    data: any;
    requirements: {
        security?: boolean;
        performance?: boolean;
        compliance?: boolean;
    };
    timeout?: number;
    retryCount?: number;
}

export interface DelegationResult {
    taskId: string;
    success: boolean;
    result?: any;
    error?: string;
    processingTime: number;
    metadata: {
        module: string;
        timestamp: Date;
        securityValidated: boolean;
        dataIntegrity: boolean;
        performanceMetrics: {
            latency: number;
            memoryUsage: number;
            cpuUsage: number;
        };
    };
}
