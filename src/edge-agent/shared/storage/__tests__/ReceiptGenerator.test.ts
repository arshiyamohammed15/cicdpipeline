/**
 * ReceiptGenerator Test Suite
 * 
 * 100% Coverage Test Suite for ReceiptGenerator
 * Tests receipt generation with all optional fields (TR-1.2.1, TR-3.2, TR-4.4, TR-6.2)
 * 
 * Coverage:
 * - generateDecisionReceipt() - all parameters, all optional fields, all evaluation points
 * - generateFeedbackReceipt() - all pattern IDs, all choices
 * - Constructor - all key loading paths
 * - Private methods - signature generation, receipt ID generation
 */

import { ReceiptGenerator } from '../ReceiptGenerator';
import { DecisionReceipt, FeedbackReceipt } from '../../receipt-types';
import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

describe('ReceiptGenerator', () => {
    let privateKey: string;
    let publicKey: crypto.KeyObject;
    const keyId = 'test-key-id';

    beforeAll(() => {
        const { publicKey: pub, privateKey: priv } = crypto.generateKeyPairSync('ed25519');
        privateKey = priv.export({ format: 'pem', type: 'pkcs8' }).toString();
        publicKey = pub;
    });

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

    describe('Constructor', () => {
        it('should create generator with privateKey option', () => {
            const generator = new ReceiptGenerator({
                privateKey: privateKey,
                keyId: keyId
            });
            expect(generator).toBeDefined();
        });

        it('should create generator with privateKeyPath option', () => {
            const tempDir = os.tmpdir();
            const keyPath = path.join(tempDir, `test-key-${Date.now()}.pem`);
            fs.writeFileSync(keyPath, privateKey);

            const generator = new ReceiptGenerator({
                privateKeyPath: keyPath,
                keyId: keyId
            });
            expect(generator).toBeDefined();

            fs.unlinkSync(keyPath);
        });

        it('should create generator with EDGE_AGENT_SIGNING_KEY env var', () => {
            const originalEnv = process.env.EDGE_AGENT_SIGNING_KEY;
            process.env.EDGE_AGENT_SIGNING_KEY = privateKey;
            process.env.EDGE_AGENT_SIGNING_KEY_ID = keyId;

            const generator = new ReceiptGenerator({});
            expect(generator).toBeDefined();

            process.env.EDGE_AGENT_SIGNING_KEY = originalEnv;
            delete process.env.EDGE_AGENT_SIGNING_KEY_ID;
        });

        it('should create generator with EDGE_AGENT_SIGNING_KEY_PATH env var', () => {
            const tempDir = os.tmpdir();
            const keyPath = path.join(tempDir, `test-key-${Date.now()}.pem`);
            fs.writeFileSync(keyPath, privateKey);

            const originalEnv = process.env.EDGE_AGENT_SIGNING_KEY_PATH;
            const originalKeyEnv = process.env.EDGE_AGENT_SIGNING_KEY;
            delete process.env.EDGE_AGENT_SIGNING_KEY; // Clear inline key to force path usage
            process.env.EDGE_AGENT_SIGNING_KEY_PATH = keyPath;
            process.env.EDGE_AGENT_SIGNING_KEY_ID = keyId;

            const generator = new ReceiptGenerator({});
            expect(generator).toBeDefined();

            process.env.EDGE_AGENT_SIGNING_KEY_PATH = originalEnv;
            if (originalKeyEnv) {
                process.env.EDGE_AGENT_SIGNING_KEY = originalKeyEnv;
            }
            delete process.env.EDGE_AGENT_SIGNING_KEY_ID;
            fs.unlinkSync(keyPath);
        });

        it('should throw error when no key provided', () => {
            const originalEnv = process.env.EDGE_AGENT_SIGNING_KEY;
            delete process.env.EDGE_AGENT_SIGNING_KEY;
            delete process.env.EDGE_AGENT_SIGNING_KEY_PATH;

            expect(() => {
                new ReceiptGenerator({});
            }).toThrow('ReceiptGenerator requires an Ed25519 private key');

            if (originalEnv) {
                process.env.EDGE_AGENT_SIGNING_KEY = originalEnv;
            }
        });

        it('should use default keyId when not provided', () => {
            const originalEnv = process.env.EDGE_AGENT_SIGNING_KEY_ID;
            delete process.env.EDGE_AGENT_SIGNING_KEY_ID;
            process.env.EDGE_AGENT_SIGNING_KEY = privateKey;

            const generator = new ReceiptGenerator({});
            // Generate a receipt to verify it works with default keyId
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' }
            );
            expect(receipt.signature).toContain('edge-agent');

            process.env.EDGE_AGENT_SIGNING_KEY_ID = originalEnv;
        });
    });

    describe('generateDecisionReceipt() - Required Fields', () => {
        let generator: ReceiptGenerator;

        beforeEach(() => {
            generator = new ReceiptGenerator({
                privateKey: privateKey,
                keyId: keyId
            });
        });

        it('should generate receipt with all required fields', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                ['policy-1.0.0'],
                'sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
                { file_count: 5 },
                {
                    status: 'pass',
                    rationale: 'All checks passed',
                    badges: ['test']
                },
                [],
                {
                    repo_id: 'test-repo'
                }
            );

            expect(receipt.receipt_id).toBeDefined();
            expect(receipt.gate_id).toBe('test-gate');
            expect(receipt.policy_version_ids).toEqual(['policy-1.0.0']);
            expect(receipt.snapshot_hash).toBe('sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890');
            expect(receipt.timestamp_utc).toBeDefined();
            expect(receipt.timestamp_monotonic_ms).toBeDefined();
            expect(receipt.evaluation_point).toBe('pre-commit');
            expect(receipt.inputs).toEqual({ file_count: 5 });
            expect(receipt.decision.status).toBe('pass');
            expect(receipt.decision.rationale).toBe('All checks passed');
            expect(receipt.decision.badges).toEqual(['test']);
            expect(receipt.evidence_handles).toEqual([]);
            expect(receipt.actor.repo_id).toBe('test-repo');
            expect(receipt.degraded).toBe(false);
            expect(receipt.signature).toBeDefined();
        });

        it('should generate receipt with valid signature', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' }
            );

            const { signature, ...payload } = receipt;
            expectValidSignature(payload, signature);
        });

        it('should generate unique receipt IDs', () => {
            const receipt1 = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' }
            );

            const receipt2 = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' }
            );

            expect(receipt1.receipt_id).not.toBe(receipt2.receipt_id);
        });

        it('should accept all evaluation_point values', () => {
            const evaluationPoints: DecisionReceipt['evaluation_point'][] = [
                'pre-commit',
                'pre-merge',
                'pre-deploy',
                'post-deploy'
            ];

            for (const point of evaluationPoints) {
                const receipt = generator.generateDecisionReceipt(
                    'test-gate',
                    [],
                    'sha256:test',
                    {},
                    { status: 'pass', rationale: 'test', badges: [] },
                    [],
                    { repo_id: 'test-repo' },
                    false,
                    point
                );

                expect(receipt.evaluation_point).toBe(point);
            }
        });

        it('should accept all decision status values', () => {
            const statuses: Array<'pass' | 'warn' | 'soft_block' | 'hard_block'> = [
                'pass',
                'warn',
                'soft_block',
                'hard_block'
            ];

            for (const status of statuses) {
                const receipt = generator.generateDecisionReceipt(
                    'test-gate',
                    [],
                    'sha256:test',
                    {},
                    { status, rationale: 'test', badges: [] },
                    [],
                    { repo_id: 'test-repo' }
                );

                expect(receipt.decision.status).toBe(status);
            }
        });

        it('should set degraded flag correctly', () => {
            const receipt1 = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' },
                false
            );
            expect(receipt1.degraded).toBe(false);

            const receipt2 = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' },
                true
            );
            expect(receipt2.degraded).toBe(true);
        });
    });

    describe('generateDecisionReceipt() - Optional Fields: actor.type (TR-6.2)', () => {
        let generator: ReceiptGenerator;

        beforeEach(() => {
            generator = new ReceiptGenerator({
                privateKey: privateKey,
                keyId: keyId
            });
        });

        it('should generate receipt without actor.type', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' }
            );

            expect(receipt.actor.type).toBeUndefined();
        });

        it('should generate receipt with actor.type = "human"', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo', type: 'human' }
            );

            expect(receipt.actor.type).toBe('human');
        });

        it('should generate receipt with actor.type = "ai"', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo', type: 'ai' }
            );

            expect(receipt.actor.type).toBe('ai');
        });

        it('should generate receipt with actor.type = "automated"', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo', type: 'automated' }
            );

            expect(receipt.actor.type).toBe('automated');
        });

        it('should include machine_fingerprint when provided', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo', machine_fingerprint: 'fp-123' }
            );

            expect(receipt.actor.machine_fingerprint).toBe('fp-123');
        });
    });

    describe('generateDecisionReceipt() - Optional Fields: context (TR-1.2.3)', () => {
        let generator: ReceiptGenerator;

        beforeEach(() => {
            generator = new ReceiptGenerator({
                privateKey: privateKey,
                keyId: keyId
            });
        });

        it('should generate receipt without context', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' }
            );

            expect(receipt.context).toBeUndefined();
        });

        it('should generate receipt with context.surface = "ide"', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' },
                false,
                'pre-commit',
                { surface: 'ide' }
            );

            expect(receipt.context?.surface).toBe('ide');
        });

        it('should generate receipt with context.surface = "pr"', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' },
                false,
                'pre-merge',
                { surface: 'pr' }
            );

            expect(receipt.context?.surface).toBe('pr');
        });

        it('should generate receipt with context.surface = "ci"', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' },
                false,
                'pre-deploy',
                { surface: 'ci' }
            );

            expect(receipt.context?.surface).toBe('ci');
        });

        it('should generate receipt with context.branch', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' },
                false,
                'pre-commit',
                { branch: 'main' }
            );

            expect(receipt.context?.branch).toBe('main');
        });

        it('should generate receipt with context.commit', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' },
                false,
                'pre-commit',
                { commit: 'abc123' }
            );

            expect(receipt.context?.commit).toBe('abc123');
        });

        it('should generate receipt with context.pr_id', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' },
                false,
                'pre-merge',
                { pr_id: 'pr-456' }
            );

            expect(receipt.context?.pr_id).toBe('pr-456');
        });

        it('should generate receipt with all context fields', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' },
                false,
                'pre-merge',
                {
                    surface: 'pr',
                    branch: 'main',
                    commit: 'abc123',
                    pr_id: 'pr-456'
                }
            );

            expect(receipt.context?.surface).toBe('pr');
            expect(receipt.context?.branch).toBe('main');
            expect(receipt.context?.commit).toBe('abc123');
            expect(receipt.context?.pr_id).toBe('pr-456');
        });
    });

    describe('generateDecisionReceipt() - Optional Fields: override (TR-3.2)', () => {
        let generator: ReceiptGenerator;

        beforeEach(() => {
            generator = new ReceiptGenerator({
                privateKey: privateKey,
                keyId: keyId
            });
        });

        it('should generate receipt without override', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' }
            );

            expect(receipt.override).toBeUndefined();
        });

        it('should generate receipt with override (required fields)', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' },
                false,
                'pre-commit',
                undefined,
                {
                    reason: 'Emergency fix',
                    approver: 'user@example.com',
                    timestamp: '2025-01-01T01:00:00.000Z'
                }
            );

            expect(receipt.override).toBeDefined();
            expect(receipt.override?.reason).toBe('Emergency fix');
            expect(receipt.override?.approver).toBe('user@example.com');
            expect(receipt.override?.timestamp).toBe('2025-01-01T01:00:00.000Z');
        });

        it('should generate receipt with override including override_id', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' },
                false,
                'pre-commit',
                undefined,
                {
                    reason: 'Emergency fix',
                    approver: 'user@example.com',
                    timestamp: '2025-01-01T01:00:00.000Z',
                    override_id: 'override-789'
                }
            );

            expect(receipt.override?.override_id).toBe('override-789');
        });
    });

    describe('generateDecisionReceipt() - Optional Fields: data_category (TR-4.4)', () => {
        let generator: ReceiptGenerator;

        beforeEach(() => {
            generator = new ReceiptGenerator({
                privateKey: privateKey,
                keyId: keyId
            });
        });

        it('should generate receipt without data_category', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' }
            );

            expect(receipt.data_category).toBeUndefined();
        });

        it('should generate receipt with data_category = "public"', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' },
                false,
                'pre-commit',
                undefined,
                undefined,
                'public'
            );

            expect(receipt.data_category).toBe('public');
        });

        it('should generate receipt with data_category = "internal"', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' },
                false,
                'pre-commit',
                undefined,
                undefined,
                'internal'
            );

            expect(receipt.data_category).toBe('internal');
        });

        it('should generate receipt with data_category = "confidential"', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' },
                false,
                'pre-commit',
                undefined,
                undefined,
                'confidential'
            );

            expect(receipt.data_category).toBe('confidential');
        });

        it('should generate receipt with data_category = "restricted"', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                [],
                'sha256:test',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo' },
                false,
                'pre-commit',
                undefined,
                undefined,
                'restricted'
            );

            expect(receipt.data_category).toBe('restricted');
        });
    });

    describe('generateDecisionReceipt() - All Optional Fields Combined', () => {
        let generator: ReceiptGenerator;

        beforeEach(() => {
            generator = new ReceiptGenerator({
                privateKey: privateKey,
                keyId: keyId
            });
        });

        it('should generate receipt with all optional fields', () => {
            const receipt = generator.generateDecisionReceipt(
                'test-gate',
                ['policy-1.0.0'],
                'sha256:test',
                { file_count: 5 },
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'test-repo', type: 'ai', machine_fingerprint: 'fp-123' },
                false,
                'pre-merge',
                {
                    surface: 'pr',
                    branch: 'main',
                    commit: 'abc123',
                    pr_id: 'pr-456'
                },
                {
                    reason: 'Emergency fix',
                    approver: 'user@example.com',
                    timestamp: '2025-01-01T01:00:00.000Z',
                    override_id: 'override-789'
                },
                'confidential'
            );

            expect(receipt.actor.type).toBe('ai');
            expect(receipt.actor.machine_fingerprint).toBe('fp-123');
            expect(receipt.context?.surface).toBe('pr');
            expect(receipt.context?.branch).toBe('main');
            expect(receipt.context?.commit).toBe('abc123');
            expect(receipt.context?.pr_id).toBe('pr-456');
            expect(receipt.override?.reason).toBe('Emergency fix');
            expect(receipt.override?.approver).toBe('user@example.com');
            expect(receipt.override?.timestamp).toBe('2025-01-01T01:00:00.000Z');
            expect(receipt.override?.override_id).toBe('override-789');
            expect(receipt.data_category).toBe('confidential');

            // Verify signature is still valid with all fields
            const { signature, ...payload } = receipt;
            expectValidSignature(payload, signature);
        });
    });

    describe('generateFeedbackReceipt()', () => {
        let generator: ReceiptGenerator;

        beforeEach(() => {
            generator = new ReceiptGenerator({
                privateKey: privateKey,
                keyId: keyId
            });
        });

        it('should generate feedback receipt with all required fields', () => {
            const receipt = generator.generateFeedbackReceipt(
                'receipt-123',
                'FB-01',
                'worked',
                ['accurate', 'helpful'],
                { repo_id: 'test-repo' }
            );

            expect(receipt.feedback_id).toBeDefined();
            expect(receipt.decision_receipt_id).toBe('receipt-123');
            expect(receipt.pattern_id).toBe('FB-01');
            expect(receipt.choice).toBe('worked');
            expect(receipt.tags).toEqual(['accurate', 'helpful']);
            expect(receipt.actor.repo_id).toBe('test-repo');
            expect(receipt.timestamp_utc).toBeDefined();
            expect(receipt.signature).toBeDefined();
        });

        it('should accept all pattern_id values', () => {
            const patternIds: Array<'FB-01' | 'FB-02' | 'FB-03' | 'FB-04'> = ['FB-01', 'FB-02', 'FB-03', 'FB-04'];

            for (const patternId of patternIds) {
                const receipt = generator.generateFeedbackReceipt(
                    'receipt-123',
                    patternId,
                    'worked',
                    [],
                    { repo_id: 'test-repo' }
                );

                expect(receipt.pattern_id).toBe(patternId);
            }
        });

        it('should accept all choice values', () => {
            const choices: Array<'worked' | 'partly' | 'didnt'> = ['worked', 'partly', 'didnt'];

            for (const choice of choices) {
                const receipt = generator.generateFeedbackReceipt(
                    'receipt-123',
                    'FB-01',
                    choice,
                    [],
                    { repo_id: 'test-repo' }
                );

                expect(receipt.choice).toBe(choice);
            }
        });

        it('should include machine_fingerprint when provided', () => {
            const receipt = generator.generateFeedbackReceipt(
                'receipt-123',
                'FB-01',
                'worked',
                [],
                { repo_id: 'test-repo', machine_fingerprint: 'fp-123' }
            );

            expect(receipt.actor.machine_fingerprint).toBe('fp-123');
        });

        it('should generate valid signature for feedback receipt', () => {
            const receipt = generator.generateFeedbackReceipt(
                'receipt-123',
                'FB-01',
                'worked',
                [],
                { repo_id: 'test-repo' }
            );

            const { signature, ...payload } = receipt;
            expectValidSignature(payload, signature);
        });

        it('should generate unique feedback IDs', () => {
            const receipt1 = generator.generateFeedbackReceipt(
                'receipt-123',
                'FB-01',
                'worked',
                [],
                { repo_id: 'test-repo' }
            );

            const receipt2 = generator.generateFeedbackReceipt(
                'receipt-123',
                'FB-01',
                'worked',
                [],
                { repo_id: 'test-repo' }
            );

            expect(receipt1.feedback_id).not.toBe(receipt2.feedback_id);
        });
    });
});
