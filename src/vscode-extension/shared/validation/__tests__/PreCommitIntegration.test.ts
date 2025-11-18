import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as crypto from 'crypto';
import { PSCLArtifactWriter } from '../../storage/PSCLArtifactWriter';
import { PlanExecutionAgent } from '../../storage/PlanExecutionAgent';
import { PreCommitValidationPipeline } from '../PreCommitValidationPipeline';
import { StoragePathResolver } from '../../storage/StoragePathResolver';

const sanitizeRepoId = (repoId: string) =>
    repoId
        .toLowerCase()
        .replace(/[^a-z0-9-]/g, '-')
        .replace(/^-+|-+$/g, '') || 'default';

const writeFile = (root: string, relative: string, contents: string) => {
    const fullPath = path.join(root, relative);
    fs.mkdirSync(path.dirname(fullPath), { recursive: true });
    fs.writeFileSync(fullPath, contents, 'utf-8');
};

const readReceipt = async (zuRoot: string, repoId: string) => {
    const resolver = new StoragePathResolver(zuRoot);
    const now = new Date();
    const receiptDir = resolver.resolveReceiptPath(repoId, now.getUTCFullYear(), now.getUTCMonth() + 1);
    const receiptFile = path.join(receiptDir, 'receipts.jsonl');

    for (let attempt = 0; attempt < 5; attempt++) {
        if (fs.existsSync(receiptFile)) {
            const content = fs.readFileSync(receiptFile, 'utf-8').trim();
            const lines = content.split('\n');
            return JSON.parse(lines[lines.length - 1]);
        }
        await new Promise(resolve => setTimeout(resolve, 50));
    }
    throw new Error('DecisionReceipt not written in time');
};

describe('Pre-commit Integration', () => {
    let workspaceRoot: string;
    let zuRoot: string;
    let repoId: string;
    let privateKeyPem: string;
    const signingKeyId = 'integration-key';

    beforeAll(() => {
        const { privateKey } = crypto.generateKeyPairSync('ed25519');
        privateKeyPem = privateKey.export({ type: 'pkcs8', format: 'pem' }).toString();
    });

    beforeEach(() => {
        workspaceRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'zeroui-precommit-workspace-'));
        zuRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'zeroui-precommit-zu-'));
        repoId = sanitizeRepoId('test-repo');
        process.env.ZU_ROOT = zuRoot;
        // Seed policy cache
        const policyDir = path.join(zuRoot, 'ide', 'policy');
        fs.mkdirSync(path.join(policyDir, 'current'), { recursive: true });
        fs.mkdirSync(path.join(policyDir, 'cache'), { recursive: true });
        fs.writeFileSync(
            path.join(policyDir, 'current', `${repoId}.json`),
            JSON.stringify({
                policy_id: repoId,
                version: '1.0.0',
                timestamp_utc: new Date().toISOString()
            }),
            'utf-8'
        );
        fs.writeFileSync(
            path.join(policyDir, 'cache', `${repoId}-1.0.0.json`),
            JSON.stringify({
                policy_id: repoId,
                version: '1.0.0',
                policy_snapshot_id: 'SNAP.TEST.001',
                snapshot_hash: 'sha256:policyhash',
                policy_content: {},
                timestamp_utc: new Date().toISOString(),
                signature: 'sig-policy'
            }),
            'utf-8'
        );
        // Store default private key
        const keyPath = path.join(zuRoot, 'ide', 'trust', 'private', `${signingKeyId}.pem`);
        fs.mkdirSync(path.dirname(keyPath), { recursive: true });
        fs.writeFileSync(keyPath, privateKeyPem, 'utf-8');
    });

    afterEach(() => {
        delete process.env.ZU_ROOT;
        if (fs.existsSync(workspaceRoot)) {
            fs.rmSync(workspaceRoot, { recursive: true, force: true });
        }
        if (fs.existsSync(zuRoot)) {
            fs.rmSync(zuRoot, { recursive: true, force: true });
        }
    });

    const preparePlan = () => {
        const writer = new PSCLArtifactWriter({
            workspaceRoot,
            repoId,
            readerInstance: {
                getCurrentSnapshotId: () => ({
                    found: true,
                    policy_snapshot_id: 'SNAP.TEST.001'
                })
            } as any
        });
        (writer as any).listModifiedFiles = () => ['infra/config.json', 'src/example.ts'];
        return writer.write();
    };

    const runPipeline = async () => {
        const agent = new PlanExecutionAgent({
            workspaceRoot,
            repoId,
            zuRoot,
            signingKeyId,
            policyReaderOptions: {
                policyId: repoId
            },
            readerInstance: {
                getCurrentSnapshotId: () => ({
                    found: true,
                    policy_snapshot_id: 'SNAP.TEST.001'
                })
            } as any
        });
        await agent.execute();
        const pipeline = new PreCommitValidationPipeline({
            workspaceRoot,
            repoId,
            zuRoot,
            readerInstance: {
                getCurrentSnapshotId: () => ({
                    found: true,
                    policy_snapshot_id: 'SNAP.TEST.001'
                })
            } as any,
            policyReaderOptions: {
                policyId: repoId
            }
        });
        return pipeline.run();
    };

    test('produces PASS receipt when workspace matches plan', async () => {
        writeFile(workspaceRoot, 'src/example.ts', 'console.log("hello world");\n');
        writeFile(workspaceRoot, 'infra/config.json', '{"enabled":true}\n');

        preparePlan();
        const result = await runPipeline();
        expect(result.status).toBe('pass');
        const psclStage = result.stages.find(stage => stage.stage === 'pscl');
        expect(psclStage?.status).toBe('pass');
        expect(psclStage?.issues || []).toHaveLength(0);

        const receipt = await readReceipt(zuRoot, repoId);
        expect(receipt.decision.status).toBe('pass');
    });

    test('produces BLOCK receipt when workspace diverges from plan', async () => {
        writeFile(workspaceRoot, 'src/example.ts', 'console.log("hello world");\n');
        writeFile(workspaceRoot, 'infra/config.json', '{"enabled":true}\n');

        preparePlan();
        // Modify file after plan generation
        writeFile(workspaceRoot, 'infra/config.json', '{"enabled":false}\n');

        const result = await runPipeline();
        expect(result.status).toBe('hard_block');
        const psclStage = result.stages.find(stage => stage.stage === 'pscl');
        expect(psclStage?.status).toBe('hard_block');
        expect(psclStage?.issues && psclStage.issues.length).toBeGreaterThan(0);

        const receipt = await readReceipt(zuRoot, repoId);
        expect(receipt.decision.status).toBe('hard_block');
        expect(Array.isArray(receipt.inputs.mismatches)).toBe(true);
        expect(receipt.inputs.mismatches.length).toBeGreaterThan(0);
        const mismatch = receipt.inputs.mismatches[0];
        expect(mismatch.detail.toLowerCase()).toContain('mismatch');
    });
});
