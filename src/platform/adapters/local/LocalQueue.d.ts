/**
 * LocalQueue
 *
 * Local file-based implementation of QueuePort using NDJSON files.
 * Implements ack/nack/retry/backoff and integrates with LocalDLQ.
 */
/// <reference types="node" />
/// <reference types="node" />
import { QueuePort, QueueSendOptions, QueueReceiveOptions, QueueMessage, QueueAttributes } from '../../ports/QueuePort';
import { DLQPort } from '../../ports/DLQPort';
export declare class LocalQueue implements QueuePort {
    private baseDir;
    private dlq;
    private maxReceiveCount;
    private defaultVisibilityTimeout;
    constructor(baseDir: string, dlq?: DLQPort, maxReceiveCount?: number, defaultVisibilityTimeout?: number);
    send(queueName: string, message: string | Buffer, options?: QueueSendOptions): Promise<string>;
    receive(queueName: string, maxMessages?: number, options?: QueueReceiveOptions): Promise<QueueMessage[]>;
    delete(queueName: string, receiptHandle: string): Promise<void>;
    getAttributes(queueName: string): Promise<QueueAttributes>;
    /**
     * Acknowledge a message (delete it).
     */
    ack(queueName: string, receiptHandle: string): Promise<void>;
    /**
     * Negative acknowledge (nack) - return message to queue with backoff.
     */
    nack(queueName: string, receiptHandle: string, retry?: boolean): Promise<void>;
    private getQueueFile;
    private ensureDirectory;
    private appendToJsonl;
    private updateQueueFile;
    private rewriteQueueFile;
    private generateMessageId;
    private generateReceiptHandle;
    private getMonotonicTime;
    private sleep;
}
//# sourceMappingURL=LocalQueue.d.ts.map