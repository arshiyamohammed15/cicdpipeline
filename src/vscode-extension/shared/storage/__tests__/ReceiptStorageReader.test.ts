/**
 * ReceiptStorageReader Test Suite
 *
 * Tests for receipt reading operations in VS Code Extension
 * Validates receipt parsing, signature validation, and date range queries
 */

import { ReceiptStorageReader } from '../ReceiptStorageReader';
import { ReceiptParser } from '../../receipt-parser/ReceiptParser';
import { DecisionReceipt, FeedbackReceipt } from '../../receipt-parser/ReceiptParser';
import { Ed25519ReceiptSigner } from '../ReceiptSigner';
import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

/**
 * DISCOVERY replacement:
 * - Previously fs.writeFileSync(... 'receipts.jsonl', ...) truncated files during test setup.
 * - Now uses append-only writes with fdatasync to mirror production guarantees.
 */
const appendReceiptsJsonl = (filePath: string, payload: string): void => {
    const fd = fs.openSync(filePath, fs.constants.O_CREAT | fs.constants.O_APPEND | fs.constants.O_WRONLY);
    try {
        fs.writeSync(fd, payload, undefined, 'utf8');
        fs.fdatasyncSync(fd);
    } finally {
        fs.closeSync(fd);
    }
};

describe('ReceiptStorageReader', () => {
    const testZuRoot = os.tmpdir() + '/zeroui-test-' + Date.now();
    let reader: ReceiptStorageReader;
    const testRepoId = 'test-repo-id';
    const signingKeyId = 'test-signing-key';
    let signer: Ed25519ReceiptSigner;
    const signDecisionReceipt = (base: Omit<DecisionReceipt, 'signature'>): DecisionReceipt => ({
        ...base,
        signature: signer.signReceipt(base as unknown as Record<string, unknown>)
    });

    beforeEach(() => {
        if (!fs.existsSync(testZuRoot)) {
            fs.mkdirSync(testZuRoot, { recursive: true });
        }
        process.env.ZU_ROOT = testZuRoot;
        const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
        const privatePem = privateKey.export({ format: 'pem', type: 'pkcs8' }).toString();
        const publicPem = publicKey.export({ format: 'pem', type: 'spki' }).toString();
        signer = new Ed25519ReceiptSigner({
            privateKey: privatePem,
            keyId: signingKeyId
        });
        const trustDir = path.join(testZuRoot, 'tenant', 'policy', 'trust', 'pubkeys');
        fs.mkdirSync(trustDir, { recursive: true });
        fs.writeFileSync(path.join(trustDir, `${signingKeyId}.pem`), publicPem);
        reader = new ReceiptStorageReader(testZuRoot);
    });

    afterEach(() => {
        if (fs.existsSync(testZuRoot)) {
            fs.rmSync(testZuRoot, { recursive: true, force: true });
        }
        delete process.env.ZU_ROOT;
    });

    describe('Read Receipts', () => {
        const createTestReceipt = (receiptId: string, timestamp: string): DecisionReceipt => {
            const base: Omit<DecisionReceipt, 'signature'> = {
                receipt_id: receiptId,
                gate_id: 'test-gate',
                policy_version_ids: [],
                snapshot_hash: 'hash',
                timestamp_utc: timestamp,
                timestamp_monotonic_ms: Date.now(),
                evaluation_point: 'pre-commit',
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
                degraded: false
            };
            return signDecisionReceipt(base);
        };

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
            appendReceiptsJsonl(receiptFile, JSON.stringify(receipt1) + '\n' + JSON.stringify(receipt2) + '\n');

            const receipts = await reader.readReceipts(testRepoId, 2025, 1);

            expect(receipts.length).toBe(2);
            // Use type guard to check receipt type
            const readReceipt1 = receipts[0];
            const readReceipt2 = receipts[1];
            const receipt1Id = 'receipt_id' in readReceipt1 ? readReceipt1.receipt_id : readReceipt1.feedback_id;
            const receipt2Id = 'receipt_id' in readReceipt2 ? readReceipt2.receipt_id : readReceipt2.feedback_id;
            expect(receipt1Id).toBe('receipt-1');
            expect(receipt2Id).toBe('receipt-2');
            if ('evaluation_point' in readReceipt1) {
                expect(readReceipt1.evaluation_point).toBe('pre-commit');
            }
        });

        it('should handle invalid receipt lines gracefully', async () => {
            const receiptDir = path.join(testZuRoot, 'ide', 'receipts', testRepoId, '2025', '01');
            fs.mkdirSync(receiptDir, { recursive: true });
            const receiptFile = path.join(receiptDir, 'receipts.jsonl');

            // Write valid and invalid lines
            const validReceipt = createTestReceipt('receipt-1', '2025-01-15T10:00:00.000Z');
            appendReceiptsJsonl(receiptFile, JSON.stringify(validReceipt) + '\n' + 'invalid json line\n');

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

            appendReceiptsJsonl(receiptFile, JSON.stringify(receiptWithSig) + '\n' + JSON.stringify(receiptWithoutSig) + '\n');

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
            fs.mkdirSync(receiptFile, { recursive: true }); // Force EISDIR error

            const receipts = await reader.readReceipts(testRepoId, 2025, 1);

            // Should return empty array on error
            expect(receipts).toEqual([]);
        });
    });

    describe('Read Receipts In Range', () => {
        const createReceiptForDate = (receiptId: string, date: Date): DecisionReceipt => {
            const base: Omit<DecisionReceipt, 'signature'> = {
                receipt_id: receiptId,
                gate_id: 'gate',
                policy_version_ids: [],
                snapshot_hash: 'hash',
                timestamp_utc: date.toISOString(),
                timestamp_monotonic_ms: date.getTime(),
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: { status: 'pass', rationale: '', badges: [] },
                evidence_handles: [],
                actor: { repo_id: testRepoId },
                degraded: false
            };
            return signDecisionReceipt(base);
        };

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
            appendReceiptsJsonl(
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
            const startDate = new Date(Date.UTC(2025, 0, 28)); // Jan 28, 2025 UTC
            const endDate = new Date(Date.UTC(2025, 1, 5)); // Feb 5, 2025 UTC

            const createReceiptForDate = (receiptId: string, date: Date): DecisionReceipt => {
            const base: Omit<DecisionReceipt, 'signature'> = {
                    receipt_id: receiptId,
                    gate_id: 'gate',
                    policy_version_ids: [],
                    snapshot_hash: 'hash',
                    timestamp_utc: date.toISOString(),
                    timestamp_monotonic_ms: date.getTime(),
                evaluation_point: 'pre-commit',
                inputs: { evaluation_point: 'pre-commit' },
                    decision: { status: 'pass', rationale: '', badges: [] },
                    evidence_handles: [],
                    actor: { repo_id: testRepoId },
                    degraded: false
                };
                return signDecisionReceipt(base);
            };

            const receipt1 = createReceiptForDate('receipt-1', new Date(Date.UTC(2025, 0, 30))); // Jan 30, 2025 UTC
            const receipt2 = createReceiptForDate('receipt-2', new Date(Date.UTC(2025, 1, 2))); // Feb 2, 2025 UTC

            // Write to both months (use forward slashes for consistency with StoragePathResolver)
            const receiptDir1 = `${testZuRoot}/ide/receipts/${testRepoId}/2025/01`;
            const receiptDir2 = `${testZuRoot}/ide/receipts/${testRepoId}/2025/02`;
            fs.mkdirSync(receiptDir1, { recursive: true });
            fs.mkdirSync(receiptDir2, { recursive: true });
            appendReceiptsJsonl(`${receiptDir1}/receipts.jsonl`, JSON.stringify(receipt1) + '\n');
            appendReceiptsJsonl(`${receiptDir2}/receipts.jsonl`, JSON.stringify(receipt2) + '\n');

            const receipts = await reader.readReceiptsInRange(testRepoId, startDate, endDate);

            expect(receipts.length).toBe(2);
        });
    });

    describe('Read Latest Receipts', () => {
        // Helper function to get receipt ID safely
        const getReceiptId = (receipt: DecisionReceipt | FeedbackReceipt): string => {
            return 'receipt_id' in receipt ? receipt.receipt_id : receipt.feedback_id;
        };

        const createReceiptForDate = (receiptId: string, date: Date): DecisionReceipt => {
            const base: Omit<DecisionReceipt, 'signature'> = {
                receipt_id: receiptId,
                gate_id: 'gate',
                policy_version_ids: [],
                snapshot_hash: 'hash',
                timestamp_utc: date.toISOString(),
                timestamp_monotonic_ms: date.getTime(),
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: { status: 'pass', rationale: '', badges: [] },
                evidence_handles: [],
                actor: { repo_id: testRepoId },
                degraded: false
            };
            return signDecisionReceipt(base);
        };

        it('should return latest receipts sorted by timestamp', async () => {
            const now = new Date();
            const nowUTC = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), now.getUTCHours(), now.getUTCMinutes(), now.getUTCSeconds()));
            const receipt1 = createReceiptForDate('receipt-1', new Date(nowUTC.getTime() - 1000));
            const receipt2 = createReceiptForDate('receipt-2', new Date(nowUTC.getTime() - 500));
            const receipt3 = createReceiptForDate('receipt-3', nowUTC);

            // Use forward slashes (consistent with StoragePathResolver)
            const receiptDir = `${testZuRoot}/ide/receipts/${testRepoId}/${nowUTC.getUTCFullYear()}/${(nowUTC.getUTCMonth() + 1).toString().padStart(2, '0')}`;
            fs.mkdirSync(receiptDir, { recursive: true });
            appendReceiptsJsonl(
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
            const nowUTC = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), now.getUTCHours(), now.getUTCMinutes(), now.getUTCSeconds()));
            const receipts = [];
            for (let i = 0; i < 20; i++) {
                receipts.push(createReceiptForDate(`receipt-${i}`, new Date(nowUTC.getTime() - i * 1000)));
            }

            // Use forward slashes (consistent with StoragePathResolver)
            const receiptDir = `${testZuRoot}/ide/receipts/${testRepoId}/${nowUTC.getUTCFullYear()}/${(nowUTC.getUTCMonth() + 1).toString().padStart(2, '0')}`;
            fs.mkdirSync(receiptDir, { recursive: true });
            appendReceiptsJsonl(
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
            const base: Omit<DecisionReceipt, 'signature'> = {
                receipt_id: 'receipt-1',
                gate_id: 'gate',
                policy_version_ids: [],
                snapshot_hash: 'hash',
                timestamp_utc: '2025-01-15T10:00:00.000Z',
                timestamp_monotonic_ms: Date.now(),
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: { status: 'pass', rationale: '', badges: [] },
                evidence_handles: [],
                actor: { repo_id: testRepoId },
                degraded: false
            };
            const receipt = signDecisionReceipt(base);

            const receiptDir = path.join(testZuRoot, 'ide', 'receipts', testRepoId, '2025', '01');
            fs.mkdirSync(receiptDir, { recursive: true });
            appendReceiptsJsonl(path.join(receiptDir, 'receipts.jsonl'), JSON.stringify(receipt) + '\n');

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
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: { status: 'pass', rationale: '', badges: [] },
                evidence_handles: [],
                actor: { repo_id: testRepoId },
                degraded: false,
                signature: '' // Empty signature
            };

            const receiptDir = path.join(testZuRoot, 'ide', 'receipts', testRepoId, '2025', '01');
            fs.mkdirSync(receiptDir, { recursive: true });
            appendReceiptsJsonl(path.join(receiptDir, 'receipts.jsonl'), JSON.stringify(receipt) + '\n');

            const receipts = await reader.readReceipts(testRepoId, 2025, 1);

            expect(receipts.length).toBe(0);
        });
    });
});
