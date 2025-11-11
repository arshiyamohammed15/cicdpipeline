import * as crypto from 'crypto';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { ReceiptStorageReader } from '../ReceiptStorageReader';
import { Ed25519ReceiptSigner } from '../ReceiptSigner';
import { DecisionReceipt } from '../../receipt-parser/ReceiptParser';

describe('ReceiptStorageReader signature verification integration', () => {
    const repoId = 'integration-repo';
    let zuRoot: string;
    let signer: Ed25519ReceiptSigner;
    let reader: ReceiptStorageReader;

    beforeEach(() => {
        zuRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'receipt-verifier-int-'));
        process.env.ZU_ROOT = zuRoot;
        const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
        const privatePem = privateKey.export({ format: 'pem', type: 'pkcs8' }).toString();
        const publicPem = publicKey.export({ format: 'pem', type: 'spki' }).toString();
        signer = new Ed25519ReceiptSigner({ privateKey: privatePem, keyId: 'integration-kid' });

        const trustDir = path.join(zuRoot, 'product', 'policy', 'trust', 'pubkeys');
        fs.mkdirSync(trustDir, { recursive: true });
        fs.writeFileSync(path.join(trustDir, 'integration-kid.pem'), publicPem);

        reader = new ReceiptStorageReader(zuRoot);
    });

    afterEach(() => {
        delete process.env.ZU_ROOT;
        if (fs.existsSync(zuRoot)) {
            fs.rmSync(zuRoot, { recursive: true, force: true });
        }
    });

    const buildBaseReceipt = (overrides: Partial<Omit<DecisionReceipt, 'signature'>> = {}): Omit<DecisionReceipt, 'signature'> => ({
        receipt_id: 'receipt-valid',
        gate_id: 'gate',
        policy_version_ids: ['policy.v1'],
        snapshot_hash: 'hash',
        timestamp_utc: '2025-01-01T00:00:00.000Z',
        timestamp_monotonic_ms: 1,
        evaluation_point: 'pre-commit',
        inputs: { path: 'src/app.ts' },
        decision: { status: 'pass', rationale: 'ok', badges: [] },
        evidence_handles: [],
        actor: { repo_id: repoId },
        degraded: false,
        ...overrides
    });

    it('returns only receipts with valid signatures', async () => {
        const base = buildBaseReceipt();
        const validReceipt: DecisionReceipt = {
            ...base,
            signature: signer.signReceipt(base as unknown as Record<string, unknown>)
        };

        const tamperedBase = {
            ...base,
            receipt_id: 'receipt-tampered',
            inputs: { path: 'src/app.ts', extra: true }
        };

        const tamperedSignature = signer.signReceipt(base as unknown as Record<string, unknown>);
        const tamperedReceipt: DecisionReceipt = {
            ...tamperedBase,
            signature: tamperedSignature
        };

        const receiptDir = path.join(zuRoot, 'ide', 'receipts', repoId, '2025', '01');
        fs.mkdirSync(receiptDir, { recursive: true });
        fs.writeFileSync(
            path.join(receiptDir, 'receipts.jsonl'),
            JSON.stringify(validReceipt) + '\n' + JSON.stringify(tamperedReceipt) + '\n'
        );

        const receipts = await reader.readReceipts(repoId, 2025, 1);
        expect(receipts.length).toBe(1);
        const [onlyReceipt] = receipts;
        expect('receipt_id' in onlyReceipt ? onlyReceipt.receipt_id : '').toBe('receipt-valid');
    });
});

