/**
 * Receipt Storage Service
 * 
 * Handles receipt storage according to 4-Plane Storage Architecture rules.
 * 
 * Compliance:
 * - Rule 219: JSONL receipts (append-only, newline-delimited, signed)
 * - Rule 223: Path resolution via ZU_ROOT
 * - Rule 224: Receipts validation (signed, append-only)
 * - Rule 228: Laptop receipts use YYYY/MM month partitioning
 * - Rule 217: No code/PII in stores
 * 
 * @module storage
 */

import * as fs from 'fs';
import * as path from 'path';
import { StoragePathResolver } from './StoragePathResolver';
import { DecisionReceipt, FeedbackReceipt } from '../receipt-types';

/**
 * Receipt storage service for Edge Agent
 * Stores receipts in IDE Plane: ide/receipts/{repo-id}/{yyyy}/{mm}/
 */
export class ReceiptStorageService {
    private pathResolver: StoragePathResolver;

    constructor(zuRoot?: string) {
        this.pathResolver = new StoragePathResolver(zuRoot);
    }

    /**
     * Store a decision receipt (append-only JSONL format)
     * 
     * @param receipt Decision receipt to store
     * @param repoId Repository identifier (kebab-case)
     * @returns Promise<string> Path where receipt was stored
     */
    public async storeDecisionReceipt(
        receipt: DecisionReceipt,
        repoId: string
    ): Promise<string> {
        // Extract year and month from timestamp_utc
        const date = new Date(receipt.timestamp_utc);
        const year = date.getUTCFullYear();
        const month = date.getUTCMonth() + 1; // getUTCMonth() returns 0-11

        // Resolve storage path (Rule 228: YYYY/MM month partitioning)
        const receiptDir = this.pathResolver.resolveReceiptPath(repoId, year, month);
        // Use forward slash to maintain consistency (StoragePathResolver normalizes to forward slashes)
        const receiptFile = `${receiptDir}/receipts.jsonl`;

        // Ensure directory exists
        await this.ensureDirectoryExists(receiptDir);

        // Validate receipt signature before storing (Rule 224)
        if (!receipt.signature || receipt.signature.length === 0) {
            throw new Error('Receipt must be signed before storage (Rule 224)');
        }

        // Validate no code/PII in receipt BEFORE storage (Rule 217)
        this.validateNoCodeOrPII(receipt);

        // Store complete receipt with signature (Rule 219: signed JSONL receipts)
        // Note: Canonical form is used for signing, but we store the complete receipt
        const receiptJson = JSON.stringify(receipt, null, 0);

        // Append to JSONL file (Rule 219: append-only, newline-delimited)
        await this.appendToJsonl(receiptFile, receiptJson);

        return receiptFile;
    }

    /**
     * Store a feedback receipt (append-only JSONL format)
     * 
     * @param receipt Feedback receipt to store
     * @param repoId Repository identifier (kebab-case)
     * @returns Promise<string> Path where receipt was stored
     */
    public async storeFeedbackReceipt(
        receipt: FeedbackReceipt,
        repoId: string
    ): Promise<string> {
        // Extract year and month from timestamp_utc
        const date = new Date(receipt.timestamp_utc);
        const year = date.getUTCFullYear();
        const month = date.getUTCMonth() + 1;

        // Resolve storage path
        const receiptDir = this.pathResolver.resolveReceiptPath(repoId, year, month);
        // Use forward slash to maintain consistency
        const receiptFile = `${receiptDir}/receipts.jsonl`;

        // Ensure directory exists
        await this.ensureDirectoryExists(receiptDir);

        // Validate receipt signature
        if (!receipt.signature || receipt.signature.length === 0) {
            throw new Error('Receipt must be signed before storage (Rule 224)');
        }

        // Validate no code/PII BEFORE storage (Rule 217)
        this.validateNoCodeOrPII(receipt);

        // Store complete receipt with signature (Rule 219: signed JSONL receipts)
        const receiptJson = JSON.stringify(receipt, null, 0);

        // Append to JSONL file
        await this.appendToJsonl(receiptFile, receiptJson);

        return receiptFile;
    }

    /**
     * Read receipts from storage (for validation/testing)
     * 
     * @param repoId Repository identifier
     * @param year 4-digit year
     * @param month 2-digit month (1-12)
     * @returns Promise<string[]> Array of receipt JSON strings (one per line)
     */
    public async readReceipts(
        repoId: string,
        year: number,
        month: number
    ): Promise<string[]> {
        const receiptDir = this.pathResolver.resolveReceiptPath(repoId, year, month);
        // Use forward slash to maintain consistency
        const receiptFile = `${receiptDir}/receipts.jsonl`;

        // Check if file exists
        if (!fs.existsSync(receiptFile)) {
            return [];
        }

        // Read file content
        const content = fs.readFileSync(receiptFile, 'utf-8');

        // Split by newlines (JSONL format)
        const lines = content.split('\n').filter(line => line.trim().length > 0);

        return lines;
    }

    /**
     * Append receipt to JSONL file (Rule 219: append-only, newline-delimited)
     */
    private async appendToJsonl(filePath: string, jsonContent: string): Promise<void> {
        return new Promise((resolve, reject) => {
            // Append mode (Rule 219: append-only)
            const stream = fs.createWriteStream(filePath, { flags: 'a' });
            
            stream.write(jsonContent + '\n', (err) => {
                if (err) {
                    reject(err);
                } else {
                    resolve();
                }
            });

            stream.end();
        });
    }

    /**
     * Convert receipt to canonical JSON (for consistent signature validation)
     * 
     * Note: This matches the canonical form used in ReceiptGenerator.signReceipt()
     * Signature is removed before sorting keys to ensure consistent canonical form.
     */
    private toCanonicalJson(receipt: DecisionReceipt | FeedbackReceipt): string {
        // Remove signature before creating canonical form (signature is not part of signed data)
        const { signature, ...receiptWithoutSignature } = receipt as any;
        // Sort keys for consistent canonical form
        const sortedKeys = Object.keys(receiptWithoutSignature).sort();
        return JSON.stringify(receiptWithoutSignature, sortedKeys);
    }

    /**
     * Validate no code/PII in receipt (Rule 217)
     */
    private validateNoCodeOrPII(receipt: DecisionReceipt | FeedbackReceipt): void {
        const receiptStr = JSON.stringify(receipt);

        // Check for code patterns (function, class, import, etc.)
        const codePatterns = [
            /\bfunction\s+\w+\s*\(/,  // function name()
            /\bfunction\s*\(/,        // function()
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

        // Check for PII patterns (email, SSN, credit card, etc.)
        const piiPatterns = [
            /\b\d{3}-\d{2}-\d{4}\b/, // SSN
            /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/, // Credit card
            /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/ // Email
        ];

        for (const pattern of piiPatterns) {
            if (pattern.test(receiptStr)) {
                throw new Error('Receipt contains PII (violates Rule 217: No Code/PII in Stores)');
            }
        }
    }

    /**
     * Ensure directory exists (create if needed)
     */
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

