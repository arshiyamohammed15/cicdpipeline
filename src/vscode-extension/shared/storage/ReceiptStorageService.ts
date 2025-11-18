import * as fs from 'fs';
import * as path from 'path';
import { StoragePathResolver } from './StoragePathResolver';
import { DecisionReceipt, FeedbackReceipt } from '../receipt-parser/ReceiptParser';

export class ReceiptStorageService {
    private pathResolver: StoragePathResolver;

    constructor(zuRoot?: string) {
        this.pathResolver = new StoragePathResolver(zuRoot);
    }

    public async storeDecisionReceipt(
        receipt: DecisionReceipt,
        repoId: string
    ): Promise<string> {
        const date = new Date(receipt.timestamp_utc);
        const year = date.getUTCFullYear();
        const month = date.getUTCMonth() + 1;

        const receiptDir = this.pathResolver.resolveReceiptPath(repoId, year, month);
        const receiptFile = `${receiptDir}/receipts.jsonl`;

        await this.ensureDirectoryExists(receiptDir);

        if (!receipt.signature || receipt.signature.length === 0) {
            throw new Error('Receipt must be signed before storage (Rule 224)');
        }

        this.validateNoCodeOrPII(receipt);

        const receiptJson = JSON.stringify(receipt, null, 0);
        await this.appendToJsonl(receiptFile, receiptJson);

        return receiptFile;
    }

    /**
     * Append a single JSONL line in append-only mode.
     * Ensures the file descriptor is fsync'ed before close (WORM continuity).
     * Previously: fs.createWriteStream(..., { flags: 'a' }) [DISCOVERY: single site]
     */
    private async appendToJsonl(filePath: string, jsonContent: string): Promise<void> {
        try {
            const createHandle = await fs.promises.open(filePath, 'ax');
            await createHandle.close();
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

    private validateNoCodeOrPII(receipt: DecisionReceipt | FeedbackReceipt): void {
        const receiptStr = JSON.stringify(receipt);

        const codePatterns = [
            /\bfunction\s+\w+\s*\(/,
            /\bfunction\s*\(/,
            /\bclass\s+\w+/,
            /\bimport\s+.*from/,
            /\bexport\s+/,
            /<script>/i,
            /<style>/i
        ];

        for (const pattern of codePatterns) {
            if (pattern.test(receiptStr)) {
                throw new Error('Receipt contains executable code (violates Rule 217: No Code/PII in Stores)');
            }
        }

        const piiPatterns = [
            /\b\d{3}-\d{2}-\d{4}\b/,
            /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/,
            /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/
        ];

        for (const pattern of piiPatterns) {
            if (pattern.test(receiptStr)) {
                throw new Error('Receipt contains PII (violates Rule 217: No Code/PII in Stores)');
            }
        }
    }

    private async ensureDirectoryExists(dirPath: string): Promise<void> {
        return new Promise((resolve, reject) => {
            fs.mkdir(dirPath, { recursive: true }, (err) => {
                if (err) {
                    reject(err);
                } else {
                    resolve();
                }
            });
        });
    }
}
