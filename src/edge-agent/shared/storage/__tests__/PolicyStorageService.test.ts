/**
 * PolicyStorageService Test Suite
 * 
 * Tests for policy storage operations
 * Validates policy caching, version management, and signature validation
 */

import { PolicyStorageService, PolicySnapshot } from '../PolicyStorageService';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

describe('PolicyStorageService', () => {
    const testZuRoot = os.tmpdir() + '/zeroui-test-' + Date.now();
    let policyService: PolicyStorageService;

    beforeEach(() => {
        if (!fs.existsSync(testZuRoot)) {
            fs.mkdirSync(testZuRoot, { recursive: true });
        }
        process.env.ZU_ROOT = testZuRoot;
        policyService = new PolicyStorageService(testZuRoot);
    });

    afterEach(() => {
        if (fs.existsSync(testZuRoot)) {
            fs.rmSync(testZuRoot, { recursive: true, force: true });
        }
    });

    describe('Cache Policy (Rule 221)', () => {
        const createPolicySnapshot = (policyId: string, version: string): PolicySnapshot => ({
            policy_id: policyId,
            version: version,
            snapshot_hash: `hash-${policyId}-${version}`,
            policy_content: { rule: 'test-rule', value: 'test-value' },
            timestamp_utc: new Date().toISOString(),
            signature: `sig-${policyId}-${version}`
        });

        it('should cache policy snapshot', async () => {
            const snapshot = createPolicySnapshot('policy-123', '1.0.0');
            const policyPath = await policyService.cachePolicy(snapshot);

            expect(fs.existsSync(policyPath)).toBe(true);
            expect(policyPath).toContain('policy-123-1.0.0.json');
        });

        it('should reject policy without signature (Rule 221)', async () => {
            const snapshot = createPolicySnapshot('policy-123', '1.0.0');
            snapshot.signature = '';

            await expect(
                policyService.cachePolicy(snapshot)
            ).rejects.toThrow('Policy must be signed before storage');
        });

        it('should reject policy with missing signature', async () => {
            const snapshot = createPolicySnapshot('policy-123', '1.0.0');
            delete (snapshot as any).signature;

            await expect(
                policyService.cachePolicy(snapshot)
            ).rejects.toThrow('Policy must be signed before storage');
        });

        it('should store policy with signature', async () => {
            const snapshot = createPolicySnapshot('policy-123', '1.0.0');
            const policyPath = await policyService.cachePolicy(snapshot);

            const content = fs.readFileSync(policyPath, 'utf-8');
            const stored = JSON.parse(content);

            expect(stored.signature).toBe(snapshot.signature);
            expect(stored.policy_id).toBe(snapshot.policy_id);
            expect(stored.version).toBe(snapshot.version);
        });

        it('should create directory structure if it does not exist', async () => {
            const snapshot = createPolicySnapshot('policy-123', '1.0.0');
            await policyService.cachePolicy(snapshot);

            const policyDir = path.join(testZuRoot, 'ide', 'policy', 'cache');
            expect(fs.existsSync(policyDir)).toBe(true);
        });
    });

    describe('Read Cached Policy', () => {
        it('should return null if policy does not exist', async () => {
            const policy = await policyService.readCachedPolicy('nonexistent', '1.0.0');
            expect(policy).toBeNull();
        });

        it('should read cached policy', async () => {
            const snapshot: PolicySnapshot = {
                policy_id: 'policy-123',
                version: '1.0.0',
                snapshot_hash: 'hash123',
                policy_content: { rule: 'test' },
                timestamp_utc: new Date().toISOString(),
                signature: 'sig-123'
            };

            await policyService.cachePolicy(snapshot);
            const read = await policyService.readCachedPolicy('policy-123', '1.0.0');

            expect(read).not.toBeNull();
            expect(read!.policy_id).toBe('policy-123');
            expect(read!.version).toBe('1.0.0');
            expect(read!.signature).toBe('sig-123');
        });

        it('should throw error if cached policy missing signature', async () => {
            const snapshot: PolicySnapshot = {
                policy_id: 'policy-123',
                version: '1.0.0',
                snapshot_hash: 'hash123',
                policy_content: { rule: 'test' },
                timestamp_utc: new Date().toISOString(),
                signature: 'sig-123'
            };

            await policyService.cachePolicy(snapshot);

            // Manually corrupt the file to remove signature
            const policyFile = path.join(testZuRoot, 'ide', 'policy', 'cache', 'policy-123-1.0.0.json');
            const content = JSON.parse(fs.readFileSync(policyFile, 'utf-8'));
            delete content.signature;
            fs.writeFileSync(policyFile, JSON.stringify(content));

            await expect(
                policyService.readCachedPolicy('policy-123', '1.0.0')
            ).rejects.toThrow('Cached policy missing signature');
        });
    });

    describe('Current Policy Version Management', () => {
        it('should return null if current version not set', async () => {
            const version = await policyService.readCurrentPolicyVersion('policy-123');
            expect(version).toBeNull();
        });

        it('should set and read current policy version', async () => {
            await policyService.setCurrentPolicyVersion('policy-123', '1.0.0');
            const version = await policyService.readCurrentPolicyVersion('policy-123');

            expect(version).toBe('1.0.0');
        });

        it('should update current policy version', async () => {
            await policyService.setCurrentPolicyVersion('policy-123', '1.0.0');
            await policyService.setCurrentPolicyVersion('policy-123', '2.0.0');

            const version = await policyService.readCurrentPolicyVersion('policy-123');
            expect(version).toBe('2.0.0');
        });

        it('should create directory structure for current pointer', async () => {
            await policyService.setCurrentPolicyVersion('policy-123', '1.0.0');

            const currentDir = path.join(testZuRoot, 'ide', 'policy', 'current');
            expect(fs.existsSync(currentDir)).toBe(true);
        });

        it('should store timestamp with current version', async () => {
            await policyService.setCurrentPolicyVersion('policy-123', '1.0.0');

            const currentFile = path.join(testZuRoot, 'ide', 'policy', 'current', 'policy-123.json');
            const content = JSON.parse(fs.readFileSync(currentFile, 'utf-8'));

            expect(content.policy_id).toBe('policy-123');
            expect(content.version).toBe('1.0.0');
            expect(content.timestamp_utc).toBeDefined();
        });
    });

    describe('Code/PII Detection (Rule 217)', () => {
        it('should reject policy containing function code', async () => {
            const snapshot: PolicySnapshot = {
                policy_id: 'policy-123',
                version: '1.0.0',
                snapshot_hash: 'hash',
                policy_content: { code: 'function test() {}' },
                timestamp_utc: new Date().toISOString(),
                signature: 'sig-123'
            };

            await expect(
                policyService.cachePolicy(snapshot)
            ).rejects.toThrow('contains executable code');
        });

        it('should reject policy containing class code', async () => {
            const snapshot: PolicySnapshot = {
                policy_id: 'policy-123',
                version: '1.0.0',
                snapshot_hash: 'hash',
                policy_content: { code: 'class Test {}' },
                timestamp_utc: new Date().toISOString(),
                signature: 'sig-123'
            };

            await expect(
                policyService.cachePolicy(snapshot)
            ).rejects.toThrow('contains executable code');
        });

        it('should accept policy without code', async () => {
            const snapshot: PolicySnapshot = {
                policy_id: 'policy-123',
                version: '1.0.0',
                snapshot_hash: 'hash',
                policy_content: { rule: 'safe-rule', value: 'safe-value' },
                timestamp_utc: new Date().toISOString(),
                signature: 'sig-123'
            };

            await expect(
                policyService.cachePolicy(snapshot)
            ).resolves.toBeTruthy();
        });
    });
});

