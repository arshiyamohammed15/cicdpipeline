import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as crypto from 'crypto';
import { PlanExecutionAgent } from '../PlanExecutionAgent';
import { StoragePathResolver } from '../StoragePathResolver';
import { BuildSandbox } from '../BuildSandbox';

jest.mock('vscode', () => {
    const mockGetConfig = jest.fn(() => ({
        get: jest.fn()
    }));
    return {
        workspace: {
            getConfiguration: mockGetConfig,
            workspaceFolders: [
                {
                    name: 'workspace',
                    uri: { fsPath: '' }
                }
            ]
        }
    };
}, { virtual: true });

describe('PlanExecutionAgent', () => {
    let workspaceRoot: string;
    let zuRoot: string;
    const repoId = 'demo-repo';
    const policySnapshotId = 'SNAP.TEST.001';
    const signingKeyId = 'kid-123';

    const createTempDir = (prefix: string) => fs.mkdtempSync(path.join(os.tmpdir(), prefix));

    beforeEach(() => {
        workspaceRoot = createTempDir('plan-agent-workspace-');
        zuRoot = createTempDir('plan-agent-zu-');
        process.env.ZU_ROOT = zuRoot;
    });

    afterEach(() => {
        const cleanup = (dir: string | undefined) => {
            if (dir && fs.existsSync(dir)) {
                fs.rmSync(dir, { recursive: true, force: true });
            }
        };
        cleanup(workspaceRoot);
        cleanup(zuRoot);
        delete process.env.ZU_ROOT;
    });

    const writeJson = (filePath: string, value: unknown) => {
        fs.mkdirSync(path.dirname(filePath), { recursive: true });
        fs.writeFileSync(filePath, JSON.stringify(value, null, 2));
    };

    const setupPolicyCache = (snapshotHash: string, kid: string) => {
        const resolver = new StoragePathResolver(zuRoot);
        const policyDir = resolver.resolvePolicyPath('ide');
        fs.mkdirSync(path.join(policyDir, 'current'), { recursive: true });
        fs.mkdirSync(path.join(policyDir, 'cache'), { recursive: true });

        writeJson(path.join(policyDir, 'current', 'default.json'), {
            policy_id: 'default',
            version: '1.0.0',
            timestamp_utc: new Date().toISOString()
        });

        writeJson(path.join(policyDir, 'cache', `default-1.0.0.json`), {
            policy_id: 'default',
            version: '1.0.0',
            policy_snapshot_id: policySnapshotId,
            snapshot_hash: snapshotHash,
            kid,
            policy_content: {},
            timestamp_utc: new Date().toISOString(),
            signature: 'sig-placeholder'
        });
    };

    const setupPlanArtifacts = (
        expectedArtifact: string,
        expectedSbom: string,
        inputs: string[],
        overrides?: Record<string, unknown>
    ) => {
        const resolver = new StoragePathResolver(zuRoot);
        const psclDir = resolver.getPsclTempDir(repoId, { workspaceRoot });

        writeJson(path.join(psclDir, 'FileEnvelope.json'), {
            policy_snapshot_id: policySnapshotId,
            files: inputs.map(input => ({
                path: input,
                sha256: crypto.createHash('sha256').update(fs.readFileSync(path.join(workspaceRoot, input))).digest('hex'),
                mode: '0644'
            })),
            sbom_expected: true,
            immutable_registry_required: true
        });

        const buildPlan: Record<string, unknown> = {
            policy_snapshot_id: policySnapshotId,
            artifact_id: 'ai-build.20250101.deadbeef',
            expected_artifact_digest: expectedArtifact,
            expected_sbom_digest: expectedSbom,
            build_inputs: ['src/**', 'infra/**'],
            cost_profile: 'light|ai-inference|batch',
            routing: 'serverless|gpu-queue',
            canary: {
                stages: [10, 50, 100]
            }
        };

        if (overrides) {
            Object.assign(buildPlan, overrides);
        }

        writeJson(path.join(psclDir, 'BuildPlan.json'), buildPlan);
    };

    const readReceipts = (): any[] => {
        const resolver = new StoragePathResolver(zuRoot);
        const now = new Date();
        const receiptDir = resolver.resolveReceiptPath(repoId, now.getUTCFullYear(), now.getUTCMonth() + 1);
        const receiptFile = path.join(receiptDir, 'receipts.jsonl');
        const content = fs.readFileSync(receiptFile, 'utf-8');
        return content.trim().split('\n').map(line => JSON.parse(line));
    };

    test('produces PASS receipt when all checks succeed', async () => {
        fs.mkdirSync(path.join(workspaceRoot, 'src'), { recursive: true });
        fs.mkdirSync(path.join(workspaceRoot, 'infra'), { recursive: true });
        fs.writeFileSync(path.join(workspaceRoot, 'src', 'main.ts'), 'console.log("hello");\n', 'utf-8');
        fs.writeFileSync(path.join(workspaceRoot, 'infra', 'config.json'), '{"flag":true}\n', 'utf-8');

        const sandbox = new BuildSandbox({
            workspaceRoot,
            buildInputs: ['src/**', 'infra/**']
        });
        const sandboxResult = sandbox.run();

        setupPolicyCache('sha256:policyhash', signingKeyId);
        setupPlanArtifacts(
            sandboxResult.artifact_digest,
            sandboxResult.sbom_digest,
            ['infra/config.json', 'src/main.ts'],
            {
                model_cache_hints: {
                    warm_start: true
                }
            }
        );

        const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
        const privateKeyPath = path.join(zuRoot, 'ide', 'trust', 'private', `${signingKeyId}.pem`);
        fs.mkdirSync(path.dirname(privateKeyPath), { recursive: true });
        fs.writeFileSync(privateKeyPath, privateKey.export({ type: 'pkcs8', format: 'pem' }));

        const agent = new PlanExecutionAgent({
            repoId,
            workspaceRoot,
            zuRoot,
            signingKeyId
        });

        const result = await agent.execute();

        expect(result.receiptStatus).toBe('pass');
        const receipts = readReceipts();
        expect(receipts).toHaveLength(1);
        const latest = receipts[0];
        expect(latest.signature.startsWith('sig-ed25519:')).toBe(true);
        expect(latest.decision.status).toBe('pass');
        expect(latest.evaluation_point).toBe('pre-commit');
        expect(latest.inputs.evaluation_point).toBe('pre-commit');
        expect(latest.inputs.artifact_digest).toBe(sandboxResult.artifact_digest);
        expect(latest.inputs.sbom_digest).toBe(sandboxResult.sbom_digest);
        expect(latest.inputs.labels).toBeDefined();
        expect(latest.inputs.labels.cost_profile).toBe('light|ai-inference|batch');
        expect(latest.inputs.labels.routing).toBe('serverless|gpu-queue');
        expect(latest.inputs.labels.model_cache_hints).toEqual({ warm_start: true });
        expect(latest.inputs.artifact_id).toBe('ai-build.20250101.deadbeef');
        expect(latest.inputs.mismatches).toBeUndefined();
        const signatureParts = latest.signature.split(':');
        expect(signatureParts[0]).toBe('sig-ed25519');
        expect(signatureParts[1]).toBe(signingKeyId);
        expect(() => Buffer.from(signatureParts[2], 'base64')).not.toThrow();
    });

    test('produces FAIL receipt when digests mismatch', async () => {
        fs.mkdirSync(path.join(workspaceRoot, 'src'), { recursive: true });
        fs.mkdirSync(path.join(workspaceRoot, 'infra'), { recursive: true });
        fs.writeFileSync(path.join(workspaceRoot, 'src', 'main.ts'), 'console.log("hello");\n', 'utf-8');
        fs.writeFileSync(path.join(workspaceRoot, 'infra', 'config.json'), '{"flag":true}\n', 'utf-8');

        const sandbox = new BuildSandbox({
            workspaceRoot,
            buildInputs: ['src/**', 'infra/**']
        });
        const sandboxResult = sandbox.run();

        setupPolicyCache('sha256:policyhash', signingKeyId);
        setupPlanArtifacts('sha256:expected-different', sandboxResult.sbom_digest, [
            'infra/config.json',
            'src/main.ts'
        ]);

        const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
        const privateKeyPath = path.join(zuRoot, 'ide', 'trust', 'private', `${signingKeyId}.pem`);
        fs.mkdirSync(path.dirname(privateKeyPath), { recursive: true });
        fs.writeFileSync(privateKeyPath, privateKey.export({ type: 'pkcs8', format: 'pem' }));

        const agent = new PlanExecutionAgent({
            repoId,
            workspaceRoot,
            zuRoot,
            signingKeyId
        });

        await agent.execute(); // first receipt (pass expected but fails due to mismatch)

        const receipts = readReceipts();
        expect(receipts).toHaveLength(1);
        const latest = receipts[0];
        expect(latest.signature.startsWith('sig-ed25519:')).toBe(true);
        expect(latest.evaluation_point).toBe('pre-commit');
        expect(latest.decision.status).toBe('hard_block');
        expect(latest.decision.rationale).toContain('Artifact digest mismatch');
        expect(latest.inputs.labels).toBeDefined();
        expect(latest.inputs.labels.cost_profile).toBe('light|ai-inference|batch');
        expect(latest.inputs.labels.routing).toBe('serverless|gpu-queue');
        expect(latest.inputs.labels.model_cache_hints).toBeUndefined();
        expect(latest.inputs.artifact_id).toBe('ai-build.20250101.deadbeef');
        expect(Array.isArray(latest.inputs.mismatches)).toBe(true);
        expect(latest.inputs.mismatches).toHaveLength(1);
        expect(latest.inputs.mismatches[0].detail).toContain('Artifact digest mismatch');
        const signatureParts = latest.signature.split(':');
        expect(signatureParts[0]).toBe('sig-ed25519');
        expect(signatureParts[1]).toBe(signingKeyId);
        expect(() => Buffer.from(signatureParts[2], 'base64')).not.toThrow();
    });
});

