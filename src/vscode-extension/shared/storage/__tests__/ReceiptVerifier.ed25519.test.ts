import * as crypto from 'crypto';
import { computeSignableReceiptBuffer, verifyReceiptSignature } from '../ReceiptVerifier';
import { Ed25519ReceiptSigner } from '../ReceiptSigner';

const buildBaseReceipt = () => ({
    receipt_id: 'receipt-abc',
    gate_id: 'zeroui.pscl.precommit',
    policy_version_ids: ['POLICY.LOCAL'],
    snapshot_hash: 'hash-local',
    timestamp_utc: '2025-01-02T10:00:00.000Z',
    timestamp_monotonic_ms: Date.now(),
    evaluation_point: 'pre-commit' as const,
    inputs: {
        evaluation_point: 'pre-commit'
    },
    decision: {
        status: 'pass' as const,
        rationale: 'all green',
        badges: ['pscl-plan', 'pass']
    },
    evidence_handles: [] as Array<Record<string, unknown>>,
    actor: {
        repo_id: 'repo-test'
    },
    degraded: false
});

describe('ReceiptVerifier Ed25519 interoperability', () => {
    it('verifies signer output and rejects tampered receipts', () => {
        const { privateKey, publicKey } = crypto.generateKeyPairSync('ed25519');
        const signer = new Ed25519ReceiptSigner({
            privateKey: privateKey.export({ type: 'pkcs8', format: 'pem' }),
            keyId: 'local-test'
        });

        const unsigned = buildBaseReceipt();
        const signature = signer.signReceipt(unsigned as unknown as Record<string, unknown>);
        const signedReceipt = { ...unsigned, signature };

        const publicPem = publicKey.export({ type: 'spki', format: 'pem' }).toString();
        expect(verifyReceiptSignature(signedReceipt, publicPem)).toBe(true);

        const tampered = {
            ...signedReceipt,
            decision: {
                ...signedReceipt.decision,
                status: 'warn' as const
            }
        };

        expect(verifyReceiptSignature(tampered, publicPem)).toBe(false);

        const buffer = computeSignableReceiptBuffer(signedReceipt);
        expect(Buffer.isBuffer(buffer)).toBe(true);
        expect(buffer.length).toBeGreaterThan(0);
    });
});
