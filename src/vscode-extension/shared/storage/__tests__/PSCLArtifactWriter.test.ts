import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as crypto from 'crypto';

jest.mock('child_process', () => {
    const actual = jest.requireActual('child_process');
    return {
        ...actual,
        execSync: jest.fn()
    };
});

jest.mock('vscode', () => {
    const mockGetConfig = jest.fn(() => ({
        get: jest.fn()
    }));
    return {
        workspace: {
            getConfiguration: mockGetConfig
        }
    };
}, { virtual: true });

const { execSync } = require('child_process');
const { PSCLArtifactWriter } = require('../PSCLArtifactWriter');

describe('PSCLArtifactWriter', () => {
    const originalZuRoot = process.env.ZU_ROOT;
    let readerStub: { getCurrentSnapshotId: jest.Mock };
    let workspaceRoot: string;

    beforeEach(() => {
        workspaceRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'pscl-writer-'));
        process.env.ZU_ROOT = path.join(workspaceRoot, 'zu-root');
        fs.mkdirSync(process.env.ZU_ROOT, { recursive: true });
        jest.useFakeTimers().setSystemTime(new Date('2025-03-05T12:00:00Z'));
        readerStub = {
            getCurrentSnapshotId: jest.fn()
        };
        readerStub.getCurrentSnapshotId.mockReturnValue({
            found: true,
            policy_snapshot_id: 'SNAP.TEST.001'
        });
    });

    afterEach(() => {
        jest.useRealTimers();
        if (originalZuRoot) {
            process.env.ZU_ROOT = originalZuRoot;
        } else {
            delete process.env.ZU_ROOT;
        }
        if (fs.existsSync(workspaceRoot)) {
            fs.rmSync(workspaceRoot, { recursive: true, force: true });
        }
        (execSync as jest.Mock).mockReset();
    });

    const writeFile = (relative: string, contents: string) => {
        const fullPath = path.join(workspaceRoot, relative);
        fs.mkdirSync(path.dirname(fullPath), { recursive: true });
        fs.writeFileSync(fullPath, contents, 'utf-8');
    };

    const readJson = (filePath: string) =>
        JSON.parse(fs.readFileSync(filePath, 'utf-8'));

    it('writes FileEnvelope and BuildPlan with deterministic hashes', () => {
        writeFile('src/fileA.txt', 'hello world\n');
        writeFile('infra/config.json', '{"enabled":true}\n');

        (execSync as jest.Mock).mockReturnValue(
            [
                ' M src/fileA.txt',
                'A  infra/config.json',
                '?? docs/note.md'
            ].join('\n')
        );

        const writer = new PSCLArtifactWriter({
            repoId: 'sample-repo',
            workspaceRoot,
            readerInstance: readerStub as any
        });

        const result = writer.write();

        const expectedHashFileA = crypto
            .createHash('sha256')
            .update('hello world\n')
            .digest('hex');
        const expectedHashConfig = crypto
            .createHash('sha256')
            .update('{"enabled":true}\n')
            .digest('hex');

        expect(result.files).toEqual([
            { path: 'infra/config.json', sha256: expectedHashConfig, mode: '0644' },
            { path: 'src/fileA.txt', sha256: expectedHashFileA, mode: '0644' }
        ]);

        const envelopePath = result.envelopePath;
        const buildPlanPath = result.buildPlanPath;

        const envelope = readJson(envelopePath);
        expect(envelope).toEqual({
            policy_snapshot_id: 'SNAP.TEST.001',
            files: result.files,
            sbom_expected: true,
            immutable_registry_required: true
        });

        const buildPlan = readJson(buildPlanPath);
        expect(buildPlan.policy_snapshot_id).toBe('SNAP.TEST.001');
        expect(buildPlan.build_inputs).toEqual(['src/**', 'infra/**']);
        expect(buildPlan.cost_profile).toBe('light|ai-inference|batch');
        expect(buildPlan.routing).toBe('serverless|gpu-queue');
        expect(buildPlan.canary).toEqual({ stages: [10, 50, 100] });
        expect(buildPlan.expected_artifact_digest).toBe('<TBD>');
        expect(buildPlan.expected_sbom_digest).toBe('<TBD>');

        const digestSource = JSON.stringify({
            policy_snapshot_id: 'SNAP.TEST.001',
            files: result.files
        });
        const shortHash = crypto.createHash('sha256').update(digestSource).digest('hex').slice(0, 8);
        expect(buildPlan.artifact_id).toBe(`ai-build.20250305.${shortHash}`);
    });

    it('propagates MISSING snapshot id when reader cannot find value', () => {
        readerStub.getCurrentSnapshotId.mockReturnValue({
            found: false,
            policy_snapshot_id: 'MISSING'
        });

        writeFile('src/example.ts', 'console.log("test");\n');
        (execSync as jest.Mock).mockReturnValue(' M src/example.ts\n');

        const writer = new PSCLArtifactWriter({
            repoId: 'missing-policy',
            workspaceRoot,
            readerInstance: readerStub as any
        });

        const result = writer.write();

        const envelope = readJson(result.envelopePath);
        const buildPlan = readJson(result.buildPlanPath);

        expect(envelope.policy_snapshot_id).toBe('MISSING');
        expect(buildPlan.policy_snapshot_id).toBe('MISSING');
    });
});

