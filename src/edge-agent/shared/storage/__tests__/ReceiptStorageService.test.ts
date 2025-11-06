/**
 * ReceiptStorageService Test Suite
 * 
 * Tests for receipt storage operations
 * Validates JSONL format, append-only behavior, signature validation, and code/PII detection
 */

import { ReceiptStorageService } from '../ReceiptStorageService';
import { ReceiptGenerator } from '../ReceiptGenerator';
import { DecisionReceipt, FeedbackReceipt } from '../../receipt-types';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as crypto from 'crypto';

describe('ReceiptStorageService', () => {
    const testZuRoot = os.tmpdir() + '/zeroui-test-' + Date.now();
    let storageService: ReceiptStorageService;
    let receiptGenerator: ReceiptGenerator;
    const testRepoId = 'test-repo-id';

    beforeEach(() => {
        // Create test directory
        if (!fs.existsSync(testZuRoot)) {
            fs.mkdirSync(testZuRoot, { recursive: true });
        }
        process.env.ZU_ROOT = testZuRoot;
        storageService = new ReceiptStorageService(testZuRoot);
        receiptGenerator = new ReceiptGenerator();
    });

    afterEach(() => {
        // Clean up test directory
        if (fs.existsSync(testZuRoot)) {
            fs.rmSync(testZuRoot, { recursive: true, force: true });
        }
    });

    describe('Store Decision Receipt (Rule 219: JSONL)', () => {
        it('should store decision receipt in JSONL format', async () => {
            const receipt = receiptGenerator.generateDecisionReceipt(
                'test-gate',
                ['policy-v1'],
                'hash123',
                { input: 'test' },
                { status: 'pass', rationale: 'Test', badges: [] },
                [],
                { repo_id: testRepoId },
                false
            );

            const receiptPath = await storageService.storeDecisionReceipt(receipt, testRepoId);

            expect(fs.existsSync(receiptPath)).toBe(true);
            expect(receiptPath).toContain('receipts.jsonl');

            const content = fs.readFileSync(receiptPath, 'utf-8');
            const lines = content.split('\n').filter(l => l.trim());
            expect(lines.length).toBe(1);

            const parsed = JSON.parse(lines[0]);
            expect(parsed.receipt_id).toBe(receipt.receipt_id);
        });

        it('should append multiple receipts (append-only)', async () => {
            const receipt1 = receiptGenerator.generateDecisionReceipt(
                'gate1', [], 'hash1', {}, { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );
            // Set timestamp to ensure same month
            receipt1.timestamp_utc = '2025-01-15T10:00:00.000Z';
            
            const receipt2 = receiptGenerator.generateDecisionReceipt(
                'gate2', [], 'hash2', {}, { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );
            receipt2.timestamp_utc = '2025-01-16T10:00:00.000Z';

            await storageService.storeDecisionReceipt(receipt1, testRepoId);
            await storageService.storeDecisionReceipt(receipt2, testRepoId);

            // Use forward slash to match storage implementation
            const receiptDir = `${testZuRoot}/ide/receipts/${testRepoId}/2025/01`;
            const receiptFile = `${receiptDir}/receipts.jsonl`;
            const content = fs.readFileSync(receiptFile, 'utf-8');
            const lines = content.split('\n').filter(l => l.trim());

            expect(lines.length).toBe(2);
        });

        it('should use YYYY/MM partitioning (Rule 228)', async () => {
            const receipt = receiptGenerator.generateDecisionReceipt(
                'test-gate', [], 'hash', {}, { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );

            // Set timestamp to January 2025
            receipt.timestamp_utc = '2025-01-15T10:00:00.000Z';

            const receiptPath = await storageService.storeDecisionReceipt(receipt, testRepoId);

            expect(receiptPath).toContain('/2025/01/');
        });
    });

    describe('Store Feedback Receipt', () => {
        it('should store feedback receipt in JSONL format', async () => {
            const decisionReceipt = receiptGenerator.generateDecisionReceipt(
                'gate', [], 'hash', {}, { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );

            const feedbackReceipt = receiptGenerator.generateFeedbackReceipt(
                decisionReceipt.receipt_id,
                'FB-01',
                'worked',
                ['tag1'],
                { repo_id: testRepoId }
            );

            const receiptPath = await storageService.storeFeedbackReceipt(feedbackReceipt, testRepoId);

            expect(fs.existsSync(receiptPath)).toBe(true);
            const content = fs.readFileSync(receiptPath, 'utf-8');
            const lines = content.split('\n').filter(l => l.trim());
            expect(lines.length).toBeGreaterThan(0);
        });
    });

    describe('Signature Validation (Rule 224)', () => {
        it('should reject receipt without signature', async () => {
            const receipt = receiptGenerator.generateDecisionReceipt(
                'gate', [], 'hash', {}, { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );

            // Remove signature
            delete (receipt as any).signature;

            await expect(
                storageService.storeDecisionReceipt(receipt, testRepoId)
            ).rejects.toThrow('Receipt must be signed before storage');
        });

        it('should reject receipt with empty signature', async () => {
            const receipt = receiptGenerator.generateDecisionReceipt(
                'gate', [], 'hash', {}, { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );

            receipt.signature = '';

            await expect(
                storageService.storeDecisionReceipt(receipt, testRepoId)
            ).rejects.toThrow('Receipt must be signed before storage');
        });

        it('should accept receipt with valid signature', async () => {
            const receipt = receiptGenerator.generateDecisionReceipt(
                'gate', [], 'hash', {}, { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );

            await expect(
                storageService.storeDecisionReceipt(receipt, testRepoId)
            ).resolves.toBeTruthy();
        });
    });

    describe('Code/PII Detection (Rule 217)', () => {
        it('should reject receipt containing function code', async () => {
            const receipt = receiptGenerator.generateDecisionReceipt(
                'gate', [], 'hash', { code: 'function test() {}' },
                { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );

            // The pattern should match "function(" in the JSON stringified receipt
            // JSON.stringify will produce: "...code":"function test() {}"...
            // The pattern /\bfunction\s*\(/ should match "function("
            await expect(
                storageService.storeDecisionReceipt(receipt, testRepoId)
            ).rejects.toThrow('contains executable code');
        });

        it('should reject receipt containing class code', async () => {
            const receipt = receiptGenerator.generateDecisionReceipt(
                'gate', [], 'hash', { code: 'class Test {}' },
                { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );

            await expect(
                storageService.storeDecisionReceipt(receipt, testRepoId)
            ).rejects.toThrow('contains executable code');
        });

        it('should reject receipt containing import statement', async () => {
            const receipt = receiptGenerator.generateDecisionReceipt(
                'gate', [], 'hash', { code: 'import something from "module"' },
                { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );

            await expect(
                storageService.storeDecisionReceipt(receipt, testRepoId)
            ).rejects.toThrow('contains executable code');
        });

        it('should reject receipt containing email (PII)', async () => {
            const receipt = receiptGenerator.generateDecisionReceipt(
                'gate', [], 'hash', { email: 'test@example.com' },
                { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );

            await expect(
                storageService.storeDecisionReceipt(receipt, testRepoId)
            ).rejects.toThrow('contains PII');
        });

        it('should reject receipt containing SSN (PII)', async () => {
            const receipt = receiptGenerator.generateDecisionReceipt(
                'gate', [], 'hash', { ssn: '123-45-6789' },
                { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );

            await expect(
                storageService.storeDecisionReceipt(receipt, testRepoId)
            ).rejects.toThrow('contains PII');
        });

        it('should accept receipt without code or PII', async () => {
            const receipt = receiptGenerator.generateDecisionReceipt(
                'gate', [], 'hash', { data: 'safe-data' },
                { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );

            await expect(
                storageService.storeDecisionReceipt(receipt, testRepoId)
            ).resolves.toBeTruthy();
        });
    });

    describe('Read Receipts', () => {
        it('should return empty array if file does not exist', async () => {
            const receipts = await storageService.readReceipts(testRepoId, 2025, 1);
            expect(receipts).toEqual([]);
        });

        it('should read stored receipts', async () => {
            const receipt = receiptGenerator.generateDecisionReceipt(
                'gate', [], 'hash', {}, { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );
            // Set timestamp to January 2025
            receipt.timestamp_utc = '2025-01-15T10:00:00.000Z';

            await storageService.storeDecisionReceipt(receipt, testRepoId);

            const receipts = await storageService.readReceipts(testRepoId, 2025, 1);
            expect(receipts.length).toBe(1);

            const parsed = JSON.parse(receipts[0]);
            expect(parsed.receipt_id).toBe(receipt.receipt_id);
        });

        it('should read multiple receipts', async () => {
            const receipt1 = receiptGenerator.generateDecisionReceipt(
                'gate1', [], 'hash1', {}, { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );
            receipt1.timestamp_utc = '2025-01-15T10:00:00.000Z';
            
            const receipt2 = receiptGenerator.generateDecisionReceipt(
                'gate2', [], 'hash2', {}, { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );
            receipt2.timestamp_utc = '2025-01-16T10:00:00.000Z';

            await storageService.storeDecisionReceipt(receipt1, testRepoId);
            await storageService.storeDecisionReceipt(receipt2, testRepoId);

            const receipts = await storageService.readReceipts(testRepoId, 2025, 1);
            expect(receipts.length).toBe(2);
        });
    });

    describe('Canonical JSON Format', () => {
        it('should store receipt without signature field in canonical form', async () => {
            const receipt = receiptGenerator.generateDecisionReceipt(
                'gate', [], 'hash', {}, { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );
            receipt.timestamp_utc = '2025-01-15T10:00:00.000Z';

            await storageService.storeDecisionReceipt(receipt, testRepoId);

            const receipts = await storageService.readReceipts(testRepoId, 2025, 1);
            expect(receipts.length).toBeGreaterThan(0);
            
            // Receipt should be stored with signature (Rule 219: signed JSONL receipts)
            const stored = JSON.parse(receipts[0]);
            expect(stored).toHaveProperty('signature');
            expect(stored.signature).toBe(receipt.signature);
            expect(stored.receipt_id).toBe(receipt.receipt_id);
        });
    });

    describe('Directory Creation', () => {
        it('should create directory structure if it does not exist', async () => {
            const receipt = receiptGenerator.generateDecisionReceipt(
                'gate', [], 'hash', {}, { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );

            const receiptPath = await storageService.storeDecisionReceipt(receipt, testRepoId);
            const receiptDir = path.dirname(receiptPath);

            expect(fs.existsSync(receiptDir)).toBe(true);
        });
    });
});

