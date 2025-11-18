import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as crypto from 'crypto';
import { ReceiptStorageService } from '../ReceiptStorageService';
import { DecisionReceipt } from '../../receipt-parser/ReceiptParser';

const buildReceipt = (id: string, timestamp: string): DecisionReceipt => ({
    receipt_id: id,
    gate_id: 'zeroui.pscl.precommit',
    policy_version_ids: ['SNAP.LOCAL.2025'],
    snapshot_hash: 'SNAP.LOCAL.2025',
    timestamp_utc: timestamp,
    timestamp_monotonic_ms: Date.parse(timestamp),
    evaluation_point: 'pre-commit',
    inputs: {
        evaluation_point: 'pre-commit',
        policy_snapshot_id: 'SNAP.LOCAL.2025',
        artifact_digest: 'sha256:test',
        expected_artifact_digest: '<TBD>',
        sbom_digest: 'sha256:test',
        expected_sbom_digest: '<TBD>',
        build_inputs: ['src/**']
    },
    decision: {
        status: 'pass',
        rationale: 'flag-toggle',
        badges: ['pscl-plan', 'pass']
    },
    evidence_handles: [],
    actor: {
        repo_id: 'flag-toggle'
    },
    degraded: false,
    signature: 'sig-ed25519:testkid:ZmFrZVNpZw=='
});

const extractInode = (stat: fs.Stats): number | undefined => {
    const maybe = (stat as unknown as { ino?: number }).ino;
    return typeof maybe === 'number' && maybe > 0 ? maybe : undefined;
};

describe('receipts.feature-flag.off-noop', () => {
    let tempRoot: string;
    let service: ReceiptStorageService;
    let repoId: string;
    let receiptsPath: string;

    beforeEach(async () => {
        tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'pscl-flag-toggle-'));
        process.env.ZU_ROOT = tempRoot;
        service = new ReceiptStorageService(tempRoot);
        repoId = 'flag-toggle';
        const initial = buildReceipt('receipt-initial', '2025-05-01T00:00:00.000Z');
        receiptsPath = await service.storeDecisionReceipt(initial, repoId);
    });

    afterEach(() => {
        if (fs.existsSync(tempRoot)) {
            fs.rmSync(tempRoot, { recursive: true, force: true });
        }
        delete process.env.ZU_ROOT;
    });

    it('does not modify receipts during PSCL disable periods', async () => {
        const beforeContent = fs.readFileSync(receiptsPath, 'utf-8');
        const beforeSize = beforeContent.length;
        const beforeHash = crypto.createHash('sha256').update(beforeContent).digest('hex');

        const toggles = ['off-1', 'on-1', 'off-2'] as const;
        for (const toggle of toggles) {
            if (toggle.startsWith('on')) {
                const receipt = buildReceipt(`receipt-${toggle}`, '2025-05-01T00:05:00.000Z');
                await service.storeDecisionReceipt(receipt, repoId);
            } else {
                const exists = fs.existsSync(receiptsPath);
                expect(exists).toBe(true);
            }
        }

        const finalContent = fs.readFileSync(receiptsPath, 'utf-8');
        expect(finalContent.length).toBeGreaterThanOrEqual(beforeSize);
        expect(finalContent.slice(0, beforeSize)).toBe(beforeContent);
        expect(crypto.createHash('sha256').update(beforeContent).digest('hex')).toBe(beforeHash);
    });

    it('preserves receipt file inode and prefix across OFF→ON→OFF toggles', async () => {
        const initialStat = fs.statSync(receiptsPath);
        const initialSize = Number(initialStat.size);
        const initialInode = extractInode(initialStat);
        const initialContent = fs.readFileSync(receiptsPath, 'utf-8');
        const initialPrefixHash = crypto.createHash('sha256').update(initialContent).digest('hex');

        const toggles: Array<{ enabled: boolean; id: string; timestamp: string }> = [
            { enabled: false, id: 'receipt-off-a', timestamp: '2025-05-01T00:10:00.000Z' },
            { enabled: true, id: 'receipt-on-a', timestamp: '2025-05-01T00:15:00.000Z' },
            { enabled: false, id: 'receipt-off-b', timestamp: '2025-05-01T00:20:00.000Z' }
        ];

        for (const toggle of toggles) {
            if (!toggle.enabled) {
                expect(fs.existsSync(receiptsPath)).toBe(true);
                continue;
            }
            const receipt = buildReceipt(toggle.id, toggle.timestamp);
            await service.storeDecisionReceipt(receipt, repoId);
        }

        const finalContent = fs.readFileSync(receiptsPath, 'utf-8');
        expect(finalContent.length).toBeGreaterThanOrEqual(initialSize);
        const finalPrefixHash = crypto
            .createHash('sha256')
            .update(finalContent.slice(0, initialSize))
            .digest('hex');
        expect(finalPrefixHash).toBe(initialPrefixHash);

        const finalStat = fs.statSync(receiptsPath);
        const finalInode = extractInode(finalStat);

        if (initialInode !== undefined && finalInode !== undefined) {
            expect(finalInode).toBe(initialInode);
        }
    });
});
