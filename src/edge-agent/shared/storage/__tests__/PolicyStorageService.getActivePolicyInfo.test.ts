/**
 * PolicyStorageService.getActivePolicyInfo() Test Suite
 *
 * Comprehensive unit tests for getActivePolicyInfo() method
 * Tests all positive, negative, and edge cases
 *
 * Coverage:
 * - Single policy case
 * - Multiple policies case
 * - Empty policies case
 * - Non-existent policies
 * - Policy version ID format
 * - Snapshot hash combination (deterministic)
 * - Snapshot hash format
 * - Edge cases
 */

import { PolicyStorageService, PolicySnapshot } from '../PolicyStorageService';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as crypto from 'crypto';

describe('PolicyStorageService.getActivePolicyInfo()', () => {
    let testZuRoot: string;
    let policyService: PolicyStorageService;
    let privateKey: crypto.KeyObject;
    let publicPem: string;

    const toCanonicalJson = (obj: any): string => {
        if (obj === null || typeof obj !== 'object') {
            return JSON.stringify(obj);
        }
        if (Array.isArray(obj)) {
            return '[' + obj.map(item => toCanonicalJson(item)).join(',') + ']';
        }
        const sortedKeys = Object.keys(obj).sort();
        const entries = sortedKeys.map(key => `${JSON.stringify(key)}:${toCanonicalJson(obj[key])}`);
        return '{' + entries.join(',') + '}';
    };

    const signSnapshot = (snapshot: Omit<PolicySnapshot, 'signature'>, keyId: string): string => {
        const canonical = toCanonicalJson(snapshot);
        const signature = crypto.sign(null, Buffer.from(canonical, 'utf-8'), privateKey);
        return `sig-ed25519:${keyId}:${signature.toString('base64')}`;
    };

    const createPolicySnapshot = (policyId: string, version: string, snapshotHash?: string): PolicySnapshot => {
        const base: Omit<PolicySnapshot, 'signature'> = {
            policy_id: policyId,
            version: version,
            snapshot_hash: snapshotHash || `sha256:${crypto.randomBytes(32).toString('hex')}`,
            policy_content: { rule: 'test-rule', value: 'test-value' },
            timestamp_utc: new Date().toISOString()
        };
        return {
            ...base,
            signature: signSnapshot(base, 'policy-kid')
        };
    };

    beforeEach(() => {
        const { publicKey, privateKey: priv } = crypto.generateKeyPairSync('ed25519');
        privateKey = priv;
        publicPem = publicKey.export({ format: 'pem', type: 'spki' }).toString();
        testZuRoot = path.join(os.tmpdir(), `zeroui-test-${Date.now()}-${Math.random().toString(36).substring(7)}`);
        if (!fs.existsSync(testZuRoot)) {
            fs.mkdirSync(testZuRoot, { recursive: true });
        }
        process.env.ZU_ROOT = testZuRoot;
        policyService = new PolicyStorageService(testZuRoot, { verificationKey: publicPem });
    });

    afterEach(() => {
        if (fs.existsSync(testZuRoot)) {
            fs.rmSync(testZuRoot, { recursive: true, force: true });
        }
    });

    describe('Single Policy Case', () => {
        it('should return policy info for single existing policy', async () => {
            const snapshot = createPolicySnapshot('policy-1', '1.0.0', 'sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890');

            await policyService.cachePolicy(snapshot);
            await policyService.setCurrentPolicyVersion('policy-1', '1.0.0');

            const result = await policyService.getActivePolicyInfo(['policy-1']);

            expect(result.policy_version_ids).toHaveLength(1);
            expect(result.policy_version_ids[0]).toBe('policy-1-1.0.0');
            expect(result.snapshot_hash).toBeDefined();
            expect(result.snapshot_hash).toMatch(/^sha256:[0-9a-f]{64}$/);
        });

        it('should format policy version ID correctly (policy_id-version)', async () => {
            const snapshot = createPolicySnapshot('test-policy', '2.5.3');

            await policyService.cachePolicy(snapshot);
            await policyService.setCurrentPolicyVersion('test-policy', '2.5.3');

            const result = await policyService.getActivePolicyInfo(['test-policy']);

            expect(result.policy_version_ids[0]).toBe('test-policy-2.5.3');
        });

        it('should return snapshot hash in correct format (sha256:hex)', async () => {
            const snapshotHash = 'sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef';
            const snapshot = createPolicySnapshot('policy-1', '1.0.0', snapshotHash);

            await policyService.cachePolicy(snapshot);
            await policyService.setCurrentPolicyVersion('policy-1', '1.0.0');

            const result = await policyService.getActivePolicyInfo(['policy-1']);

            // Note: getActivePolicyInfo always hashes the combined hash, even for single policies
            // So we verify the format and that it's a hash of the original hash
            expect(result.snapshot_hash).toMatch(/^sha256:[0-9a-f]{64}$/);

            // Verify it's a hash of the original snapshot hash
            const sortedHashes = [snapshotHash].sort();
            const combinedHash = sortedHashes.join('|');
            const expectedHash = crypto.createHash('sha256').update(combinedHash).digest('hex');
            expect(result.snapshot_hash).toBe(`sha256:${expectedHash}`);
        });
    });

    describe('Multiple Policies Case', () => {
        it('should return policy info for multiple existing policies', async () => {
            const snapshot1 = createPolicySnapshot('policy-1', '1.0.0', 'sha256:1111111111111111111111111111111111111111111111111111111111111111');
            const snapshot2 = createPolicySnapshot('policy-2', '2.0.0', 'sha256:2222222222222222222222222222222222222222222222222222222222222222');
            const snapshot3 = createPolicySnapshot('policy-3', '3.0.0', 'sha256:3333333333333333333333333333333333333333333333333333333333333333');

            await policyService.cachePolicy(snapshot1);
            await policyService.cachePolicy(snapshot2);
            await policyService.cachePolicy(snapshot3);
            await policyService.setCurrentPolicyVersion('policy-1', '1.0.0');
            await policyService.setCurrentPolicyVersion('policy-2', '2.0.0');
            await policyService.setCurrentPolicyVersion('policy-3', '3.0.0');

            const result = await policyService.getActivePolicyInfo(['policy-1', 'policy-2', 'policy-3']);

            expect(result.policy_version_ids).toHaveLength(3);
            expect(result.policy_version_ids).toContain('policy-1-1.0.0');
            expect(result.policy_version_ids).toContain('policy-2-2.0.0');
            expect(result.policy_version_ids).toContain('policy-3-3.0.0');
            expect(result.snapshot_hash).toMatch(/^sha256:[0-9a-f]{64}$/);
        });

        it('should combine snapshot hashes deterministically (sorted)', async () => {
            const hash1 = 'sha256:1111111111111111111111111111111111111111111111111111111111111111';
            const hash2 = 'sha256:2222222222222222222222222222222222222222222222222222222222222222';
            const hash3 = 'sha256:3333333333333333333333333333333333333333333333333333333333333333';

            const snapshot1 = createPolicySnapshot('policy-a', '1.0.0', hash1);
            const snapshot2 = createPolicySnapshot('policy-b', '2.0.0', hash2);
            const snapshot3 = createPolicySnapshot('policy-c', '3.0.0', hash3);

            await policyService.cachePolicy(snapshot1);
            await policyService.cachePolicy(snapshot2);
            await policyService.cachePolicy(snapshot3);
            await policyService.setCurrentPolicyVersion('policy-a', '1.0.0');
            await policyService.setCurrentPolicyVersion('policy-b', '2.0.0');
            await policyService.setCurrentPolicyVersion('policy-c', '3.0.0');

            // Call multiple times with same order
            const result1 = await policyService.getActivePolicyInfo(['policy-a', 'policy-b', 'policy-c']);
            const result2 = await policyService.getActivePolicyInfo(['policy-a', 'policy-b', 'policy-c']);

            // Should produce same hash (deterministic)
            expect(result1.snapshot_hash).toBe(result2.snapshot_hash);
        });

        it('should produce same hash regardless of policy order (sorted hashes)', async () => {
            const hash1 = 'sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';
            const hash2 = 'sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb';

            const snapshot1 = createPolicySnapshot('policy-x', '1.0.0', hash1);
            const snapshot2 = createPolicySnapshot('policy-y', '2.0.0', hash2);

            await policyService.cachePolicy(snapshot1);
            await policyService.cachePolicy(snapshot2);
            await policyService.setCurrentPolicyVersion('policy-x', '1.0.0');
            await policyService.setCurrentPolicyVersion('policy-y', '2.0.0');

            // Call with different order
            const result1 = await policyService.getActivePolicyInfo(['policy-x', 'policy-y']);
            const result2 = await policyService.getActivePolicyInfo(['policy-y', 'policy-x']);

            // Should produce same hash (hashes are sorted before combination)
            expect(result1.snapshot_hash).toBe(result2.snapshot_hash);
        });

        it('should correctly combine multiple snapshot hashes using SHA-256', async () => {
            const hash1 = 'sha256:1111111111111111111111111111111111111111111111111111111111111111';
            const hash2 = 'sha256:2222222222222222222222222222222222222222222222222222222222222222';

            const snapshot1 = createPolicySnapshot('policy-1', '1.0.0', hash1);
            const snapshot2 = createPolicySnapshot('policy-2', '2.0.0', hash2);

            await policyService.cachePolicy(snapshot1);
            await policyService.cachePolicy(snapshot2);
            await policyService.setCurrentPolicyVersion('policy-1', '1.0.0');
            await policyService.setCurrentPolicyVersion('policy-2', '2.0.0');

            const result = await policyService.getActivePolicyInfo(['policy-1', 'policy-2']);

            // Verify hash is SHA-256 of sorted hashes joined by |
            const sortedHashes = [hash1, hash2].sort();
            const combinedHash = sortedHashes.join('|');
            const expectedHash = crypto.createHash('sha256').update(combinedHash).digest('hex');

            expect(result.snapshot_hash).toBe(`sha256:${expectedHash}`);
        });
    });

    describe('Empty Policies Case', () => {
        it('should return empty arrays when no policies are found', async () => {
            const result = await policyService.getActivePolicyInfo(['nonexistent-policy']);

            expect(result.policy_version_ids).toEqual([]);
            expect(result.snapshot_hash).toBe('');
        });

        it('should return empty arrays when no current version is set', async () => {
            const snapshot = createPolicySnapshot('policy-1', '1.0.0');
            await policyService.cachePolicy(snapshot);
            // Don't set current version

            const result = await policyService.getActivePolicyInfo(['policy-1']);

            expect(result.policy_version_ids).toEqual([]);
            expect(result.snapshot_hash).toBe('');
        });

        it('should return empty arrays when policy exists but version does not match', async () => {
            const snapshot = createPolicySnapshot('policy-1', '1.0.0');
            await policyService.cachePolicy(snapshot);
            await policyService.setCurrentPolicyVersion('policy-1', '2.0.0'); // Different version

            const result = await policyService.getActivePolicyInfo(['policy-1']);

            expect(result.policy_version_ids).toEqual([]);
            expect(result.snapshot_hash).toBe('');
        });
    });

    describe('Non-existent Policies', () => {
        it('should handle non-existent policy IDs gracefully', async () => {
            const result = await policyService.getActivePolicyInfo(['nonexistent-1', 'nonexistent-2']);

            expect(result.policy_version_ids).toEqual([]);
            expect(result.snapshot_hash).toBe('');
        });

        it('should skip non-existent policies and return existing ones', async () => {
            const snapshot = createPolicySnapshot('existing-policy', '1.0.0');
            await policyService.cachePolicy(snapshot);
            await policyService.setCurrentPolicyVersion('existing-policy', '1.0.0');

            const result = await policyService.getActivePolicyInfo(['nonexistent-1', 'existing-policy', 'nonexistent-2']);

            expect(result.policy_version_ids).toHaveLength(1);
            expect(result.policy_version_ids[0]).toBe('existing-policy-1.0.0');
            expect(result.snapshot_hash).toMatch(/^sha256:[0-9a-f]{64}$/);
        });
    });

    describe('Default Parameter Handling', () => {
        it('should use default policy ID when no policyIds provided', async () => {
            const snapshot = createPolicySnapshot('default', '1.0.0');
            await policyService.cachePolicy(snapshot);
            await policyService.setCurrentPolicyVersion('default', '1.0.0');

            const result = await policyService.getActivePolicyInfo();

            expect(result.policy_version_ids).toHaveLength(1);
            expect(result.policy_version_ids[0]).toBe('default-1.0.0');
        });

        it('should return empty arrays when default policy does not exist', async () => {
            const result = await policyService.getActivePolicyInfo();

            expect(result.policy_version_ids).toEqual([]);
            expect(result.snapshot_hash).toBe('');
        });
    });

    describe('Edge Cases', () => {
        it('should handle empty policyIds array', async () => {
            const result = await policyService.getActivePolicyInfo([]);

            expect(result.policy_version_ids).toEqual([]);
            expect(result.snapshot_hash).toBe('');
        });

        it('should handle policy with empty snapshot hash', async () => {
            const snapshot = createPolicySnapshot('policy-1', '1.0.0', '');
            await policyService.cachePolicy(snapshot);
            await policyService.setCurrentPolicyVersion('policy-1', '1.0.0');

            const result = await policyService.getActivePolicyInfo(['policy-1']);

            expect(result.policy_version_ids).toHaveLength(1);
            expect(result.policy_version_ids[0]).toBe('policy-1-1.0.0');
            // Empty hash should still produce a hash (empty string sorted and hashed)
            expect(result.snapshot_hash).toMatch(/^sha256:[0-9a-f]{64}$/);
        });

        it('should handle policy with very long snapshot hash', async () => {
            const longHash = `sha256:${'a'.repeat(64)}`;
            const snapshot = createPolicySnapshot('policy-1', '1.0.0', longHash);
            await policyService.cachePolicy(snapshot);
            await policyService.setCurrentPolicyVersion('policy-1', '1.0.0');

            const result = await policyService.getActivePolicyInfo(['policy-1']);

            // Note: getActivePolicyInfo always hashes the combined hash, even for single policies
            // So we verify the format and that it's a hash of the original hash
            expect(result.snapshot_hash).toMatch(/^sha256:[0-9a-f]{64}$/);

            // Verify it's a hash of the original snapshot hash
            const sortedHashes = [longHash].sort();
            const combinedHash = sortedHashes.join('|');
            const expectedHash = crypto.createHash('sha256').update(combinedHash).digest('hex');
            expect(result.snapshot_hash).toBe(`sha256:${expectedHash}`);
        });

        it('should handle policy IDs with special characters (kebab-case)', async () => {
            const snapshot = createPolicySnapshot('policy-with-dashes', '1-0-0');
            await policyService.cachePolicy(snapshot);
            await policyService.setCurrentPolicyVersion('policy-with-dashes', '1-0-0');

            const result = await policyService.getActivePolicyInfo(['policy-with-dashes']);

            expect(result.policy_version_ids[0]).toBe('policy-with-dashes-1-0-0');
        });

        it('should handle multiple policies with same hash (should still combine)', async () => {
            const sameHash = 'sha256:1111111111111111111111111111111111111111111111111111111111111111';
            const snapshot1 = createPolicySnapshot('policy-1', '1.0.0', sameHash);
            const snapshot2 = createPolicySnapshot('policy-2', '2.0.0', sameHash);

            await policyService.cachePolicy(snapshot1);
            await policyService.cachePolicy(snapshot2);
            await policyService.setCurrentPolicyVersion('policy-1', '1.0.0');
            await policyService.setCurrentPolicyVersion('policy-2', '2.0.0');

            const result = await policyService.getActivePolicyInfo(['policy-1', 'policy-2']);

            expect(result.policy_version_ids).toHaveLength(2);
            // Same hash should be sorted and combined
            const sortedHashes = [sameHash, sameHash].sort();
            const combinedHash = sortedHashes.join('|');
            const expectedHash = crypto.createHash('sha256').update(combinedHash).digest('hex');
            expect(result.snapshot_hash).toBe(`sha256:${expectedHash}`);
        });
    });

    describe('Policy Version ID Format Validation', () => {
        it('should format policy version IDs correctly for all policies', async () => {
            const policies = [
                { id: 'policy-a', version: '1.0.0' },
                { id: 'policy-b', version: '2.5.3' },
                { id: 'policy-c', version: '10.20.30' }
            ];

            for (const policy of policies) {
                const snapshot = createPolicySnapshot(policy.id, policy.version);
                await policyService.cachePolicy(snapshot);
                await policyService.setCurrentPolicyVersion(policy.id, policy.version);
            }

            const result = await policyService.getActivePolicyInfo(policies.map(p => p.id));

            expect(result.policy_version_ids).toContain('policy-a-1.0.0');
            expect(result.policy_version_ids).toContain('policy-b-2.5.3');
            expect(result.policy_version_ids).toContain('policy-c-10.20.30');
        });
    });

    describe('Snapshot Hash Determinism', () => {
        it('should produce identical hash for identical policy sets', async () => {
            const hash1 = 'sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';
            const hash2 = 'sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb';

            const snapshot1 = createPolicySnapshot('policy-1', '1.0.0', hash1);
            const snapshot2 = createPolicySnapshot('policy-2', '2.0.0', hash2);

            await policyService.cachePolicy(snapshot1);
            await policyService.cachePolicy(snapshot2);
            await policyService.setCurrentPolicyVersion('policy-1', '1.0.0');
            await policyService.setCurrentPolicyVersion('policy-2', '2.0.0');

            const result1 = await policyService.getActivePolicyInfo(['policy-1', 'policy-2']);
            const result2 = await policyService.getActivePolicyInfo(['policy-1', 'policy-2']);
            const result3 = await policyService.getActivePolicyInfo(['policy-1', 'policy-2']);

            // All should be identical
            expect(result1.snapshot_hash).toBe(result2.snapshot_hash);
            expect(result2.snapshot_hash).toBe(result3.snapshot_hash);
        });

        it('should produce same hash regardless of input order (sorted internally)', async () => {
            const hash1 = 'sha256:1111111111111111111111111111111111111111111111111111111111111111';
            const hash2 = 'sha256:2222222222222222222222222222222222222222222222222222222222222222';
            const hash3 = 'sha256:3333333333333333333333333333333333333333333333333333333333333333';

            const snapshot1 = createPolicySnapshot('policy-1', '1.0.0', hash1);
            const snapshot2 = createPolicySnapshot('policy-2', '2.0.0', hash2);
            const snapshot3 = createPolicySnapshot('policy-3', '3.0.0', hash3);

            await policyService.cachePolicy(snapshot1);
            await policyService.cachePolicy(snapshot2);
            await policyService.cachePolicy(snapshot3);
            await policyService.setCurrentPolicyVersion('policy-1', '1.0.0');
            await policyService.setCurrentPolicyVersion('policy-2', '2.0.0');
            await policyService.setCurrentPolicyVersion('policy-3', '3.0.0');

            const result1 = await policyService.getActivePolicyInfo(['policy-1', 'policy-2', 'policy-3']);
            const result2 = await policyService.getActivePolicyInfo(['policy-3', 'policy-1', 'policy-2']);
            const result3 = await policyService.getActivePolicyInfo(['policy-2', 'policy-3', 'policy-1']);

            // All should produce same hash (hashes are sorted before combination)
            expect(result1.snapshot_hash).toBe(result2.snapshot_hash);
            expect(result2.snapshot_hash).toBe(result3.snapshot_hash);
        });
    });
});
