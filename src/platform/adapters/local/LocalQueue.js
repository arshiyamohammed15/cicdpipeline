"use strict";
/**
 * LocalQueue
 *
 * Local file-based implementation of QueuePort using NDJSON files.
 * Implements ack/nack/retry/backoff and integrates with LocalDLQ.
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.LocalQueue = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class LocalQueue {
    constructor(baseDir, dlq, maxReceiveCount = 3, defaultVisibilityTimeout = 30) {
        this.baseDir = baseDir;
        this.dlq = dlq || null;
        this.maxReceiveCount = maxReceiveCount;
        this.defaultVisibilityTimeout = defaultVisibilityTimeout;
    }
    async send(queueName, message, options) {
        const queueFile = this.getQueueFile(queueName);
        await this.ensureDirectory(path.dirname(queueFile));
        const messageId = this.generateMessageId();
        const now = this.getMonotonicTime();
        const delaySeconds = options?.delaySeconds || 0;
        const visibleAt = now + delaySeconds * 1000;
        const record = {
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
    async receive(queueName, maxMessages = 1, options) {
        const queueFile = this.getQueueFile(queueName);
        if (!fs.existsSync(queueFile)) {
            return [];
        }
        const visibilityTimeout = (options?.visibilityTimeout || this.defaultVisibilityTimeout) * 1000;
        const waitTimeSeconds = options?.waitTimeSeconds || 0;
        const waitUntil = this.getMonotonicTime() + waitTimeSeconds * 1000;
        const messages = [];
        const now = this.getMonotonicTime();
        const allRecords = [];
        const processedReceiptHandles = new Set();
        // Read all messages
        const content = fs.readFileSync(queueFile, 'utf-8');
        const lines = content.split('\n').filter((line) => line.trim());
        for (const line of lines) {
            try {
                const record = JSON.parse(line);
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
            }
            catch (error) {
                // Skip invalid lines
                continue;
            }
        }
        // Filter available messages (not currently visible)
        const availableRecords = allRecords.filter((record) => !record.receiptHandle || (record.receivedAt && now >= record.receivedAt + visibilityTimeout));
        // Wait if no messages available
        if (availableRecords.length === 0 && waitTimeSeconds > 0) {
            await this.sleep(Math.min(waitTimeSeconds * 1000, 1000)); // Max 1 second wait per iteration
            if (this.getMonotonicTime() < waitUntil) {
                return this.receive(queueName, maxMessages, options);
            }
        }
        // Take up to maxMessages
        const toReceive = availableRecords.slice(0, maxMessages);
        const receiptHandles = [];
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
    async delete(queueName, receiptHandle) {
        const queueFile = this.getQueueFile(queueName);
        if (!fs.existsSync(queueFile)) {
            return;
        }
        const content = fs.readFileSync(queueFile, 'utf-8');
        const lines = content.split('\n').filter((line) => line.trim());
        const updatedRecords = [];
        for (const line of lines) {
            try {
                const record = JSON.parse(line);
                if (record.receiptHandle === receiptHandle) {
                    // Delete this message (don't add to updatedRecords)
                    continue;
                }
                updatedRecords.push(record);
            }
            catch (error) {
                // Keep invalid lines (don't lose data)
                continue;
            }
        }
        // Rewrite queue file
        await this.rewriteQueueFile(queueFile, updatedRecords);
    }
    async getAttributes(queueName) {
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
                const record = JSON.parse(line);
                // Count only visible messages (not in visibility timeout)
                if (!record.receiptHandle || !record.receivedAt) {
                    if (record.visibleAt <= now) {
                        messageCount++;
                    }
                }
                else {
                    const visibilityExpires = record.receivedAt + this.defaultVisibilityTimeout * 1000;
                    if (now >= visibilityExpires) {
                        messageCount++;
                    }
                }
            }
            catch (error) {
                // Skip invalid lines
                continue;
            }
        }
        return {
            approximateMessageCount: messageCount,
            visibilityTimeout: this.defaultVisibilityTimeout,
            messageRetentionPeriod: 86400 * 7,
            maxMessageSize: 256 * 1024, // 256 KB default
        };
    }
    /**
     * Acknowledge a message (delete it).
     */
    async ack(queueName, receiptHandle) {
        return this.delete(queueName, receiptHandle);
    }
    /**
     * Negative acknowledge (nack) - return message to queue with backoff.
     */
    async nack(queueName, receiptHandle, retry = true) {
        const queueFile = this.getQueueFile(queueName);
        if (!fs.existsSync(queueFile)) {
            return;
        }
        const content = fs.readFileSync(queueFile, 'utf-8');
        const lines = content.split('\n').filter((line) => line.trim());
        const updatedRecords = [];
        let nackedRecord = null;
        for (const line of lines) {
            try {
                const record = JSON.parse(line);
                if (record.receiptHandle === receiptHandle) {
                    nackedRecord = record;
                    if (retry && record.receiveCount < this.maxReceiveCount) {
                        // Exponential backoff: 2^receiveCount seconds
                        const backoffSeconds = Math.pow(2, record.receiveCount);
                        record.visibleAt = this.getMonotonicTime() + backoffSeconds * 1000;
                        record.receiptHandle = undefined;
                        record.receivedAt = undefined;
                        updatedRecords.push(record);
                    }
                    else if (this.dlq && record.receiveCount >= this.maxReceiveCount) {
                        // Move to DLQ
                        const bodyStr = typeof record.body === 'string' ? record.body : record.body.toString();
                        const messageBody = bodyStr.startsWith('base64:')
                            ? Buffer.from(bodyStr.substring(7), 'base64')
                            : bodyStr;
                        await this.dlq.sendFailedMessage(queueName, messageBody, 'Max receive count exceeded', {
                            receiveCount: record.receiveCount,
                            failedAt: new Date(),
                            originalQueueName: queueName,
                        });
                        // Don't add to updatedRecords (message moved to DLQ)
                    }
                    // If retry is false and no DLQ, message is dropped
                }
                else {
                    updatedRecords.push(record);
                }
            }
            catch (error) {
                // Keep invalid lines
                continue;
            }
        }
        await this.rewriteQueueFile(queueFile, updatedRecords);
    }
    getQueueFile(queueName) {
        return path.join(this.baseDir, 'queues', `${queueName}.jsonl`);
    }
    async ensureDirectory(dirPath) {
        await fs.promises.mkdir(dirPath, { recursive: true });
    }
    async appendToJsonl(filePath, jsonContent) {
        try {
            await fs.promises.open(filePath, 'ax').then((handle) => handle.close());
        }
        catch (error) {
            const err = error;
            if (err.code !== 'EEXIST') {
                throw err;
            }
        }
        const line = `${jsonContent}\n`;
        const handle = await fs.promises.open(filePath, 'a');
        try {
            await handle.write(line);
            await handle.sync();
        }
        finally {
            await handle.close();
        }
    }
    async updateQueueFile(filePath, records) {
        await this.rewriteQueueFile(filePath, records);
    }
    async rewriteQueueFile(filePath, records) {
        const lines = records.map((record) => JSON.stringify(record));
        const content = lines.join('\n') + (lines.length > 0 ? '\n' : '');
        await fs.promises.writeFile(filePath, content, 'utf-8');
        const handle = await fs.promises.open(filePath, 'r+');
        try {
            await handle.sync();
        }
        finally {
            await handle.close();
        }
    }
    generateMessageId() {
        return `msg-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
    }
    generateReceiptHandle() {
        return `receipt-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
    }
    getMonotonicTime() {
        return Date.now();
    }
    sleep(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }
}
exports.LocalQueue = LocalQueue;
//# sourceMappingURL=LocalQueue.js.map