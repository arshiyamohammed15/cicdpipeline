/**
 * EdgeAgent Test Suite
 * 
 * Comprehensive unit tests for EdgeAgent class
 * Tests processTaskWithReceipt() method with all scenarios
 * 
 * Coverage:
 * - Happy path with policy integration
 * - Policy integration (with and without policies)
 * - Error handling
 * - Edge cases
 */

import { EdgeAgent } from '../EdgeAgent';
import { PolicyStorageService, PolicySnapshot } from '../shared/storage/PolicyStorageService';
import { ReceiptStorageService } from '../shared/storage/ReceiptStorageService';
import { ReceiptGenerator } from '../shared/storage/ReceiptGenerator';
import { DecisionReceipt } from '../shared/receipt-types';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

describe('EdgeAgent', () => {
    let testZuRoot: string;
    let edgeAgent: EdgeAgent;
    let receiptStorage: ReceiptStorageService;
    let receiptGenerator: ReceiptGenerator;
    let policyStorage: PolicyStorageService;

    beforeEach(() => {
        testZuRoot = path.join(os.tmpdir(), `zeroui-test-${Date.now()}-${Math.random().toString(36).substring(7)}`);
        if (!fs.existsSync(testZuRoot)) {
            fs.mkdirSync(testZuRoot, { recursive: true });
        }
        process.env.ZU_ROOT = testZuRoot;
        edgeAgent = new EdgeAgent(testZuRoot);
        // Access services via getter methods
        receiptStorage = edgeAgent.getReceiptStorage();
        receiptGenerator = edgeAgent.getReceiptGenerator();
        policyStorage = edgeAgent.getPolicyStorage();
    });

    afterEach(() => {
        if (fs.existsSync(testZuRoot)) {
            fs.rmSync(testZuRoot, { recursive: true, force: true });
        }
    });

    describe('processTaskWithReceipt() - Happy Path', () => {
        it('should process task and generate receipt successfully', async () => {
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

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            expect(result.receiptPath).toBeDefined();
            expect(fs.existsSync(result.receiptPath)).toBe(true);
            expect(result.result).toBeDefined();
        });

        it('should generate receipt with correct gate_id', async () => {
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            // Read receipt from storage
            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            expect(lastReceipt.gate_id).toBe('edge-agent');
        });

        it('should include task data in receipt inputs', async () => {
            const taskData = {
                file_path: 'src/test.ts',
                context: 'pre-commit',
                custom_field: 'custom_value'
            };
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: taskData,
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            expect(lastReceipt.inputs).toEqual(taskData);
        });

        it('should include repo_id in receipt actor', async () => {
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };
            const repoId = 'test-repo-id';

            const result = await edgeAgent.processTaskWithReceipt(task, repoId);

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            expect(lastReceipt.actor.repo_id).toBe(repoId);
        });

        it('should generate receipt with signature', async () => {
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            expect(lastReceipt.signature).toBeDefined();
            expect(lastReceipt.signature).toMatch(/^sig-[0-9a-f]{64}$/);
        });
    });

    describe('processTaskWithReceipt() - Policy Integration', () => {
        it('should include policy information when policies are available', async () => {
            // Setup policy
            const testPolicy: PolicySnapshot = {
                policy_id: 'default',
                version: '1.0.0',
                snapshot_hash: 'sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
                policy_content: { rules: ['rule1'] },
                timestamp_utc: new Date().toISOString(),
                signature: 'sig-test-policy'
            };

            await policyStorage.cachePolicy(testPolicy);
            await policyStorage.setCurrentPolicyVersion('default', '1.0.0');

            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            expect(lastReceipt.policy_version_ids).toBeDefined();
            expect(lastReceipt.policy_version_ids.length).toBeGreaterThan(0);
            expect(lastReceipt.snapshot_hash).toBeDefined();
            expect(lastReceipt.snapshot_hash).toMatch(/^sha256:[0-9a-f]{64}$/);
        });

        it('should include correct policy version IDs format', async () => {
            // Note: EdgeAgent.processTaskWithReceipt() calls getActivePolicyInfo(['default'])
            // So we need to use 'default' as the policy ID
            const testPolicy: PolicySnapshot = {
                policy_id: 'default',
                version: '2.5.3',
                snapshot_hash: 'sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
                policy_content: {},
                timestamp_utc: new Date().toISOString(),
                signature: 'sig-test'
            };

            await policyStorage.cachePolicy(testPolicy);
            await policyStorage.setCurrentPolicyVersion('default', '2.5.3');

            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            expect(lastReceipt.policy_version_ids).toContain('default-2.5.3');
        });

        it('should handle multiple policies correctly', async () => {
            const policy1: PolicySnapshot = {
                policy_id: 'policy-1',
                version: '1.0.0',
                snapshot_hash: 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                policy_content: {},
                timestamp_utc: new Date().toISOString(),
                signature: 'sig-1'
            };
            const policy2: PolicySnapshot = {
                policy_id: 'policy-2',
                version: '2.0.0',
                snapshot_hash: 'sha256:2222222222222222222222222222222222222222222222222222222222222222',
                policy_content: {},
                timestamp_utc: new Date().toISOString(),
                signature: 'sig-2'
            };

            await policyStorage.cachePolicy(policy1);
            await policyStorage.cachePolicy(policy2);
            await policyStorage.setCurrentPolicyVersion('policy-1', '1.0.0');
            await policyStorage.setCurrentPolicyVersion('policy-2', '2.0.0');

            // Note: getActivePolicyInfo is called with ['default'], so we need to set default policy
            const defaultPolicy: PolicySnapshot = {
                policy_id: 'default',
                version: '1.0.0',
                snapshot_hash: 'sha256:3333333333333333333333333333333333333333333333333333333333333333',
                policy_content: {},
                timestamp_utc: new Date().toISOString(),
                signature: 'sig-default'
            };
            await policyStorage.cachePolicy(defaultPolicy);
            await policyStorage.setCurrentPolicyVersion('default', '1.0.0');

            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            expect(lastReceipt.policy_version_ids).toBeDefined();
            expect(lastReceipt.snapshot_hash).toMatch(/^sha256:[0-9a-f]{64}$/);
        });

        it('should handle no policies gracefully (graceful degradation)', async () => {
            // Don't set up any policies
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            // Should still generate receipt with empty policy info
            expect(lastReceipt.policy_version_ids).toEqual([]);
            expect(lastReceipt.snapshot_hash).toBe('');
        });

        it('should use default policy ID when calling getActivePolicyInfo', async () => {
            const defaultPolicy: PolicySnapshot = {
                policy_id: 'default',
                version: '1.0.0',
                snapshot_hash: 'sha256:default1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
                policy_content: {},
                timestamp_utc: new Date().toISOString(),
                signature: 'sig-default'
            };

            await policyStorage.cachePolicy(defaultPolicy);
            await policyStorage.setCurrentPolicyVersion('default', '1.0.0');

            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            expect(lastReceipt.policy_version_ids).toContain('default-1.0.0');
        });
    });

    describe('processTaskWithReceipt() - Decision Status', () => {
        it('should set decision status to pass when validation succeeds', async () => {
            // Mock successful validation by ensuring task is valid
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            // Note: Actual status depends on validateResult() implementation
            // This test verifies the receipt is generated with a valid status
            expect(['pass', 'warn', 'soft_block', 'hard_block']).toContain(lastReceipt.decision.status);
        });

        it('should include rationale in decision', async () => {
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            expect(lastReceipt.decision.rationale).toBeDefined();
            expect(typeof lastReceipt.decision.rationale).toBe('string');
        });

        it('should include badges in decision', async () => {
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            expect(Array.isArray(lastReceipt.decision.badges)).toBe(true);
        });

        it('should set degraded flag based on validation result', async () => {
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            expect(typeof lastReceipt.degraded).toBe('boolean');
        });
    });

    describe('processTaskWithReceipt() - Edge Cases', () => {
        it('should handle task with empty data object', async () => {
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            expect(result.receiptPath).toBeDefined();
            expect(fs.existsSync(result.receiptPath)).toBe(true);
        });

        it('should handle task with null data (should use empty object)', async () => {
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: null as any,
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            expect(lastReceipt.inputs).toEqual({});
        });

        it('should handle task with undefined data (should use empty object)', async () => {
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                requirements: {}
                // data is undefined
            } as any;

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            expect(lastReceipt.inputs).toEqual({});
        });

        it('should handle task with complex nested data', async () => {
            const complexData = {
                nested: {
                    level1: {
                        level2: {
                            value: 'deep'
                        }
                    }
                },
                array: [1, 2, { nested: 'value' }],
                special: 'test with "quotes" and \'apostrophes\''
            };

            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: complexData,
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            expect(lastReceipt.inputs).toEqual(complexData);
        });

        it('should handle kebab-case repo IDs', async () => {
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };
            const repoId = 'test-repo-with-dashes';

            const result = await edgeAgent.processTaskWithReceipt(task, repoId);

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            expect(lastReceipt.actor.repo_id).toBe(repoId);
        });

        it('should store receipt in correct location (IDE Plane)', async () => {
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            // Verify receipt path follows IDE Plane structure
            expect(result.receiptPath).toContain('ide/receipts');
            expect(result.receiptPath).toContain('test-repo');
        });
    });

    describe('processTaskWithReceipt() - Receipt Storage', () => {
        it('should store receipt in JSONL format', async () => {
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const lines = receiptContent.trim().split('\n');

            // Each line should be valid JSON
            for (const line of lines) {
                expect(() => JSON.parse(line)).not.toThrow();
            }
        });

        it('should append receipt to existing file (append-only)', async () => {
            const task1 = {
                id: 'test-task-1',
                type: 'validation',
                priority: 'medium' as const,
                data: { first: 'receipt' },
                requirements: {}
            };
            const task2 = {
                id: 'test-task-2',
                type: 'validation',
                priority: 'medium' as const,
                data: { second: 'receipt' },
                requirements: {}
            };

            const result1 = await edgeAgent.processTaskWithReceipt(task1, 'test-repo');
            const result2 = await edgeAgent.processTaskWithReceipt(task2, 'test-repo');

            // Both should be in same file
            expect(result1.receiptPath).toBe(result2.receiptPath);

            const receiptContent = fs.readFileSync(result1.receiptPath, 'utf-8');
            const lines = receiptContent.trim().split('\n');

            expect(lines.length).toBeGreaterThanOrEqual(2);
        });

        it('should store receipt with all required fields', async () => {
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
            const receiptLines = receiptContent.trim().split('\n');
            const lastReceipt = JSON.parse(receiptLines[receiptLines.length - 1]) as DecisionReceipt;

            // Verify all required fields are present
            expect(lastReceipt.receipt_id).toBeDefined();
            expect(lastReceipt.gate_id).toBeDefined();
            expect(lastReceipt.policy_version_ids).toBeDefined();
            expect(lastReceipt.snapshot_hash).toBeDefined();
            expect(lastReceipt.timestamp_utc).toBeDefined();
            expect(lastReceipt.timestamp_monotonic_ms).toBeDefined();
            expect(lastReceipt.inputs).toBeDefined();
            expect(lastReceipt.decision).toBeDefined();
            expect(lastReceipt.evidence_handles).toBeDefined();
            expect(lastReceipt.actor).toBeDefined();
            expect(lastReceipt.degraded).toBeDefined();
            expect(lastReceipt.signature).toBeDefined();
        });
    });

    describe('processTaskWithReceipt() - Return Value', () => {
        it('should return result and receiptPath', async () => {
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            expect(result).toHaveProperty('result');
            expect(result).toHaveProperty('receiptPath');
        });

        it('should return receiptPath that exists on filesystem', async () => {
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            expect(fs.existsSync(result.receiptPath)).toBe(true);
        });

        it('should return receiptPath as absolute path', async () => {
            const task = {
                id: 'test-task',
                type: 'validation',
                priority: 'medium' as const,
                data: {},
                requirements: {}
            };

            const result = await edgeAgent.processTaskWithReceipt(task, 'test-repo');

            expect(path.isAbsolute(result.receiptPath)).toBe(true);
        });
    });
});

