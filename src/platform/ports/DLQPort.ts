/**
 * DLQPort
 * 
 * Cloud-agnostic interface for Dead Letter Queue (DLQ) operations.
 * Implemented by local adapters for handling failed messages.
 * 
 * @interface DLQPort
 */
export interface DLQPort {
  /**
   * Send a failed message to the dead letter queue.
   * 
   * @param originalQueueName - Name of the original queue where message failed
   * @param message - Original message that failed processing
   * @param error - Error that caused the failure
   * @param metadata - Additional metadata about the failure (receive count, timestamp, etc.)
   * @returns Promise resolving to DLQ message ID
   */
  sendFailedMessage(
    originalQueueName: string,
    message: string | Buffer,
    error: Error | string,
    metadata?: DLQMessageMetadata
  ): Promise<string>;

  /**
   * Receive messages from the dead letter queue for analysis/reprocessing.
   * 
   * @param originalQueueName - Name of the original queue (to filter DLQ messages)
   * @param maxMessages - Maximum number of messages to receive (default: 1)
   * @returns Promise resolving to array of DLQ messages
   */
  receiveFailedMessages(
    originalQueueName: string,
    maxMessages?: number
  ): Promise<DLQMessage[]>;

  /**
   * Delete a message from the dead letter queue.
   * 
   * @param originalQueueName - Name of the original queue
   * @param receiptHandle - DLQ message receipt handle
   * @returns Promise resolving when message is deleted
   */
  deleteFailedMessage(originalQueueName: string, receiptHandle: string): Promise<void>;

  /**
   * Get DLQ attributes and statistics.
   * 
   * @param originalQueueName - Name of the original queue
   * @returns Promise resolving to DLQ attributes
   */
  getDLQAttributes(originalQueueName: string): Promise<DLQAttributes>;
}

/**
 * Metadata about a failed message sent to DLQ.
 */
export interface DLQMessageMetadata {
  /** Number of times message was received before failure */
  receiveCount: number;
  /** Timestamp when message first entered queue */
  firstReceivedAt?: Date;
  /** Timestamp when message failed */
  failedAt: Date;
  /** Original queue name */
  originalQueueName: string;
  /** Additional context about the failure */
  context?: Record<string, unknown>;
}

/**
 * Represents a message in the dead letter queue.
 */
export interface DLQMessage {
  /** DLQ message ID */
  id: string;
  /** Receipt handle for deletion */
  receiptHandle: string;
  /** Original message body */
  originalMessage: string | Buffer;
  /** Error that caused the failure */
  error: string;
  /** Failure metadata */
  metadata: DLQMessageMetadata;
}

/**
 * Dead letter queue attributes and statistics.
 */
export interface DLQAttributes {
  /** Approximate number of failed messages in DLQ */
  approximateMessageCount?: number;
  /** Maximum receive count threshold before moving to DLQ */
  maxReceiveCount?: number;
  /** Message retention period (seconds) */
  messageRetentionPeriod?: number;
}

