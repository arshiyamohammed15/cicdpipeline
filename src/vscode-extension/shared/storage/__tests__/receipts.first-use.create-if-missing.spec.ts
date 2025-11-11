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
        rationale: 'first-use',
        badges: ['pscl-plan', 'pass']
    },
    evidence_handles: [],
    actor: {
        repo_id: 'first-use'
    },
    degraded: false,
    signature: 'sig-ed25519:testkid:ZmFrZVNpZw=='
});

describe('receipts.first-use.create-if-missing', () => {
    let tempRoot: string;
    let service: ReceiptStorageService;
    let repoId: string;
    let receiptDir: string;
    let receiptsPath: string;

    beforeEach(() => {
        tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'pscl-first-use-'));
        process.env.ZU_ROOT = tempRoot;
        service = new ReceiptStorageService(tempRoot);
        repoId = 'first-use';
        receiptDir = path.join(tempRoot, 'ide', 'receipts', repoId, '2025', '04');
        receiptsPath = path.join(receiptDir, 'receipts.jsonl');
        if (fs.existsSync(receiptDir)) {
            fs.rmSync(receiptDir, { recursive: true, force: true });
        }
    });

    afterEach(() => {
        if (fs.existsSync(tempRoot)) {
            fs.rmSync(tempRoot, { recursive: true, force: true });
        }
        delete process.env.ZU_ROOT;
    });

    it('creates file on first write and appends subsequently', async () => {
        const firstReceipt = buildReceipt('receipt-1', '2025-04-01T00:00:00.000Z');
        await service.storeDecisionReceipt(firstReceipt, repoId);

        expect(fs.existsSync(receiptsPath)).toBe(true);
        const firstContent = fs.readFileSync(receiptsPath, 'utf-8');
        const firstSize = firstContent.length;
        const firstHash = crypto.createHash('sha256').update(firstContent).digest('hex');

        const secondReceipt = buildReceipt('receipt-2', '2025-04-01T00:10:00.000Z');
        await service.storeDecisionReceipt(secondReceipt, repoId);

        const finalContent = fs.readFileSync(receiptsPath, 'utf-8');
        expect(finalContent.length).toBeGreaterThan(firstSize);
        expect(finalContent.slice(0, firstSize)).toBe(firstContent);
        expect(crypto.createHash('sha256').update(finalContent.slice(0, firstSize)).digest('hex')).toBe(firstHash);
        expect(finalContent.includes('receipt-2')).toBe(true);
    });
});

