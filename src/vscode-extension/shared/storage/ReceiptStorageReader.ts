/**
 * Receipt Storage Reader
 * 
 * Reads receipts from IDE Plane storage according to 4-Plane Storage Architecture rules.
 * 
 * Compliance:
 * - Rule 219: JSONL receipts (newline-delimited)
 * - Rule 223: Path resolution via ZU_ROOT
 * - Rule 224: Receipts validation (signed, append-only)
 * 
 * @module storage
 */

import * as fs from 'fs';
import * as path from 'path';
import { StoragePathResolver } from './StoragePathResolver';
import { ReceiptParser, DecisionReceipt, FeedbackReceipt } from '../receipt-parser/ReceiptParser';

/**
 * Receipt storage reader for VS Code Extension
 * Reads receipts from IDE Plane: ide/receipts/{repo-id}/{yyyy}/{mm}/
 */
export class ReceiptStorageReader {
    private pathResolver: StoragePathResolver;
    private receiptParser: ReceiptParser;

    constructor(zuRoot?: string) {
        this.pathResolver = new StoragePathResolver(zuRoot);
        this.receiptParser = new ReceiptParser();
    }

    /**
     * Read receipts from storage
     * 
     * @param repoId Repository identifier (kebab-case)
     * @param year 4-digit year (YYYY)
     * @param month 2-digit month (1-12)
     * @returns Promise<Array<DecisionReceipt | FeedbackReceipt>> Array of parsed receipts
     */
    public async readReceipts(
        repoId: string,
        year: number,
        month: number
    ): Promise<Array<DecisionReceipt | FeedbackReceipt>> {
        const receiptDir = this.pathResolver.resolveReceiptPath(repoId, year, month);
        // Use forward slash to maintain consistency
        const receiptFile = `${receiptDir}/receipts.jsonl`;

        // Check if file exists
        if (!fs.existsSync(receiptFile)) {
            return [];
        }

        // Read file content with error handling
        let content: string;
        try {
            content = fs.readFileSync(receiptFile, 'utf-8');
        } catch (error) {
            console.error(`Failed to read receipt file: ${receiptFile}`, error);
            return [];
        }

        // Split by newlines (JSONL format - Rule 219)
        const lines = content.split('\n').filter(line => line.trim().length > 0);

        // Parse each line as a receipt
        const receipts: Array<DecisionReceipt | FeedbackReceipt> = [];
        for (const line of lines) {
            try {
                // Parse receipt
                const receipt = JSON.parse(line);

                // Validate receipt type and parse
                if (this.receiptParser.isDecisionReceipt(receipt)) {
                    const parsedReceipt = this.receiptParser.parseDecisionReceipt(line);
                    if (parsedReceipt) {
                        // Validate signature (Rule 224)
                        if (this.validateReceiptSignature(parsedReceipt)) {
                            receipts.push(parsedReceipt);
                        }
                    }
                } else if (this.receiptParser.isFeedbackReceipt(receipt)) {
                    const parsedReceipt = this.receiptParser.parseFeedbackReceipt(line);
                    if (parsedReceipt) {
                        // Validate signature (Rule 224)
                        if (this.validateReceiptSignature(parsedReceipt)) {
                            receipts.push(parsedReceipt);
                        }
                    }
                }
            } catch (error) {
                // Invalid receipt line - log and continue (per Rule 219: invalid lines go to quarantine)
                console.error(`Failed to parse receipt line: ${error}`);
                // TODO: Move to quarantine directory
            }
        }

        return receipts;
    }

    /**
     * Read receipts for a specific date range
     * 
     * @param repoId Repository identifier
     * @param startDate Start date (inclusive)
     * @param endDate End date (inclusive)
     * @returns Promise<Array<DecisionReceipt | FeedbackReceipt>> Array of receipts in date range
     */
    public async readReceiptsInRange(
        repoId: string,
        startDate: Date,
        endDate: Date
    ): Promise<Array<DecisionReceipt | FeedbackReceipt>> {
        const allReceipts: Array<DecisionReceipt | FeedbackReceipt> = [];

        // Iterate through months in range
        const currentDate = new Date(startDate);
        while (currentDate <= endDate) {
            const year = currentDate.getUTCFullYear();
            const month = currentDate.getUTCMonth() + 1;

            const receipts = await this.readReceipts(repoId, year, month);
            
            // Filter receipts by date range
            for (const receipt of receipts) {
                const receiptDate = new Date(receipt.timestamp_utc);
                if (receiptDate >= startDate && receiptDate <= endDate) {
                    allReceipts.push(receipt);
                }
            }

            // Move to next month
            currentDate.setUTCMonth(currentDate.getUTCMonth() + 1);
        }

        return allReceipts;
    }

    /**
     * Read latest receipts
     * 
     * @param repoId Repository identifier
     * @param limit Maximum number of receipts to return
     * @returns Promise<Array<DecisionReceipt | FeedbackReceipt>> Latest receipts
     */
    public async readLatestReceipts(
        repoId: string,
        limit: number = 10
    ): Promise<Array<DecisionReceipt | FeedbackReceipt>> {
        const allReceipts: Array<DecisionReceipt | FeedbackReceipt> = [];

        // Read from current month and previous months (up to 12 months back)
        const now = new Date();
        for (let i = 0; i < 12; i++) {
            const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
            const year = date.getUTCFullYear();
            const month = date.getUTCMonth() + 1;

            const receipts = await this.readReceipts(repoId, year, month);
            allReceipts.push(...receipts);

            if (allReceipts.length >= limit * 2) {
                break; // Stop if we have enough receipts
            }
        }

        // Sort by timestamp (newest first)
        allReceipts.sort((a, b) => {
            const dateA = new Date(a.timestamp_utc).getTime();
            const dateB = new Date(b.timestamp_utc).getTime();
            return dateB - dateA;
        });

        // Return limited results
        return allReceipts.slice(0, limit);
    }

    /**
     * Validate receipt signature (Rule 224)
     * 
     * Note: Full signature validation requires cryptographic verification.
     * This implementation provides structure for signature validation.
     * 
     * TODO: Implement cryptographic signature verification using:
     * - Public keys from ide/policy/trust/pubkeys/ or product/policy/trust/pubkeys/
     * - Ed25519 or similar signing algorithm
     * - Canonical JSON form for signature verification
     * 
     * @param receipt Receipt to validate
     * @returns boolean True if signature is valid
     */
    private validateReceiptSignature(receipt: DecisionReceipt | FeedbackReceipt): boolean {
        // Check signature exists (Rule 224: receipts must be signed)
        if (!receipt.signature || receipt.signature.length === 0) {
            console.warn('Receipt missing signature (Rule 224 violation)');
            return false;
        }

        // Check signature format (should start with 'sig-' or be base64/hex)
        if (!receipt.signature.startsWith('sig-') && 
            !/^[A-Za-z0-9+/=]+$/.test(receipt.signature) && 
            !/^[0-9a-fA-F]+$/.test(receipt.signature)) {
            console.warn('Receipt signature has invalid format');
            return false;
        }

        // TODO: Implement cryptographic signature verification
        // Steps:
        // 1. Extract canonical JSON from receipt (without signature field)
        // 2. Load public key from trust/pubkeys/ based on receipt's policy_version_ids
        // 3. Verify signature against canonical JSON using public key
        // 4. Return verification result

        // For now, return true if signature exists and has valid format (basic check)
        return receipt.signature.length > 0;
    }
}

