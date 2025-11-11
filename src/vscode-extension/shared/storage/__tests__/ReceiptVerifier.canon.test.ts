import { computeSignableReceiptBuffer } from '../ReceiptVerifier';
import { Ed25519ReceiptSigner } from '../ReceiptSigner';
import * as crypto from 'crypto';

const baseReceipt = {
    receipt_id: 'receipt-123',
    gate_id: 'zeroui.pscl.precommit',
    policy_version_ids: ['POLICY.SAMPLE'],
    snapshot_hash: 'hash-abc',
    timestamp_utc: '2025-01-01T00:00:00.000Z',
    timestamp_monotonic_ms: 123456789,
    evaluation_point: 'pre-commit' as const,
    inputs: {
        evaluation_point: 'pre-commit',
        labels: {
            artifact_id: 'artifact-001'
        }
    },
    decision: {
        status: 'pass',
        rationale: 'ok',
        badges: ['pscl-plan', 'pass']
    },
    evidence_handles: [],
    actor: {
        repo_id: 'repo-xyz'
    },
    degraded: false
};

describe('ReceiptVerifier canonicalisation', () => {
    it('produces identical canonical buffers regardless of field ordering', () => {
        const receiptA = {
            ...baseReceipt,
            signature: 'sig-ed25519:test:AQ=='
        };

        const receiptB = {
            signature: 'sig-ed25519:test:AQ==',
            actor: baseReceipt.actor,
            decision: baseReceipt.decision,
            degraded: baseReceipt.degraded,
            evidence_handles: baseReceipt.evidence_handles,
            gate_id: baseReceipt.gate_id,
            evaluation_point: baseReceipt.evaluation_point,
            inputs: baseReceipt.inputs,
            policy_version_ids: baseReceipt.policy_version_ids,
            receipt_id: baseReceipt.receipt_id,
            snapshot_hash: baseReceipt.snapshot_hash,
            timestamp_monotonic_ms: baseReceipt.timestamp_monotonic_ms,
            timestamp_utc: baseReceipt.timestamp_utc
        };

        const bufferA = computeSignableReceiptBuffer(receiptA);
        const bufferB = computeSignableReceiptBuffer(receiptB);
        const canonicalString = bufferA.toString('utf8');

        expect(bufferA.equals(bufferB)).toBe(true);
        expect(canonicalString).toBe(
            '{"actor":{"repo_id":"repo-xyz"},"decision":{"badges":["pscl-plan","pass"],"rationale":"ok","status":"pass"},"degraded":false,"evaluation_point":"pre-commit","evidence_handles":[],"gate_id":"zeroui.pscl.precommit","inputs":{"evaluation_point":"pre-commit","labels":{"artifact_id":"artifact-001"}},"policy_version_ids":["POLICY.SAMPLE"],"receipt_id":"receipt-123","snapshot_hash":"hash-abc","timestamp_monotonic_ms":123456789,"timestamp_utc":"2025-01-01T00:00:00.000Z"}'
        );
    });

    it('matches signer canonicalisation', () => {
        const { privateKey, publicKey } = crypto.generateKeyPairSync('ed25519');
        const signer = new Ed25519ReceiptSigner({
            privateKey: privateKey.export({ type: 'pkcs8', format: 'pem' }),
            keyId: 'test'
        });

        const receipt = {
            ...baseReceipt
        };

        const signature = signer.signReceipt(receipt);
        const buffer = computeSignableReceiptBuffer({ ...receipt, signature });
        const canonical = buffer.toString('utf8');

        expect(signature.startsWith('sig-ed25519:test:')).toBe(true);
        expect(canonical).toContain('"receipt_id":"receipt-123"');
        expect(canonical).not.toContain('"signature"');

        const ok = crypto.verify(
            null,
            buffer,
            crypto.createPublicKey(publicKey.export({ type: 'spki', format: 'pem' })),
            Buffer.from(signature.split(':')[2], 'base64')
        );
        expect(ok).toBe(true);
    });

    it('produces stable buffers and omits signature field', () => {
        const receipt = {
            receipt_id: 'receipt-123',
            gate_id: 'gate',
            policy_version_ids: ['policy-1'],
            evaluation_point: 'pre-commit' as const,
            inputs: {
                evaluation_point: 'pre-commit',
                alpha: 1,
                beta: ['x', 'y']
            },
            decision: {
                status: 'pass',
                rationale: 'ok',
                badges: []
            },
            evidence_handles: [],
            actor: { repo_id: 'demo' },
            degraded: false,
            signature: 'sig-ed25519:test:ZmFrZVNpZw==' // excluded during computation
        };

        const buffer1 = computeSignableReceiptBuffer(receipt);
        const buffer2 = computeSignableReceiptBuffer(receipt);

        expect(buffer1.equals(buffer2)).toBe(true);
        const canonical = buffer1.toString('utf-8');
        expect(canonical).not.toContain('signature');
        expect(canonical).toContain('"alpha":1');
});
});
