/**
 * LocalQueue
 * 
 * Local file-based implementation of QueuePort using NDJSON files.
 * Implements ack/nack/retry/backoff and integrates with LocalDLQ.
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  QueuePort,
  QueueSendOptions,
  QueueReceiveOptions,
  QueueMessage,
  QueueAttributes,
} from '../../ports/QueuePort';
import { DLQPort } from '../../ports/DLQPort';

interface QueueMessageRecord {
  id: string;
  body: string | Buffer;
  attributes?: Record<string, string>;
  sentAt: number; // monotonic timestamp
  visibleAt: number; // when message becomes visible (for delay)
  receiveCount: number;
  receiptHandle?: string; // set when received
  receivedAt?: number; // when received (for visibility timeout)
}

export class LocalQueue implements QueuePort {
  private baseDir: string;
  private dlq: DLQPort | null;
  private maxReceiveCount: number;
  private defaultVisibilityTimeout: number;

  constructor(
    baseDir: string,
    dlq?: DLQPort,
    maxReceiveCount: number = 3,
    defaultVisibilityTimeout: number = 30
  ) {
    this.baseDir = baseDir;
    this.dlq = dlq || null;
    this.maxReceiveCount = maxReceiveCount;
    this.defaultVisibilityTimeout = defaultVisibilityTimeout;
  }

  async send(
    queueName: string,
    message: string | Buffer,
    options?: QueueSendOptions
  ): Promise<string> {
    const queueFile = this.getQueueFile(queueName);
    await this.ensureDirectory(path.dirname(queueFile));

    const messageId = this.generateMessageId();
    const now = this.getMonotonicTime();
    const delaySeconds = options?.delaySeconds || 0;
    const visibleAt = now + delaySeconds * 1000;

    const record: QueueMessageRecord = {
      id: messageId,
      body: typeof message === 'string' ? message : `base64:${message.toString('base64')}`,
      attributes: options?.attributes,
      sentAt: now,
      visibleAt,
      receiveCount: 0,
    };

    await this.appendToJsonl(queueFile, JSON.stringify(record));
    return messageId;
  }

  async receive(
    queueName: string,
    maxMessages: number = 1,
    options?: QueueReceiveOptions
  ): Promise<QueueMessage[]> {
    const queueFile = this.getQueueFile(queueName);
    if (!fs.existsSync(queueFile)) {
      return [];
    }

    const visibilityTimeout = (options?.visibilityTimeout || this.defaultVisibilityTimeout) * 1000;
    const waitTimeSeconds = options?.waitTimeSeconds || 0;
    const waitUntil = this.getMonotonicTime() + waitTimeSeconds * 1000;

    const messages: QueueMessage[] = [];
    const now = this.getMonotonicTime();
    const allRecords: QueueMessageRecord[] = [];
    const processedReceiptHandles = new Set<string>();

    // Read all messages
    const content = fs.readFileSync(queueFile, 'utf-8');
    const lines = content.split('\n').filter((line) => line.trim());

    for (const line of lines) {
      try {
        const record: QueueMessageRecord = JSON.parse(line);
        // Skip if already processed (has receipt handle and not expired)
        if (record.receiptHandle && record.receivedAt) {
          const visibilityExpires = record.receivedAt + visibilityTimeout;
          if (now < visibilityExpires) {
            processedReceiptHandles.add(record.receiptHandle);
            continue;
          }
        }
        // Skip if not yet visible (delay)
        if (record.visibleAt > now) {
          continue;
        }
        allRecords.push(record);
      } catch (error) {
        // Skip invalid lines
        continue;
      }
    }

    // Filter available messages (not currently visible)
    const availableRecords = allRecords.filter(
      (record) => !record.receiptHandle || (record.receivedAt && now >= record.receivedAt + visibilityTimeout)
    );

    // Wait if no messages available
    if (availableRecords.length === 0 && waitTimeSeconds > 0) {
      await this.sleep(Math.min(waitTimeSeconds * 1000, 1000)); // Max 1 second wait per iteration
      if (this.getMonotonicTime() < waitUntil) {
        return this.receive(queueName, maxMessages, options);
      }
    }

    // Take up to maxMessages
    const toReceive = availableRecords.slice(0, maxMessages);
    const receiptHandles: string[] = [];

    for (const record of toReceive) {
      const receiptHandle = this.generateReceiptHandle();
      receiptHandles.push(receiptHandle);

      record.receiptHandle = receiptHandle;
      record.receivedAt = now;
      record.receiveCount = (record.receiveCount || 0) + 1;

      const bodyStr = typeof record.body === 'string' ? record.body : record.body.toString();
      const body = bodyStr.startsWith('base64:') 
        ? Buffer.from(bodyStr.substring(7), 'base64')
        : bodyStr;

      messages.push({
        id: record.id,
        receiptHandle,
        body,
        attributes: record.attributes,
        receiveCount: record.receiveCount,
      });
    }

    // Update queue file with new receipt handles
    if (receiptHandles.length > 0) {
      await this.updateQueueFile(queueFile, allRecords);
    }

    return messages;
  }

  async delete(queueName: string, receiptHandle: string): Promise<void> {
    const queueFile = this.getQueueFile(queueName);
    if (!fs.existsSync(queueFile)) {
      return;
    }

    const content = fs.readFileSync(queueFile, 'utf-8');
    const lines = content.split('\n').filter((line) => line.trim());
    const updatedRecords: QueueMessageRecord[] = [];

    for (const line of lines) {
      try {
        const record: QueueMessageRecord = JSON.parse(line);
        if (record.receiptHandle === receiptHandle) {
          // Delete this message (don't add to updatedRecords)
          continue;
        }
        updatedRecords.push(record);
      } catch (error) {
        // Keep invalid lines (don't lose data)
        continue;
      }
    }

    // Rewrite queue file
    await this.rewriteQueueFile(queueFile, updatedRecords);
  }

  async getAttributes(queueName: string): Promise<QueueAttributes> {
    const queueFile = this.getQueueFile(queueName);
    if (!fs.existsSync(queueFile)) {
      return {
        approximateMessageCount: 0,
        visibilityTimeout: this.defaultVisibilityTimeout,
      };
    }

    const content = fs.readFileSync(queueFile, 'utf-8');
    const lines = content.split('\n').filter((line) => line.trim());
    const now = this.getMonotonicTime();
    let messageCount = 0;

    for (const line of lines) {
      try {
        const record: QueueMessageRecord = JSON.parse(line);
        // Count only visible messages (not in visibility timeout)
        if (!record.receiptHandle || !record.receivedAt) {
          if (record.visibleAt <= now) {
            messageCount++;
          }
        } else {
          const visibilityExpires = record.receivedAt + this.defaultVisibilityTimeout * 1000;
          if (now >= visibilityExpires) {
            messageCount++;
          }
        }
      } catch (error) {
        // Skip invalid lines
        continue;
      }
    }

    return {
      approximateMessageCount: messageCount,
      visibilityTimeout: this.defaultVisibilityTimeout,
      messageRetentionPeriod: 86400 * 7, // 7 days default
      maxMessageSize: 256 * 1024, // 256 KB default
    };
  }

  /**
   * Acknowledge a message (delete it).
   */
  async ack(queueName: string, receiptHandle: string): Promise<void> {
    return this.delete(queueName, receiptHandle);
  }

  /**
   * Negative acknowledge (nack) - return message to queue with backoff.
   */
  async nack(queueName: string, receiptHandle: string, retry: boolean = true): Promise<void> {
    const queueFile = this.getQueueFile(queueName);
    if (!fs.existsSync(queueFile)) {
      return;
    }

    const content = fs.readFileSync(queueFile, 'utf-8');
    const lines = content.split('\n').filter((line) => line.trim());
    const updatedRecords: QueueMessageRecord[] = [];
    let nackedRecord: QueueMessageRecord | null = null;

    for (const line of lines) {
      try {
        const record: QueueMessageRecord = JSON.parse(line);
        if (record.receiptHandle === receiptHandle) {
          nackedRecord = record;
          if (retry && record.receiveCount < this.maxReceiveCount) {
            // Exponential backoff: 2^receiveCount seconds
            const backoffSeconds = Math.pow(2, record.receiveCount);
            record.visibleAt = this.getMonotonicTime() + backoffSeconds * 1000;
            record.receiptHandle = undefined;
            record.receivedAt = undefined;
            updatedRecords.push(record);
          } else if (this.dlq && record.receiveCount >= this.maxReceiveCount) {
            // Move to DLQ
            const bodyStr = typeof record.body === 'string' ? record.body : record.body.toString();
            const messageBody = bodyStr.startsWith('base64:')
              ? Buffer.from(bodyStr.substring(7), 'base64')
              : bodyStr;
            await this.dlq.sendFailedMessage(
              queueName,
              messageBody,
              'Max receive count exceeded',
              {
                receiveCount: record.receiveCount,
                failedAt: new Date(),
                originalQueueName: queueName,
              }
            );
            // Don't add to updatedRecords (message moved to DLQ)
          }
          // If retry is false and no DLQ, message is dropped
        } else {
          updatedRecords.push(record);
        }
      } catch (error) {
        // Keep invalid lines
        continue;
      }
    }

    await this.rewriteQueueFile(queueFile, updatedRecords);
  }

  private getQueueFile(queueName: string): string {
    return path.join(this.baseDir, 'queues', `${queueName}.jsonl`);
  }

  private async ensureDirectory(dirPath: string): Promise<void> {
    await fs.promises.mkdir(dirPath, { recursive: true });
  }

  private async appendToJsonl(filePath: string, jsonContent: string): Promise<void> {
    try {
      await fs.promises.open(filePath, 'ax').then((handle) => handle.close());
    } catch (error) {
      const err = error as NodeJS.ErrnoException;
      if (err.code !== 'EEXIST') {
        throw err;
      }
    }

    const line = `${jsonContent}\n`;
    const handle = await fs.promises.open(filePath, 'a');
    try {
      await handle.write(line);
      await handle.sync();
    } finally {
      await handle.close();
    }
  }

  private async updateQueueFile(
    filePath: string,
    records: QueueMessageRecord[]
  ): Promise<void> {
    await this.rewriteQueueFile(filePath, records);
  }

  private async rewriteQueueFile(
    filePath: string,
    records: QueueMessageRecord[]
  ): Promise<void> {
    const lines = records.map((record) => JSON.stringify(record));
    const content = lines.join('\n') + (lines.length > 0 ? '\n' : '');
    await fs.promises.writeFile(filePath, content, 'utf-8');
    const handle = await fs.promises.open(filePath, 'r+');
    try {
      await handle.sync();
    } finally {
      await handle.close();
    }
  }

  private generateMessageId(): string {
    return `msg-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
  }

  private generateReceiptHandle(): string {
    return `receipt-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
  }

  private getMonotonicTime(): number {
    return Date.now();
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

