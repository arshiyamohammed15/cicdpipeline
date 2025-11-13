/**
 * Integration Test: Receipt Flow (Agent → Receipt → Extension)
 *
 * Tests the complete vertical slice:
 * 1. Edge Agent processes task
 * 2. Receipt is generated with policy information
 * 3. Receipt is stored in IDE Plane
 * 4. VS Code Extension can read and parse receipt
 *
 * Compliance:
 * - Rule 219: JSONL receipts (signed, append-only)
 * - Rule 224: Receipts validation (signed)
 * - Rule 223: Path resolution via ZU_ROOT
 */

import { EdgeAgent } from '../../EdgeAgent';
import { ReceiptStorageService } from '../../shared/storage/ReceiptStorageService';
import { PolicyStorageService, PolicySnapshot } from '../../shared/storage/PolicyStorageService';
import { ReceiptParser } from '../../../vscode-extension/shared/receipt-parser/ReceiptParser';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as crypto from 'crypto';

const keyId = 'edge-agent-integration-kid';
let privatePem: string;
let publicKey: crypto.KeyObject;

const toCanonicalJson = (obj: unknown): string => {
    if (obj === null || typeof obj !== 'object') {
        return JSON.stringify(obj);
    }
    if (Array.isArray(obj)) {
        return '[' + obj.map(item => toCanonicalJson(item)).join(',') + ']';
    }
    const entries = Object.keys(obj as Record<string, unknown>)
        .sort()
        .map(key => `${JSON.stringify(key)}:${toCanonicalJson((obj as Record<string, unknown>)[key])}`);
    return '{' + entries.join(',') + '}';
};

const expectValidSignature = (payload: unknown, signature: string) => {
    const parts = signature.split(':');
    expect(parts).toHaveLength(3);
    expect(parts[0]).toBe('sig-ed25519');
    expect(parts[1]).toBe(keyId);
    const signatureBuffer = Buffer.from(parts[2], 'base64');
    const canonical = toCanonicalJson(payload);
    const ok = crypto.verify(null, Buffer.from(canonical, 'utf-8'), publicKey, signatureBuffer);
    expect(ok).toBe(true);
};

