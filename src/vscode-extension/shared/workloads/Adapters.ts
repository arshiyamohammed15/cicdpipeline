/**
 * Cloud-agnostic adapter interfaces for workload orchestration.
 * These interfaces intentionally avoid any provider-specific concepts.
 */

export interface QueueAdapter<Message = unknown> {
    enqueue(message: Message): Promise<string>;
    ack(messageId: string): Promise<void>;
    nack(messageId: string, reason?: string): Promise<void>;
    requeue(messageId: string, delaySeconds?: number): Promise<void>;
}

export interface DeadLetterRecord<Message = unknown> {
    id: string;
    message: Message;
    failureReason?: string;
    firstFailedAt: Date;
    lastFailedAt: Date;
    deliveryCount: number;
}

export interface DLQAdapter<Message = unknown> {
    put(message: Message, reason?: string): Promise<void>;
    inspect(limit?: number): Promise<Array<DeadLetterRecord<Message>>>;
    reDrive(options?: { limit?: number; filterIds?: string[] }): Promise<void>;
}

export interface ServerlessInvocation<Task = unknown, Result = unknown> {
    task: Task;
    attempt?: number;
    correlationId?: string;
    payload?: Record<string, unknown>;
    result?: Result;
}

export interface ServerlessAdapter<Task = unknown, Result = unknown> {
    invoke(task: ServerlessInvocation<Task, Result>): Promise<Result>;
}

export interface GpuPoolMetrics {
    poolSize: number;
    available: number;
    pending: number;
    utilization: number;
    timestamp: Date;
}

export interface GpuPoolAdapter {
    scaleTo(desiredNodes: number): Promise<void>;
    metrics(): Promise<GpuPoolMetrics>;
}

export interface BuildPlanRoutingDescriptor {
    artifactId?: string;
    expectedArtifactDigest?: string;
    expectedSbomDigest?: string;
    costProfile?: string;
    routing?: string;
    policySnapshotId?: string;
}

export interface WorkloadRouter {
    selectPort(descriptor: BuildPlanRoutingDescriptor): Promise<number | string>;
}

