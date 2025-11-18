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
        const startYear = startDate.getUTCFullYear();
        const startMonth = startDate.getUTCMonth() + 1;
        const endYear = endDate.getUTCFullYear();
        const endMonth = endDate.getUTCMonth() + 1;

        // Calculate number of months to iterate
        const startMonthIndex = startYear * 12 + startMonth;
        const endMonthIndex = endYear * 12 + endMonth;

        for (let monthIndex = startMonthIndex; monthIndex <= endMonthIndex; monthIndex++) {
            const year = Math.floor(monthIndex / 12);
            const month = monthIndex % 12;
            const actualMonth = month === 0 ? 12 : month;
            const actualYear = month === 0 ? year - 1 : year;

            const receipts = await this.readReceipts(repoId, actualYear, actualMonth);

            // Filter receipts by date range
            for (const receipt of receipts) {
                const receiptDate = new Date(receipt.timestamp_utc);
                if (receiptDate >= startDate && receiptDate <= endDate) {
                    allReceipts.push(receipt);
                }
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
     * @returns boolean True if signature is valid
     */
    private validateReceiptSignature(receipt: DecisionReceipt | FeedbackReceipt): boolean {
        if (!receipt.signature || receipt.signature.length === 0) {
            console.warn('Receipt missing signature (Rule 224 violation)');
            return false;
        }

        const kid = extractKidFromSignature(receipt.signature);
        if (!kid) {
            console.warn('Receipt signature missing key identifier (kid)');
            return false;
        }

        try {
            const { key } = resolvePublicKeyByKid(kid);
            return verifyReceiptSignature(receipt, key);
        } catch (error) {
            console.warn(`Failed to verify receipt using kid "${kid}": ${(error as Error).message}`);
            return false;
        }
    }
}
