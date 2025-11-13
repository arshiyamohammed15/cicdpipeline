/**
 * LocalDLQ
 *
 * Local file-based implementation of DLQPort using NDJSON files.
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  DLQPort,
  DLQMessage,
  DLQMessageMetadata,
  DLQAttributes,
} from '../../ports/DLQPort';

interface DLQMessageRecord {
  id: string;
  originalMessage: string | Buffer;
  error: string;
  metadata: DLQMessageMetadata;
  receiptHandle?: string;
  receivedAt?: number;
}

export class LocalDLQ implements DLQPort {
  private baseDir: string;
  private defaultMaxReceiveCount: number;

  constructor(baseDir: string, defaultMaxReceiveCount: number = 3) {
    this.baseDir = baseDir;
    this.defaultMaxReceiveCount = defaultMaxReceiveCount;
  }

  async sendFailedMessage(
    originalQueueName: string,
    message: string | Buffer,
    error: Error | string,
    metadata?: DLQMessageMetadata
  ): Promise<string> {
    const dlqFile = this.getDLQFile(originalQueueName);
    await this.ensureDirectory(path.dirname(dlqFile));

    const messageId = this.generateMessageId();
    const errorMessage = error instanceof Error ? error.message : error;

    const record: DLQMessageRecord = {
      id: messageId,
      originalMessage: typeof message === 'string' ? message : `base64:${message.toString('base64')}`,
      error: errorMessage,
      metadata: metadata || {
        receiveCount: 0,
        failedAt: new Date(),
        originalQueueName,
      },
    };

    await this.appendToJsonl(dlqFile, JSON.stringify(record));
    return messageId;
  }

  async receiveFailedMessages(
    originalQueueName: string,
    maxMessages: number = 1
  ): Promise<DLQMessage[]> {
    const dlqFile = this.getDLQFile(originalQueueName);
    if (!fs.existsSync(dlqFile)) {
      return [];
    }

    const content = fs.readFileSync(dlqFile, 'utf-8');
    const lines = content.split('\n').filter((line) => line.trim());
    const messages: DLQMessage[] = [];
    const receiptHandles: string[] = [];
    const now = this.getMonotonicTime();

    for (const line of lines) {
      if (messages.length >= maxMessages) {
        break;
      }

      try {
        const record: DLQMessageRecord = JSON.parse(line);
        // Skip if already received (has receipt handle)
        if (record.receiptHandle) {
          continue;
        }

        const receiptHandle = this.generateReceiptHandle();
        receiptHandles.push(receiptHandle);
        record.receiptHandle = receiptHandle;
        record.receivedAt = now;

        const msgStr = typeof record.originalMessage === 'string' ? record.originalMessage : record.originalMessage.toString();
        const originalMessage = msgStr.startsWith('base64:')
          ? Buffer.from(msgStr.substring(7), 'base64')
          : msgStr;

        messages.push({
          id: record.id,
          receiptHandle,
          originalMessage,
          error: record.error,
          metadata: record.metadata,
        });
      } catch (error) {
        // Skip invalid lines
        continue;
      }
    }

    // Update DLQ file with receipt handles
    if (receiptHandles.length > 0) {
      await this.updateDLQFile(dlqFile, lines);
    }

    return messages;
  }

  async deleteFailedMessage(originalQueueName: string, receiptHandle: string): Promise<void> {
    const dlqFile = this.getDLQFile(originalQueueName);
    if (!fs.existsSync(dlqFile)) {
      return;
    }

    const content = fs.readFileSync(dlqFile, 'utf-8');
    const lines = content.split('\n').filter((line) => line.trim());
    const updatedRecords: DLQMessageRecord[] = [];

    for (const line of lines) {
      try {
        const record: DLQMessageRecord = JSON.parse(line);
        if (record.receiptHandle === receiptHandle) {
          // Delete this message
          continue;
        }
        updatedRecords.push(record);
      } catch (error) {
        // Keep invalid lines
        continue;
      }
    }

    await this.rewriteDLQFile(dlqFile, updatedRecords);
  }

  async getDLQAttributes(originalQueueName: string): Promise<DLQAttributes> {
    const dlqFile = this.getDLQFile(originalQueueName);
    if (!fs.existsSync(dlqFile)) {
      return {
        approximateMessageCount: 0,
        maxReceiveCount: this.defaultMaxReceiveCount,
      };
    }

    const content = fs.readFileSync(dlqFile, 'utf-8');
    const lines = content.split('\n').filter((line) => line.trim());
    let messageCount = 0;

    for (const line of lines) {
      try {
        const record: DLQMessageRecord = JSON.parse(line);
        // Count only non-received messages
        if (!record.receiptHandle) {
          messageCount++;
        }
      } catch (error) {
        // Skip invalid lines
        continue;
      }
    }

    return {
      approximateMessageCount: messageCount,
      maxReceiveCount: this.defaultMaxReceiveCount,
      messageRetentionPeriod: 86400 * 30, // 30 days default
    };
  }

  private getDLQFile(originalQueueName: string): string {
    return path.join(this.baseDir, 'dlq', `${originalQueueName}.dlq.jsonl`);
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

  private async updateDLQFile(filePath: string, lines: string[]): Promise<void> {
    const updatedRecords: DLQMessageRecord[] = [];
    for (const line of lines) {
      try {
        updatedRecords.push(JSON.parse(line));
      } catch (error) {
        // Keep invalid lines
        continue;
      }
    }
    await this.rewriteDLQFile(filePath, updatedRecords);
  }

  private async rewriteDLQFile(filePath: string, records: DLQMessageRecord[]): Promise<void> {
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
    return `dlq-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
  }

  private generateReceiptHandle(): string {
    return `dlq-receipt-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
  }

  private getMonotonicTime(): number {
    return Date.now();
  }
}
