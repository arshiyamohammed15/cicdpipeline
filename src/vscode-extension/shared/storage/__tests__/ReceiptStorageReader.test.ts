/**
 * ReceiptStorageReader Test Suite
 * 
 * Tests for receipt reading operations in VS Code Extension
 * Validates receipt parsing, signature validation, and date range queries
 */

import { ReceiptStorageReader } from '../ReceiptStorageReader';
import { ReceiptParser } from '../../receipt-parser/ReceiptParser';
import { DecisionReceipt, FeedbackReceipt } from '../../receipt-parser/ReceiptParser';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

describe('ReceiptStorageReader', () => {
    const testZuRoot = os.tmpdir() + '/zeroui-test-' + Date.now();
    let reader: ReceiptStorageReader;
    const testRepoId = 'test-repo-id';

    beforeEach(() => {
        if (!fs.existsSync(testZuRoot)) {
            fs.mkdirSync(testZuRoot, { recursive: true });
        }
        process.env.ZU_ROOT = testZuRoot;
        reader = new ReceiptStorageReader(testZuRoot);
    });

    afterEach(() => {
        if (fs.existsSync(testZuRoot)) {
            fs.rmSync(testZuRoot, { recursive: true, force: true });
        }
    });

    describe('Read Receipts', () => {
        const createTestReceipt = (receiptId: string, timestamp: string): DecisionReceipt => ({
            receipt_id: receiptId,
            gate_id: 'test-gate',
            policy_version_ids: [],
            snapshot_hash: 'hash',
            timestamp_utc: timestamp,
            timestamp_monotonic_ms: Date.now(),
            inputs: {},
            decision: {
                status: 'pass',
                rationale: 'Test',
                badges: []
            },
            evidence_handles: [],
            actor: {
                repo_id: testRepoId
            },
            degraded: false,
            signature: 'sig-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef' // 64 hex chars after sig-
        });

        it('should return empty array if file does not exist', async () => {
            const receipts = await reader.readReceipts(testRepoId, 2025, 1);
            expect(receipts).toEqual([]);
        });

        it('should read receipts from JSONL file', async () => {
            const receipt1 = createTestReceipt('receipt-1', '2025-01-15T10:00:00.000Z');
            const receipt2 = createTestReceipt('receipt-2', '2025-01-16T10:00:00.000Z');

            // Use forward slashes (consistent with StoragePathResolver)
            const receiptDir = `${testZuRoot}/ide/receipts/${testRepoId}/2025/01`;
            fs.mkdirSync(receiptDir, { recursive: true });
            const receiptFile = `${receiptDir}/receipts.jsonl`;

            // Write receipts in JSONL format (with signature - Rule 219: signed JSONL receipts)
            fs.writeFileSync(receiptFile, JSON.stringify(receipt1) + '\n' + JSON.stringify(receipt2) + '\n');

            const receipts = await reader.readReceipts(testRepoId, 2025, 1);

            expect(receipts.length).toBe(2);
            // Use type guard to check receipt type
            const readReceipt1 = receipts[0];
            const readReceipt2 = receipts[1];
            const receipt1Id = 'receipt_id' in readReceipt1 ? readReceipt1.receipt_id : readReceipt1.feedback_id;
            const receipt2Id = 'receipt_id' in readReceipt2 ? readReceipt2.receipt_id : readReceipt2.feedback_id;
            expect(receipt1Id).toBe('receipt-1');
            expect(receipt2Id).toBe('receipt-2');
        });

        it('should handle invalid receipt lines gracefully', async () => {
            const receiptDir = path.join(testZuRoot, 'ide', 'receipts', testRepoId, '2025', '01');
            fs.mkdirSync(receiptDir, { recursive: true });
            const receiptFile = path.join(receiptDir, 'receipts.jsonl');

            // Write valid and invalid lines
            const validReceipt = createTestReceipt('receipt-1', '2025-01-15T10:00:00.000Z');
            fs.writeFileSync(receiptFile, JSON.stringify(validReceipt) + '\n' + 'invalid json line\n');

            const receipts = await reader.readReceipts(testRepoId, 2025, 1);

            // Should return only valid receipts
            expect(receipts.length).toBe(1);
            const receipt = receipts.find(r => 'receipt_id' in r) as DecisionReceipt;
            expect(receipt?.receipt_id).toBe('receipt-1');
        });

        it('should filter out receipts without signatures', async () => {
            const receiptDir = path.join(testZuRoot, 'ide', 'receipts', testRepoId, '2025', '01');
            fs.mkdirSync(receiptDir, { recursive: true });
            const receiptFile = path.join(receiptDir, 'receipts.jsonl');

            const receiptWithSig = createTestReceipt('receipt-1', '2025-01-15T10:00:00.000Z');
            const receiptWithoutSig = createTestReceipt('receipt-2', '2025-01-16T10:00:00.000Z');
            delete (receiptWithoutSig as any).signature;

            fs.writeFileSync(receiptFile, JSON.stringify(receiptWithSig) + '\n' + JSON.stringify(receiptWithoutSig) + '\n');

            const receipts = await reader.readReceipts(testRepoId, 2025, 1);

            // Should only return receipt with signature
            expect(receipts.length).toBe(1);
            const receipt = receipts.find(r => 'receipt_id' in r) as DecisionReceipt;
            expect(receipt?.receipt_id).toBe('receipt-1');
        });

        it('should handle file read errors gracefully', async () => {
            // Create directory but make file unreadable (simulate permission error)
            const receiptDir = path.join(testZuRoot, 'ide', 'receipts', testRepoId, '2025', '01');
            fs.mkdirSync(receiptDir, { recursive: true });
            const receiptFile = path.join(receiptDir, 'receipts.jsonl');
            fs.writeFileSync(receiptFile, 'test');

            // Use jest.spyOn to mock fs.readFileSync
            const readFileSyncSpy = jest.spyOn(fs, 'readFileSync').mockImplementation(() => {
                throw new Error('Permission denied');
            });

            const receipts = await reader.readReceipts(testRepoId, 2025, 1);

            // Should return empty array on error
            expect(receipts).toEqual([]);

            // Restore original
            readFileSyncSpy.mockRestore();
        });
    });

    describe('Read Receipts In Range', () => {
        const createReceiptForDate = (receiptId: string, date: Date): DecisionReceipt => ({
            receipt_id: receiptId,
            gate_id: 'gate',
            policy_version_ids: [],
            snapshot_hash: 'hash',
            timestamp_utc: date.toISOString(),
            timestamp_monotonic_ms: date.getTime(),
            inputs: {},
            decision: { status: 'pass', rationale: '', badges: [] },
            evidence_handles: [],
            actor: { repo_id: testRepoId },
            degraded: false,
            signature: 'sig-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef' // Valid signature format
        });

        it('should read receipts within date range', async () => {
            const startDate = new Date('2025-01-15');
            const endDate = new Date('2025-01-20');

            // Create receipts in different months
            const receipt1 = createReceiptForDate('receipt-1', new Date('2025-01-15'));
            const receipt2 = createReceiptForDate('receipt-2', new Date('2025-01-18'));
            const receipt3 = createReceiptForDate('receipt-3', new Date('2025-01-25')); // Outside range

            // Write to January
            const receiptDir1 = path.join(testZuRoot, 'ide', 'receipts', testRepoId, '2025', '01');
            fs.mkdirSync(receiptDir1, { recursive: true });
            fs.writeFileSync(
                path.join(receiptDir1, 'receipts.jsonl'),
                JSON.stringify(receipt1) + '\n' + JSON.stringify(receipt2) + '\n' + JSON.stringify(receipt3) + '\n'
            );

            const receipts = await reader.readReceiptsInRange(testRepoId, startDate, endDate);

            expect(receipts.length).toBe(2);
            const receiptIds = receipts
                .filter(r => 'receipt_id' in r)
                .map(r => (r as DecisionReceipt).receipt_id);
            expect(receiptIds).toEqual(expect.arrayContaining(['receipt-1', 'receipt-2']));
        });

        it('should handle receipts across multiple months', async () => {
            const startDate = new Date('2025-01-28');
            const endDate = new Date('2025-02-05');

            const createReceiptForDate = (receiptId: string, date: Date): DecisionReceipt => ({
                receipt_id: receiptId,
                gate_id: 'gate',
                policy_version_ids: [],
                snapshot_hash: 'hash',
                timestamp_utc: date.toISOString(),
                timestamp_monotonic_ms: date.getTime(),
                inputs: {},
                decision: { status: 'pass', rationale: '', badges: [] },
                evidence_handles: [],
                actor: { repo_id: testRepoId },
                degraded: false,
                signature: 'sig-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef' // 64 hex chars
            });

            const receipt1 = createReceiptForDate('receipt-1', new Date('2025-01-30'));
            const receipt2 = createReceiptForDate('receipt-2', new Date('2025-02-02'));

            // Write to both months
            const receiptDir1 = path.join(testZuRoot, 'ide', 'receipts', testRepoId, '2025', '01');
            const receiptDir2 = path.join(testZuRoot, 'ide', 'receipts', testRepoId, '2025', '02');
            fs.mkdirSync(receiptDir1, { recursive: true });
            fs.mkdirSync(receiptDir2, { recursive: true });
            fs.writeFileSync(path.join(receiptDir1, 'receipts.jsonl'), JSON.stringify(receipt1) + '\n');
            fs.writeFileSync(path.join(receiptDir2, 'receipts.jsonl'), JSON.stringify(receipt2) + '\n');

            const receipts = await reader.readReceiptsInRange(testRepoId, startDate, endDate);

            expect(receipts.length).toBe(2);
        });
    });

    describe('Read Latest Receipts', () => {
        // Helper function to get receipt ID safely
        const getReceiptId = (receipt: DecisionReceipt | FeedbackReceipt): string => {
            return 'receipt_id' in receipt ? receipt.receipt_id : receipt.feedback_id;
        };

        const createReceiptForDate = (receiptId: string, date: Date): DecisionReceipt => ({
            receipt_id: receiptId,
            gate_id: 'gate',
            policy_version_ids: [],
            snapshot_hash: 'hash',
            timestamp_utc: date.toISOString(),
            timestamp_monotonic_ms: date.getTime(),
            inputs: {},
            decision: { status: 'pass', rationale: '', badges: [] },
            evidence_handles: [],
            actor: { repo_id: testRepoId },
            degraded: false,
            signature: 'sig-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef' // Valid signature format
        });

        it('should return latest receipts sorted by timestamp', async () => {
            const now = new Date();
            const receipt1 = createReceiptForDate('receipt-1', new Date(now.getTime() - 1000));
            const receipt2 = createReceiptForDate('receipt-2', new Date(now.getTime() - 500));
            const receipt3 = createReceiptForDate('receipt-3', now);

            // Use forward slashes (consistent with StoragePathResolver)
            const receiptDir = `${testZuRoot}/ide/receipts/${testRepoId}/${now.getUTCFullYear()}/${(now.getUTCMonth() + 1).toString().padStart(2, '0')}`;
            fs.mkdirSync(receiptDir, { recursive: true });
            fs.writeFileSync(
                `${receiptDir}/receipts.jsonl`,
                JSON.stringify(receipt1) + '\n' + JSON.stringify(receipt2) + '\n' + JSON.stringify(receipt3) + '\n'
            );

            const receipts = await reader.readLatestReceipts(testRepoId, 10);

            expect(receipts.length).toBe(3);
            // Should be sorted newest first
            expect(getReceiptId(receipts[0])).toBe('receipt-3');
            expect(getReceiptId(receipts[1])).toBe('receipt-2');
            expect(getReceiptId(receipts[2])).toBe('receipt-1');
        });

        it('should limit results to specified number', async () => {
            const now = new Date();
            const receipts = [];
            for (let i = 0; i < 20; i++) {
                receipts.push(createReceiptForDate(`receipt-${i}`, new Date(now.getTime() - i * 1000)));
            }

            // Use forward slashes (consistent with StoragePathResolver)
            const receiptDir = `${testZuRoot}/ide/receipts/${testRepoId}/${now.getUTCFullYear()}/${(now.getUTCMonth() + 1).toString().padStart(2, '0')}`;
            fs.mkdirSync(receiptDir, { recursive: true });
            fs.writeFileSync(
                `${receiptDir}/receipts.jsonl`,
                receipts.map(r => JSON.stringify(r)).join('\n') + '\n'
            );

            const latest = await reader.readLatestReceipts(testRepoId, 5);

            expect(latest.length).toBe(5);
        });

        it('should return empty array if no receipts exist', async () => {
            const receipts = await reader.readLatestReceipts(testRepoId, 10);
            expect(receipts).toEqual([]);
        });
    });

    describe('Signature Validation (Rule 224)', () => {
        it('should accept receipts with valid signature format', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'receipt-1',
                gate_id: 'gate',
                policy_version_ids: [],
                snapshot_hash: 'hash',
                timestamp_utc: '2025-01-15T10:00:00.000Z',
                timestamp_monotonic_ms: Date.now(),
                inputs: {},
                decision: { status: 'pass', rationale: '', badges: [] },
                evidence_handles: [],
                actor: { repo_id: testRepoId },
                degraded: false,
                signature: 'sig-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef' // Valid format (64 hex chars)
            };

            const receiptDir = path.join(testZuRoot, 'ide', 'receipts', testRepoId, '2025', '01');
            fs.mkdirSync(receiptDir, { recursive: true });
            fs.writeFileSync(path.join(receiptDir, 'receipts.jsonl'), JSON.stringify(receipt) + '\n');

            const receipts = await reader.readReceipts(testRepoId, 2025, 1);

            expect(receipts.length).toBe(1);
        });

        it('should reject receipts without signature', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'receipt-1',
                gate_id: 'gate',
                policy_version_ids: [],
                snapshot_hash: 'hash',
                timestamp_utc: '2025-01-15T10:00:00.000Z',
                timestamp_monotonic_ms: Date.now(),
                inputs: {},
                decision: { status: 'pass', rationale: '', badges: [] },
                evidence_handles: [],
                actor: { repo_id: testRepoId },
                degraded: false,
                signature: '' // Empty signature
            };

            const receiptDir = path.join(testZuRoot, 'ide', 'receipts', testRepoId, '2025', '01');
            fs.mkdirSync(receiptDir, { recursive: true });
            fs.writeFileSync(path.join(receiptDir, 'receipts.jsonl'), JSON.stringify(receipt) + '\n');

            const receipts = await reader.readReceipts(testRepoId, 2025, 1);

            expect(receipts.length).toBe(0);
        });
    });
});

