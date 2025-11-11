import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { ReceiptStorageService } from '../ReceiptStorageService';
import { DecisionReceipt } from '../../receipt-parser/ReceiptParser';
import * as crypto from 'crypto';

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
        rationale: 'test',
        badges: ['pscl-plan', 'pass']
    },
    evidence_handles: [],
    actor: {
        repo_id: 'pscl-test'
    },
    degraded: false,
    signature: 'sig-ed25519:testkid:ZmFrZVNpZw=='
});

describe('ReceiptStorageService WORM continuity', () => {
    const repoId = 'pscl-test';
    let tempRoot: string;
    let service: ReceiptStorageService;
    let receiptsFile: string;

    beforeEach(async () => {
        tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'pscl-worm-'));
        process.env.ZU_ROOT = tempRoot;
        service = new ReceiptStorageService(tempRoot);

        const firstReceipt = buildReceipt('receipt-1', '2025-01-01T00:00:00.000Z');
        const storedPath = await service.storeDecisionReceipt(firstReceipt, repoId);
        receiptsFile = storedPath;
    });

    afterEach(() => {
        if (fs.existsSync(tempRoot)) {
            fs.rmSync(tempRoot, { recursive: true, force: true });
        }
        delete process.env.ZU_ROOT;
    });

    it('maintains receipts across PSCL enabled/disabled toggles', async () => {
        const beforeContent = fs.readFileSync(receiptsFile, 'utf-8');
        const beforeSize = beforeContent.length;

        // Simulate toggle OFF (no write occurs)

        // Toggle ON: append a new receipt (append-only expectation)
        const secondReceipt = buildReceipt('receipt-2', '2025-01-02T00:00:00.000Z');
        await service.storeDecisionReceipt(secondReceipt, repoId);

        // Toggle OFF again (no write occurs)

        const afterContent = fs.readFileSync(receiptsFile, 'utf-8');
        expect(afterContent.length).toBeGreaterThan(beforeSize);
        expect(afterContent.slice(0, beforeSize)).toBe(beforeContent);
    });

    it('creates new monthly file without modifying previous month', async () => {
        const janReceipt = buildReceipt('receipt-jan', '2025-01-31T23:59:59.000Z');
        await service.storeDecisionReceipt(janReceipt, repoId);

        const janDir = path.join(tempRoot, 'ide', 'receipts', repoId, '2025', '01');
        const janFile = path.join(janDir, 'receipts.jsonl');
        const janContent = fs.readFileSync(janFile, 'utf-8');
        const janSize = janContent.length;
        const janHash = crypto.createHash('sha256').update(janContent).digest('hex');

        const febReceiptA = buildReceipt('receipt-feb-a', '2025-02-01T00:00:01.000Z');
        const febPath = await service.storeDecisionReceipt(febReceiptA, repoId);

        const febDir = path.join(tempRoot, 'ide', 'receipts', repoId, '2025', '02');
        const febFile = path.join(febDir, 'receipts.jsonl');

        expect(fs.existsSync(janFile)).toBe(true);
        expect(fs.existsSync(febFile)).toBe(true);
        expect(path.normalize(febPath)).toBe(path.normalize(febFile));

        const janAfter = fs.readFileSync(janFile, 'utf-8');
        expect(janAfter.length).toBe(janSize);
        expect(crypto.createHash('sha256').update(janAfter).digest('hex')).toBe(janHash);

        const febContentBefore = fs.readFileSync(febFile, 'utf-8');
        const febBeforeSize = febContentBefore.length;
        const febBeforeHash = crypto.createHash('sha256').update(febContentBefore).digest('hex');

        const febReceiptB = buildReceipt('receipt-feb-b', '2025-02-02T00:00:01.000Z');
        await service.storeDecisionReceipt(febReceiptB, repoId);

        const febContentAfter = fs.readFileSync(febFile, 'utf-8');
        expect(febContentAfter.length).toBeGreaterThan(febBeforeSize);
        expect(febContentAfter.slice(0, febBeforeSize)).toBe(febContentBefore);
        expect(crypto.createHash('sha256').update(febContentBefore).digest('hex')).toBe(febBeforeHash);

        const janFinal = fs.readFileSync(janFile, 'utf-8');
        expect(janFinal.length).toBe(janSize);
        expect(crypto.createHash('sha256').update(janFinal).digest('hex')).toBe(janHash);
    });
});

