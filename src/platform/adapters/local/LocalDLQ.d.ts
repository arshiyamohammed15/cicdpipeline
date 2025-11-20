/**
 * LocalDLQ
 *
 * Local file-based implementation of DLQPort using NDJSON files.
 */
/// <reference types="node" />
/// <reference types="node" />
import { DLQPort, DLQMessage, DLQMessageMetadata, DLQAttributes } from '../../ports/DLQPort';
export declare class LocalDLQ implements DLQPort {
    private baseDir;
    private defaultMaxReceiveCount;
    constructor(baseDir: string, defaultMaxReceiveCount?: number);
    sendFailedMessage(originalQueueName: string, message: string | Buffer, error: Error | string, metadata?: DLQMessageMetadata): Promise<string>;
    receiveFailedMessages(originalQueueName: string, maxMessages?: number): Promise<DLQMessage[]>;
    deleteFailedMessage(originalQueueName: string, receiptHandle: string): Promise<void>;
    getDLQAttributes(originalQueueName: string): Promise<DLQAttributes>;
    private getDLQFile;
    private ensureDirectory;
    private appendToJsonl;
    private updateDLQFile;
    private rewriteDLQFile;
    private generateMessageId;
    private generateReceiptHandle;
    private getMonotonicTime;
}
//# sourceMappingURL=LocalDLQ.d.ts.map