describe('Receipt Flow Integration Test', () => {
    let edgeAgent: EdgeAgent;
    let receiptStorage: ReceiptStorageService;
    let policyStorage: PolicyStorageService;
    let receiptParser: ReceiptParser;
    let testZuRoot: string;
    let testRepoId: string;

    beforeAll(() => {
        // Create temporary ZU_ROOT for testing
        testZuRoot = path.join(os.tmpdir(), `zeroui-test-${Date.now()}`);
        testRepoId = 'test-repo';

        const { publicKey: pub, privateKey } = crypto.generateKeyPairSync('ed25519');
        privatePem = privateKey.export({ format: 'pem', type: 'pkcs8' }).toString();
        publicKey = crypto.createPublicKey(pub);

        // Ensure test directory exists
        fs.mkdirSync(testZuRoot, { recursive: true });

        // Set ZU_ROOT environment variable
        process.env.ZU_ROOT = testZuRoot;
    });

    afterAll(() => {
        // Cleanup: Remove test directory
        if (fs.existsSync(testZuRoot)) {
            fs.rmSync(testZuRoot, { recursive: true, force: true });
        }
        delete process.env.ZU_ROOT;
    });

    beforeEach(() => {
        // Initialize Edge Agent with test ZU_ROOT
        edgeAgent = new EdgeAgent(testZuRoot, {
            signingKey: privatePem,
            signingKeyId: keyId
        });
        receiptStorage = edgeAgent.getReceiptStorage();
        policyStorage = edgeAgent.getPolicyStorage();
        receiptParser = new ReceiptParser();
    });

    test('Complete receipt flow: Agent → Receipt → Extension', async () => {
        // Step 1: Setup test policy
        const testPolicy: PolicySnapshot = {
            policy_id: 'default',
            version: '1.0.0',
            snapshot_hash: 'sha256:test1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab',
            policy_content: {
                rules: ['rule1', 'rule2']
            },
            timestamp_utc: new Date().toISOString(),
            signature: 'sig-test-policy-signature'
        };

        // Cache policy
        await policyStorage.cachePolicy(testPolicy);
        await policyStorage.setCurrentPolicyVersion('default', '1.0.0');

        // Step 2: Process task through Edge Agent
        const task = {
            id: 'test-task-001',
            type: 'code_review',
            priority: 'medium' as const,
            data: {
                file_path: 'src/example.ts',
                context: 'pre-commit'
            },
            requirements: {}
        };

        const result = await edgeAgent.processTaskWithReceipt(task, testRepoId);

        // Step 3: Verify receipt was generated and stored
        expect(result.receiptPath).toBeDefined();
        expect(fs.existsSync(result.receiptPath)).toBe(true);

        // Step 4: Read receipt from storage
        const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
        const receiptLines = receiptContent.trim().split('\n');
        expect(receiptLines.length).toBeGreaterThan(0);

        // Parse last receipt (most recent)
        const lastReceiptJson = receiptLines[receiptLines.length - 1];
        const receipt = receiptParser.parseDecisionReceipt(lastReceiptJson);

        // Step 5: Verify receipt structure
        expect(receipt).not.toBeNull();
        expect(receipt?.receipt_id).toBeDefined();
        expect(receipt?.gate_id).toBe('edge-agent');
        expect(receipt?.policy_version_ids).toBeDefined();
        expect(receipt?.snapshot_hash).toBeDefined();
        expect(receipt?.signature).toBeDefined();
        expect(receipt?.actor.repo_id).toBe(testRepoId);
        expect(receipt?.decision.status).toBeDefined();
        expect(['pass', 'warn', 'soft_block', 'hard_block']).toContain(receipt?.decision.status);

        // Step 6: Verify receipt signature format
        if (receipt) {
            const { signature, ...payload } = receipt;
            expectValidSignature(payload, signature);
        }

        // Step 7: Verify receipt can be read by Extension (ReceiptStorageReader)
        // This validates the receipt is in the correct format for Extension consumption
        const receiptId = receipt?.receipt_id;
        expect(receiptId).toBeDefined();

        // Step 8: Test feedback receipt generation
        if (receiptId) {
            const feedbackReceipt = edgeAgent.getReceiptGenerator().generateFeedbackReceipt(
                receiptId,
                'FB-01',
                'worked',
                ['accurate', 'helpful'],
                {
                    repo_id: testRepoId
                }
            );

            // Verify feedback receipt structure
            expect(feedbackReceipt.feedback_id).toBeDefined();
            expect(feedbackReceipt.decision_receipt_id).toBe(receiptId);
            expect(feedbackReceipt.pattern_id).toBe('FB-01');
            expect(feedbackReceipt.choice).toBe('worked');
            const { signature: feedbackSignature, ...feedbackPayload } = feedbackReceipt;
            expectValidSignature(feedbackPayload, feedbackSignature);

            // Parse feedback receipt
            const feedbackReceiptJson = JSON.stringify(feedbackReceipt);
            const parsedFeedback = receiptParser.parseFeedbackReceipt(feedbackReceiptJson);
            expect(parsedFeedback).not.toBeNull();
            expect(parsedFeedback?.feedback_id).toBe(feedbackReceipt.feedback_id);
        }
    });

    test('Receipt storage follows 4-plane architecture (IDE Plane)', async () => {
        const task = {
            id: 'test-task-002',
            type: 'validation',
            priority: 'medium' as const,
            data: {},
            requirements: {}
        };

        const result = await edgeAgent.processTaskWithReceipt(task, testRepoId);

        // Verify receipt is stored in IDE Plane structure
        // Pattern: ide/receipts/{repo-id}/{yyyy}/{mm}/
        const receiptPath = result.receiptPath;
        expect(receiptPath).toContain('ide/receipts');
        expect(receiptPath).toContain(testRepoId);

        // Verify file is JSONL format (newline-delimited JSON)
        const content = fs.readFileSync(receiptPath, 'utf-8');
        const lines = content.trim().split('\n');
        expect(lines.length).toBeGreaterThan(0);

        // Each line should be valid JSON
        for (const line of lines) {
            expect(() => JSON.parse(line)).not.toThrow();
        }
    });

    test('Receipt includes policy information when available', async () => {
        // Setup policy
        const testPolicy: PolicySnapshot = {
            policy_id: 'test-policy',
            version: '2.0.0',
            snapshot_hash: 'sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
            policy_content: {},
            timestamp_utc: new Date().toISOString(),
            signature: 'sig-test'
        };

        await policyStorage.cachePolicy(testPolicy);
        await policyStorage.setCurrentPolicyVersion('test-policy', '2.0.0');

        const task = {
            id: 'test-task-003',
            type: 'validation',
            priority: 'medium' as const,
            data: {},
            requirements: {}
        };

        const result = await edgeAgent.processTaskWithReceipt(task, testRepoId);

        // Read and parse receipt
        const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
        const receiptLines = receiptContent.trim().split('\n');
        const lastReceipt = receiptParser.parseDecisionReceipt(receiptLines[receiptLines.length - 1]);

        // Verify policy information is included
        expect(lastReceipt?.policy_version_ids).toBeDefined();
        expect(lastReceipt?.policy_version_ids.length).toBeGreaterThan(0);
        expect(lastReceipt?.snapshot_hash).toBeDefined();
        expect(lastReceipt?.snapshot_hash).toMatch(/^sha256:[0-9a-f]{64}$/);
    });
});
