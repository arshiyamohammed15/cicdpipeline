/**
 * QueuePort
 * 
 * Cloud-agnostic interface for message queue operations.
 * Implemented by local adapters for queue-based messaging.
 * 
 * @interface QueuePort
 */
export interface QueuePort {
  /**
   * Send a message to the queue.
   * 
   * @param queueName - Name of the queue
   * @param message - Message payload (serialized)
   * @param options - Optional queue-specific options (visibility timeout, delay, etc.)
   * @returns Promise resolving to message ID or receipt handle
   */
  send(
    queueName: string,
    message: string | Buffer,
    options?: QueueSendOptions
  ): Promise<string>;

  /**
   * Receive messages from the queue.
   * 
   * @param queueName - Name of the queue
   * @param maxMessages - Maximum number of messages to receive (default: 1)
   * @param options - Optional receive options (wait time, visibility timeout, etc.)
   * @returns Promise resolving to array of received messages
   */
  receive(
    queueName: string,
    maxMessages?: number,
    options?: QueueReceiveOptions
  ): Promise<QueueMessage[]>;

  /**
   * Delete a message from the queue after processing.
   * 
   * @param queueName - Name of the queue
   * @param receiptHandle - Message receipt handle from receive operation
   * @returns Promise resolving when message is deleted
   */
  delete(queueName: string, receiptHandle: string): Promise<void>;

  /**
   * Get queue attributes (approximate message count, visibility timeout, etc.).
   * 
   * @param queueName - Name of the queue
   * @returns Promise resolving to queue attributes
   */
  getAttributes(queueName: string): Promise<QueueAttributes>;
}

/**
 * Options for sending messages to a queue.
 */
export interface QueueSendOptions {
  /** Delay before message becomes visible (seconds) */
  delaySeconds?: number;
  /** Message attributes/metadata */
  attributes?: Record<string, string>;
}

/**
 * Options for receiving messages from a queue.
 */
export interface QueueReceiveOptions {
  /** Maximum wait time for messages (seconds) */
  waitTimeSeconds?: number;
  /** Visibility timeout for received messages (seconds) */
  visibilityTimeout?: number;
}

/**
 * Represents a message received from a queue.
 */
export interface QueueMessage {
  /** Message ID */
  id: string;
  /** Receipt handle for deletion */
  receiptHandle: string;
  /** Message body */
  body: string | Buffer;
  /** Message attributes */
  attributes?: Record<string, string>;
  /** Approximate receive count */
  receiveCount?: number;
}

/**
 * Queue attributes and metadata.
 */
export interface QueueAttributes {
  /** Approximate number of messages in queue */
  approximateMessageCount?: number;
  /** Visibility timeout (seconds) */
  visibilityTimeout?: number;
  /** Message retention period (seconds) */
  messageRetentionPeriod?: number;
  /** Maximum message size (bytes) */
  maxMessageSize?: number;
}

