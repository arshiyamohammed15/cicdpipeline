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
        rationale: 'green',
        badges: ['pscl-plan', 'pass']
    },
    evidence_handles: [],
    actor: {
        repo_id: 'append-green'
    },
    degraded: false,
    signature: 'sig-ed25519:testkid:ZmFrZVNpZw=='
});

describe('receipts.append-only.green', () => {
    let tempRoot: string;
    let service: ReceiptStorageService;
    let repoId: string;
    let receiptsPath: string;

    beforeEach(async () => {
        tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'pscl-append-green-'));
        process.env.ZU_ROOT = tempRoot;
        service = new ReceiptStorageService(tempRoot);
        repoId = 'append-green';
        const firstReceipt = buildReceipt('receipt-1', '2025-03-15T12:00:00.000Z');
        receiptsPath = await service.storeDecisionReceipt(firstReceipt, repoId);
    });

    afterEach(() => {
        if (fs.existsSync(tempRoot)) {
            fs.rmSync(tempRoot, { recursive: true, force: true });
        }
        delete process.env.ZU_ROOT;
    });

    it('appends lines without altering the existing prefix', async () => {
        const prefixContent = fs.readFileSync(receiptsPath, 'utf-8');
        const prefixSize = prefixContent.length;
        const prefixHash = crypto.createHash('sha256').update(prefixContent).digest('hex');

        const secondReceipt = buildReceipt('receipt-2', '2025-03-15T12:05:00.000Z');
        await service.storeDecisionReceipt(secondReceipt, repoId);

        const finalContent = fs.readFileSync(receiptsPath, 'utf-8');
        expect(finalContent.length).toBeGreaterThan(prefixSize);
        expect(finalContent.slice(0, prefixSize)).toBe(prefixContent);
        expect(crypto.createHash('sha256').update(finalContent.slice(0, prefixSize)).digest('hex')).toBe(prefixHash);
        expect(finalContent.includes('receipt-2')).toBe(true);
    });
});
