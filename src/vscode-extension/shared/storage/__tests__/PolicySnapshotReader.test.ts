import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { PolicySnapshotReader } from '../PolicySnapshotReader';

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

describe('PolicySnapshotReader (VS Code Extension)', () => {
    let tempRoot: string;
    const originalZuRoot = process.env.ZU_ROOT;
    const originalEnvSnapshot = process.env.POLICY_SNAPSHOT_ID;

    beforeEach(() => {
        tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'policy-reader-'));
        process.env.ZU_ROOT = tempRoot;
        delete process.env.POLICY_SNAPSHOT_ID;
    });

    afterEach(() => {
        if (originalZuRoot) {
            process.env.ZU_ROOT = originalZuRoot;
        } else {
            delete process.env.ZU_ROOT;
        }

        if (originalEnvSnapshot) {
            process.env.POLICY_SNAPSHOT_ID = originalEnvSnapshot;
        } else {
            delete process.env.POLICY_SNAPSHOT_ID;
        }

        if (fs.existsSync(tempRoot)) {
            fs.rmSync(tempRoot, { recursive: true, force: true });
        }
    });

    const writePointerFile = (policyId: string, contents: Record<string, unknown>) => {
        const pointerDir = path.join(tempRoot, 'ide', 'policy', 'current');
        fs.mkdirSync(pointerDir, { recursive: true });
        fs.writeFileSync(
            path.join(pointerDir, `${policyId}.json`),
            JSON.stringify(contents, null, 2),
            'utf-8'
        );
    };

    const writeCachedPolicy = (policyId: string, version: string, contents: Record<string, unknown>) => {
        const cacheDir = path.join(tempRoot, 'ide', 'policy', 'cache');
        fs.mkdirSync(cacheDir, { recursive: true });
        fs.writeFileSync(
            path.join(cacheDir, `${policyId}-${version}.json`),
            JSON.stringify(contents, null, 2),
            'utf-8'
        );
    };

    it('returns snapshot id from cached policy', () => {
        const policyId = 'default';
        const version = '2025.03.01';
        const snapshotId = 'SNAP.TEST.2025.03.01';

        writePointerFile(policyId, { policy_id: policyId, version });
        writeCachedPolicy(policyId, version, { snapshot_id: snapshotId });

        const reader = new PolicySnapshotReader();
        const result = reader.getCurrentSnapshotId();

        expect(result).toEqual({ found: true, policy_snapshot_id: snapshotId });
    });

    it('returns snapshot id from pointer when present', () => {
        const policyId = 'default';
        const snapshotId = 'SNAP.POINTER.0001';

        writePointerFile(policyId, { policy_id: policyId, version: '1.0.0', policy_snapshot_id: snapshotId });

        const reader = new PolicySnapshotReader();
        const result = reader.getCurrentSnapshotId();

        expect(result).toEqual({ found: true, policy_snapshot_id: snapshotId });
    });

    it('falls back to environment variable when cache missing', () => {
        const envId = 'SNAP.ENV.123';
        process.env.POLICY_SNAPSHOT_ID = envId;

        const reader = new PolicySnapshotReader({ zuRoot: tempRoot });
        const result = reader.getCurrentSnapshotId();

        expect(result).toEqual({ found: true, policy_snapshot_id: envId });
    });

    it('returns MISSING when no sources available', () => {
        const reader = new PolicySnapshotReader({ zuRoot: tempRoot });
        const result = reader.getCurrentSnapshotId();

        expect(result).toEqual({ found: false, policy_snapshot_id: 'MISSING' });
    });
});
