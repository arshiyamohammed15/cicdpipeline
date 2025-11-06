/**
 * Storage Integration Test Suite
 * 
 * End-to-end tests for storage integration
 * Tests receipt generation, storage, and reading flow
 */

import { EdgeAgent } from '../../../EdgeAgent';
import { ReceiptStorageService } from '../ReceiptStorageService';
import { ReceiptGenerator } from '../ReceiptGenerator';
import { DecisionReceipt } from '../../receipt-types';
import * as fs from 'fs';
import * as os from 'os';

describe('Storage Integration Tests', () => {
    const testZuRoot = os.tmpdir() + '/zeroui-integration-test-' + Date.now();
    const testRepoId = 'integration-test-repo';

    beforeEach(() => {
        if (!fs.existsSync(testZuRoot)) {
            fs.mkdirSync(testZuRoot, { recursive: true });
        }
        process.env.ZU_ROOT = testZuRoot;
    });

    afterEach(() => {
        if (fs.existsSync(testZuRoot)) {
            fs.rmSync(testZuRoot, { recursive: true, force: true });
        }
    });

    describe('Receipt Flow: Generate -> Store -> Read', () => {
        it('should complete full receipt flow', async () => {
            // Generate receipt
            const generator = new ReceiptGenerator();
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                ['policy-v1'],
                'snapshot-hash',
                { input: 'test-data' },
                { status: 'pass', rationale: 'Test passed', badges: ['validated'] },
                [],
                { repo_id: testRepoId },
                false
            );

            // Store receipt
            const storageService = new ReceiptStorageService(testZuRoot);
            const receiptPath = await storageService.storeDecisionReceipt(receipt, testRepoId);

            expect(fs.existsSync(receiptPath)).toBe(true);

            // Read receipt using ReceiptStorageService (simulating VS Code Extension read)
            const date = new Date(receipt.timestamp_utc);
            const year = date.getUTCFullYear();
            const month = date.getUTCMonth() + 1;

            const receiptLines = await storageService.readReceipts(testRepoId, year, month);
            const receipts = receiptLines
                .map(line => JSON.parse(line) as DecisionReceipt)
                .filter(r => r.receipt_id !== undefined);

            expect(receipts.length).toBe(1);
            expect(receipts[0].receipt_id).toBe(receipt.receipt_id);
            expect(receipts[0].gate_id).toBe('test-gate');
        });

        it('should handle multiple receipts in same month', async () => {
            const generator = new ReceiptGenerator();
            const storageService = new ReceiptStorageService(testZuRoot);

            // Generate and store multiple receipts
            const receipts = [];
            for (let i = 0; i < 5; i++) {
                const receipt = generator.generateDecisionReceipt(
                    `gate-${i}`, [], 'hash', {}, { status: 'pass', rationale: '', badges: [] },
                    [], { repo_id: testRepoId }, false
                );
                receipt.timestamp_utc = '2025-01-15T10:00:00.000Z';
                await storageService.storeDecisionReceipt(receipt, testRepoId);
                receipts.push(receipt);
            }

            // Read all receipts using ReceiptStorageService
            const receiptLines = await storageService.readReceipts(testRepoId, 2025, 1);
            const readReceipts = receiptLines
                .map(line => JSON.parse(line) as DecisionReceipt)
                .filter(r => r.receipt_id !== undefined);

            expect(readReceipts.length).toBe(5);
        });

        it('should handle receipts across different months', async () => {
            const generator = new ReceiptGenerator();
            const storageService = new ReceiptStorageService(testZuRoot);

            // Create receipts for different months
            const receipt1 = generator.generateDecisionReceipt(
                'gate1', [], 'hash1', {}, { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );
            receipt1.timestamp_utc = '2025-01-15T10:00:00.000Z';

            const receipt2 = generator.generateDecisionReceipt(
                'gate2', [], 'hash2', {}, { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );
            receipt2.timestamp_utc = '2025-02-15T10:00:00.000Z';

            await storageService.storeDecisionReceipt(receipt1, testRepoId);
            await storageService.storeDecisionReceipt(receipt2, testRepoId);

            // Read from both months using ReceiptStorageService
            const lines1 = await storageService.readReceipts(testRepoId, 2025, 1);
            const lines2 = await storageService.readReceipts(testRepoId, 2025, 2);
            const receipts1 = lines1.map(l => JSON.parse(l) as DecisionReceipt).filter(r => r.receipt_id !== undefined);
            const receipts2 = lines2.map(l => JSON.parse(l) as DecisionReceipt).filter(r => r.receipt_id !== undefined);

            expect(receipts1.length).toBe(1);
            expect(receipts2.length).toBe(1);
            expect(receipts1[0].receipt_id).toBe(receipt1.receipt_id);
            expect(receipts2[0].receipt_id).toBe(receipt2.receipt_id);
        });
    });

    describe('Edge Agent Integration', () => {
        it('should integrate with EdgeAgent storage services', async () => {
            const agent = new EdgeAgent(testZuRoot);

            // Verify storage services are initialized
            const receiptStorage = agent.getReceiptStorage();
            const receiptGenerator = agent.getReceiptGenerator();
            const policyStorage = agent.getPolicyStorage();

            expect(receiptStorage).toBeDefined();
            expect(receiptGenerator).toBeDefined();
            expect(policyStorage).toBeDefined();
        });

        it('should process task and generate receipt', async () => {
            const agent = new EdgeAgent(testZuRoot);

            const task = {
                type: 'test',
                data: { input: 'test-data' }
            };

            const result = await agent.processTaskWithReceipt(task, testRepoId);

            expect(result.receiptPath).toBeDefined();
            expect(fs.existsSync(result.receiptPath)).toBe(true);
        });
    });

    describe('Cross-Tier Integration', () => {
        it('should store receipt in Edge Agent and read in VS Code Extension', async () => {
            // Edge Agent: Generate and store
            const generator = new ReceiptGenerator();
            const storageService = new ReceiptStorageService(testZuRoot);

            const receipt = generator.generateDecisionReceipt(
                'gate', [], 'hash', {}, { status: 'pass', rationale: '', badges: [] },
                [], { repo_id: testRepoId }, false
            );

            await storageService.storeDecisionReceipt(receipt, testRepoId);

            // Read receipt using ReceiptStorageService (simulating VS Code Extension read)
            const date = new Date(receipt.timestamp_utc);
            const year = date.getUTCFullYear();
            const month = date.getUTCMonth() + 1;

            const receiptLines = await storageService.readReceipts(testRepoId, year, month);
            const receipts = receiptLines
                .map(line => JSON.parse(line) as DecisionReceipt)
                .filter(r => r.receipt_id !== undefined);

            expect(receipts.length).toBe(1);
            expect(receipts[0].receipt_id).toBe(receipt.receipt_id);
        });

        it('should maintain receipt integrity across tiers', async () => {
            const generator = new ReceiptGenerator();
            const storageService = new ReceiptStorageService(testZuRoot);

            const originalReceipt = generator.generateDecisionReceipt(
                'gate', ['policy-v1'], 'hash', { data: 'test' },
                { status: 'pass', rationale: 'Test', badges: ['badge1'] },
                [{ url: 'https://example.com', type: 'log', description: 'Log' }],
                { repo_id: testRepoId, machine_fingerprint: 'fp-123' },
                false
            );

            await storageService.storeDecisionReceipt(originalReceipt, testRepoId);

            const date = new Date(originalReceipt.timestamp_utc);
            const receiptLines = await storageService.readReceipts(testRepoId, date.getUTCFullYear(), date.getUTCMonth() + 1);
            const receipts = receiptLines
                .map(line => JSON.parse(line) as DecisionReceipt)
                .filter(r => r.receipt_id !== undefined);

            const readReceipt = receipts[0];

            // Verify all fields are preserved
            expect(readReceipt.gate_id).toBe(originalReceipt.gate_id);
            expect(readReceipt.policy_version_ids).toEqual(originalReceipt.policy_version_ids);
            expect(readReceipt.snapshot_hash).toBe(originalReceipt.snapshot_hash);
            expect(readReceipt.decision.status).toBe(originalReceipt.decision.status);
            expect(readReceipt.actor.repo_id).toBe(originalReceipt.actor.repo_id);
        });
    });
});

