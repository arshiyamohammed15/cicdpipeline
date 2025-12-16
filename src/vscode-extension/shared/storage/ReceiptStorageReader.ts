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
import { StoragePathResolver } from './StoragePathResolver';
import { ReceiptParser, DecisionReceipt, FeedbackReceipt } from '../receipt-parser/ReceiptParser';
import { extractKidFromSignature, resolvePublicKeyByKid, verifyReceiptSignature } from './ReceiptVerifier';

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
            // CR-054: Check file size before reading to prevent memory exhaustion
            const stats = fs.statSync(receiptFile);
            const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB limit
            if (stats.size > MAX_FILE_SIZE) {
                console.error(`Receipt file too large: ${receiptFile} (${stats.size} bytes, max ${MAX_FILE_SIZE})`);
                return [];
            }
            
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

        // CR-056: Optimize to only read necessary months
        // Calculate which months are actually needed
        const startYear = startDate.getUTCFullYear();
        const startMonth = startDate.getUTCMonth() + 1;
        const endYear = endDate.getUTCFullYear();
        const endMonth = endDate.getUTCMonth() + 1;

        // Only iterate through months that could contain receipts in range
        let currentYear = startYear;
        let currentMonth = startMonth;

        while (currentYear < endYear || (currentYear === endYear && currentMonth <= endMonth)) {
            const receipts = await this.readReceipts(repoId, currentYear, currentMonth);

            // Filter receipts by date range
            for (const receipt of receipts) {
                const receiptDate = new Date(receipt.timestamp_utc);
                if (receiptDate >= startDate && receiptDate <= endDate) {
                    allReceipts.push(receipt);
                }
            }

            // Move to next month
            currentMonth++;
            if (currentMonth > 12) {
                currentMonth = 1;
                currentYear++;
            }
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
            const date = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - i, 1));
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
     * @returns boolean True if signature is valid, false if invalid, throws on error
     */
    private validateReceiptSignature(receipt: DecisionReceipt | FeedbackReceipt): boolean {
        // CR-055: Distinguish between validation failure and error conditions
        if (!receipt.signature || receipt.signature.length === 0) {
            console.warn('Receipt missing signature (Rule 224 violation)');
            return false; // Validation failure, not an error
        }

        const kid = extractKidFromSignature(receipt.signature);
        if (!kid) {
            console.warn('Receipt signature missing key identifier (kid)');
            return false; // Validation failure, not an error
        }

        try {
            const { key } = resolvePublicKeyByKid(kid);
            const isValid = verifyReceiptSignature(receipt, key);
            if (!isValid) {
                console.warn(`Receipt signature verification failed for kid "${kid}"`);
                return false; // Validation failure
            }
            return true; // Validation success
        } catch (error) {
            // CR-055: Distinguish error conditions from validation failures
            const err = error as Error;
            if (err.name === 'PublicKeyNotFoundError') {
                console.warn(`Public key not found for kid "${kid}": ${err.message}`);
                return false; // Validation failure - key not found
            }
            // Unexpected error - log and treat as validation failure
            console.error(`Unexpected error verifying receipt signature: ${err.message}`, err);
            return false; // Treat unexpected errors as validation failure
        }
    }
}
