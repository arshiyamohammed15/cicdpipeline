import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as crypto from 'crypto';
import { PlanVerifier } from '../PlanVerifier';
import { StoragePathResolver } from '../StoragePathResolver';

const sanitizeRepoId = (repoId: string) =>
    repoId
        .toLowerCase()
        .replace(/[^a-z0-9-]/g, '-')
        .replace(/^-+|-+$/g, '') || 'default';

describe('PlanVerifier', () => {
    const repoIdRaw = 'sample-repo';
    const repoId = sanitizeRepoId(repoIdRaw);
    let workspaceRoot: string;
    let zuRoot: string;
    let policyReaderStub: { getCurrentSnapshotId: jest.Mock };

    const createTempDir = (prefix: string) => fs.mkdtempSync(path.join(os.tmpdir(), prefix));

    const computeHash = (filePath: string) =>
        crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');

    const writeJson = (filePath: string, value: unknown) => {
        fs.mkdirSync(path.dirname(filePath), { recursive: true });
        fs.writeFileSync(filePath, JSON.stringify(value, null, 2));
    };

    const createPolicyCache = (resolver: StoragePathResolver, snapshotId: string) => {
        const policyDir = resolver.resolveIdePath('policy');
        fs.mkdirSync(path.join(policyDir, 'current'), { recursive: true });
        fs.mkdirSync(path.join(policyDir, 'cache'), { recursive: true });

        writeJson(path.join(policyDir, 'current', `${repoId}.json`), {
            policy_id: repoId,
            version: '1.0.0',
            timestamp_utc: new Date().toISOString()
        });

        writeJson(path.join(policyDir, 'cache', `${repoId}-1.0.0.json`), {
            policy_id: repoId,
            version: '1.0.0',
            snapshot_hash: 'sha256:dummy',
            policy_snapshot_id: snapshotId,
            policy_content: {},
            timestamp_utc: new Date().toISOString(),
            signature: 'sig'
        });
    };

    beforeEach(() => {
        workspaceRoot = createTempDir('plan-verifier-workspace-');
        zuRoot = createTempDir('plan-verifier-zu-');
        policyReaderStub = {
            getCurrentSnapshotId: jest.fn(() => ({
                found: true,
                policy_snapshot_id: 'SNAP.TEST.001'
            }))
        };
    });

    afterEach(() => {
        const cleanup = (dir: string | undefined) => {
            if (dir && fs.existsSync(dir)) {
                fs.rmSync(dir, { recursive: true, force: true });
            }
        };
        cleanup(workspaceRoot);
        cleanup(zuRoot);
    });

    test('returns ok=true when plan artifacts match workspace state', () => {
        const resolver = new StoragePathResolver(zuRoot);
        const psclDir = resolver.getPsclTempDir(repoId, { workspaceRoot });

        const filePath = path.join(workspaceRoot, 'src', 'fileA.txt');
        fs.mkdirSync(path.dirname(filePath), { recursive: true });
        fs.writeFileSync(filePath, 'hello world\n', 'utf-8');
        const fileHash = computeHash(filePath);

        writeJson(path.join(psclDir, 'FileEnvelope.json'), {
            policy_snapshot_id: 'SNAP.TEST.001',
            files: [{ path: 'src/fileA.txt', sha256: fileHash, mode: '0644' }],
            sbom_expected: true,
            immutable_registry_required: true
        });

        writeJson(path.join(psclDir, 'BuildPlan.json'), {
            policy_snapshot_id: 'SNAP.TEST.001',
            artifact_id: 'ai-build.20250101.deadbeef',
            expected_artifact_digest: '<TBD>',
            expected_sbom_digest: '<TBD>',
            build_inputs: ['src/**', 'infra/**'],
            cost_profile: 'light|ai-inference|batch',
            routing: 'serverless|gpu-queue',
            canary: {
                stages: [10, 50, 100]
            }
        });

        createPolicyCache(resolver, 'SNAP.TEST.001');

        const verifier = new PlanVerifier({
            repoId,
            workspaceRoot,
            zuRoot,
            readerInstance: policyReaderStub as any
        });

        const result = verifier.verify();

        expect(result.ok).toBe(true);
        expect(result.issues).toHaveLength(0);
    });

    test('reports hash mismatch when workspace file differs', () => {
        const resolver = new StoragePathResolver(zuRoot);
        const psclDir = resolver.getPsclTempDir(repoId, { workspaceRoot });

        const filePath = path.join(workspaceRoot, 'src', 'fileB.txt');
        fs.mkdirSync(path.dirname(filePath), { recursive: true });
        fs.writeFileSync(filePath, 'stale content\n', 'utf-8');
        const staleHash = computeHash(filePath);

        writeJson(path.join(psclDir, 'FileEnvelope.json'), {
            policy_snapshot_id: 'SNAP.TEST.001',
            files: [{ path: 'src/fileB.txt', sha256: staleHash, mode: '0644' }],
            sbom_expected: true,
            immutable_registry_required: true
        });

        writeJson(path.join(psclDir, 'BuildPlan.json'), {
            policy_snapshot_id: 'SNAP.TEST.001',
            artifact_id: 'ai-build.20250101.deadbeef',
            expected_artifact_digest: '<TBD>',
            expected_sbom_digest: '<TBD>',
            build_inputs: ['src/**', 'infra/**'],
            cost_profile: 'light|ai-inference|batch',
            routing: 'serverless|gpu-queue',
            canary: {
                stages: [10, 50, 100]
            }
        });

        createPolicyCache(resolver, 'SNAP.TEST.001');

        // Modify file after envelope was generated
        fs.writeFileSync(filePath, 'new content\n', 'utf-8');

        const verifier = new PlanVerifier({
            repoId,
            workspaceRoot,
            zuRoot,
            readerInstance: policyReaderStub as any
        });

        const result = verifier.verify();

        expect(result.ok).toBe(false);
        expect(result.issues.some(issue => issue.category === 'hash-mismatch')).toBe(true);
    });

    test('reports missing artifacts when plan files are absent', () => {
        const verifier = new PlanVerifier({
            repoId,
            workspaceRoot,
            zuRoot,
            readerInstance: policyReaderStub as any
        });

        const result = verifier.verify();

        expect(result.ok).toBe(false);
        expect(
            result.issues.filter(issue => issue.category === 'missing-artifact').length
        ).toBeGreaterThanOrEqual(1);
    });
});
