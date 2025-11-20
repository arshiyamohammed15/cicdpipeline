"use strict";
/**
 * LocalDLQ
 *
 * Local file-based implementation of DLQPort using NDJSON files.
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
exports.LocalDLQ = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class LocalDLQ {
    constructor(baseDir, defaultMaxReceiveCount = 3) {
        this.baseDir = baseDir;
        this.defaultMaxReceiveCount = defaultMaxReceiveCount;
    }
    async sendFailedMessage(originalQueueName, message, error, metadata) {
        const dlqFile = this.getDLQFile(originalQueueName);
        await this.ensureDirectory(path.dirname(dlqFile));
        const messageId = this.generateMessageId();
        const errorMessage = error instanceof Error ? error.message : error;
        const record = {
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
    async receiveFailedMessages(originalQueueName, maxMessages = 1) {
        const dlqFile = this.getDLQFile(originalQueueName);
        if (!fs.existsSync(dlqFile)) {
            return [];
        }
        const content = fs.readFileSync(dlqFile, 'utf-8');
        const lines = content.split('\n').filter((line) => line.trim());
        const messages = [];
        const receiptHandles = [];
        const now = this.getMonotonicTime();
        for (const line of lines) {
            if (messages.length >= maxMessages) {
                break;
            }
            try {
                const record = JSON.parse(line);
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
            }
            catch (error) {
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
    async deleteFailedMessage(originalQueueName, receiptHandle) {
        const dlqFile = this.getDLQFile(originalQueueName);
        if (!fs.existsSync(dlqFile)) {
            return;
        }
        const content = fs.readFileSync(dlqFile, 'utf-8');
        const lines = content.split('\n').filter((line) => line.trim());
        const updatedRecords = [];
        for (const line of lines) {
            try {
                const record = JSON.parse(line);
                if (record.receiptHandle === receiptHandle) {
                    // Delete this message
                    continue;
                }
                updatedRecords.push(record);
            }
            catch (error) {
                // Keep invalid lines
                continue;
            }
        }
        await this.rewriteDLQFile(dlqFile, updatedRecords);
    }
    async getDLQAttributes(originalQueueName) {
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
                const record = JSON.parse(line);
                // Count only non-received messages
                if (!record.receiptHandle) {
                    messageCount++;
                }
            }
            catch (error) {
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
    getDLQFile(originalQueueName) {
        return path.join(this.baseDir, 'dlq', `${originalQueueName}.dlq.jsonl`);
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
    async updateDLQFile(filePath, lines) {
        const updatedRecords = [];
        for (const line of lines) {
            try {
                updatedRecords.push(JSON.parse(line));
            }
            catch (error) {
                // Keep invalid lines
                continue;
            }
        }
        await this.rewriteDLQFile(filePath, updatedRecords);
    }
    async rewriteDLQFile(filePath, records) {
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
        return `dlq-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
    }
    generateReceiptHandle() {
        return `dlq-receipt-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
    }
    getMonotonicTime() {
        return Date.now();
    }
}
exports.LocalDLQ = LocalDLQ;
//# sourceMappingURL=LocalDLQ.js.map