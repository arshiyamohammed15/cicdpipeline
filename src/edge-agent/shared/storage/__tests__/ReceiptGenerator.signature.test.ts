import { ReceiptGenerator } from '../ReceiptGenerator';
import * as crypto from 'crypto';

const toCanonicalJson = (obj: unknown): string => {
    if (obj === null || typeof obj !== 'object') {
        return JSON.stringify(obj);
    }
    if (Array.isArray(obj)) {
        return '[' + obj.map(item => toCanonicalJson(item)).join(',') + ']';
    }
    const entries = Object.keys(obj as Record<string, unknown>)
        .sort()
        .map(key => `${JSON.stringify(key)}:${toCanonicalJson((obj as Record<string, unknown>)[key])}`);
    return '{' + entries.join(',') + '}';
};

describe('ReceiptGenerator Signature Implementation', () => {
    const keyId = 'unit-test-kid';
    let privatePem: string;
    let publicKey: crypto.KeyObject;
    let generator: ReceiptGenerator;

    beforeAll(() => {
        const { publicKey: pub, privateKey } = crypto.generateKeyPairSync('ed25519');
        privatePem = privateKey.export({ format: 'pem', type: 'pkcs8' }).toString();
        publicKey = pub;
    });

    beforeEach(() => {
        generator = new ReceiptGenerator({ privateKey: privatePem, keyId });
    });

    const expectValidSignature = (payload: unknown, signature: string) => {
        const record = payload as Record<string, unknown>;
        const parts = signature.split(':');
        expect(parts).toHaveLength(3);
        expect(parts[0]).toBe('sig-ed25519');
        expect(parts[1]).toBe(keyId);
        const signatureBuffer = Buffer.from(parts[2], 'base64');
        const canonical = toCanonicalJson(record);
        const ok = crypto.verify(null, Buffer.from(canonical, 'utf-8'), publicKey, signatureBuffer);
        expect(ok).toBe(true);
    };

    test('signs decision receipts with Ed25519', () => {
        const receipt = generator.generateDecisionReceipt(
            'gate-id',
            ['policy-v1'],
            'snapshot-hash',
            { z_field: 'z_value', a_field: 'a_value' },
            { status: 'pass', rationale: 'ok', badges: ['pscl'] },
            [],
            { repo_id: 'repo' },
            false
        );

        const { signature, ...payload } = receipt;
        expect(signature.startsWith(`sig-ed25519:${keyId}:`)).toBe(true);
        expectValidSignature(payload, signature);
    });

    test('signs feedback receipts with Ed25519', () => {
        const decision = generator.generateDecisionReceipt(
            'gate',
            [],
            'hash',
            {},
            { status: 'pass', rationale: 'ok', badges: [] },
            [],
            { repo_id: 'repo' },
            false
        );

        const feedback = generator.generateFeedbackReceipt(
            decision.receipt_id,
            'FB-01',
            'worked',
            ['tag1'],
            { repo_id: 'repo' }
        );

        const { signature, ...payload } = feedback;
        expect(signature.startsWith(`sig-ed25519:${keyId}:`)).toBe(true);
        expectValidSignature(payload, signature);
    });

    test('canonical JSON sorts keys recursively', () => {
        const receipt = generator.generateDecisionReceipt(
            'gate',
            ['policy-v1'],
            'hash',
            { z_field: 'z', a_field: { nested: ['c', 'b', 'a'] }, m_field: 'm' },
            { status: 'pass', rationale: 'ok', badges: [] },
            [],
            { repo_id: 'repo' },
            false
        );

        const { signature, ...payload } = receipt;
        expectValidSignature(payload, signature);

        const canonical = toCanonicalJson(payload);
        expect(canonical.indexOf('"a_field"')).toBeLessThan(canonical.indexOf('"m_field"'));
        expect(canonical.indexOf('"m_field"')).toBeLessThan(canonical.indexOf('"z_field"'));
    });

    test('tampering invalidates signatures', () => {
        const receipt = generator.generateDecisionReceipt(
            'gate',
            ['policy'],
            'hash',
            { key: 'value' },
            { status: 'pass', rationale: 'ok', badges: [] },
            [],
            { repo_id: 'repo' },
            false
        );

        const { signature, ...payload } = receipt;
        expectValidSignature(payload, signature);

        const tampered = { ...payload, decision: { ...payload.decision, status: 'hard_block' } };
        const parts = signature.split(':');
        const signatureBuffer = Buffer.from(parts[2], 'base64');
        const canonical = toCanonicalJson(tampered);
        const ok = crypto.verify(null, Buffer.from(canonical, 'utf-8'), publicKey, signatureBuffer);
        expect(ok).toBe(false);
    });

    test('different receipts yield different signatures', () => {
        const receiptA = generator.generateDecisionReceipt(
            'gate-a',
            ['policy-a'],
            'hash-a',
            { input: 'a' },
            { status: 'pass', rationale: 'ok', badges: [] },
            [],
            { repo_id: 'repo' },
            false
        );
        const receiptB = generator.generateDecisionReceipt(
            'gate-b',
            ['policy-b'],
            'hash-b',
            { input: 'b' },
            { status: 'warn', rationale: 'warn', badges: [] },
            [],
            { repo_id: 'repo' },
            true
        );

        const { signature: sigA, ...payloadA } = receiptA;
        const { signature: sigB, ...payloadB } = receiptB;

        expect(sigA).not.toBe(sigB);
        expectValidSignature(payloadA, sigA);
        expectValidSignature(payloadB, sigB);
    });

    test('signature encodes key id and base64 payload', () => {
        const receipt = generator.generateDecisionReceipt(
            'gate',
            [],
            'hash',
            {},
            { status: 'pass', rationale: 'ok', badges: [] },
            [],
            { repo_id: 'repo' },
            false
        );

        const parts = receipt.signature.split(':');
        expect(parts).toHaveLength(3);
        expect(parts[0]).toBe('sig-ed25519');
        expect(parts[1]).toBe(keyId);
        expect(() => Buffer.from(parts[2], 'base64')).not.toThrow();
    });

    test('signature excludes signature field from canonical payload', () => {
        const receipt = generator.generateDecisionReceipt(
            'gate',
            ['policy-v1'],
            'hash',
            {},
            { status: 'pass', rationale: 'ok', badges: [] },
            [],
            { repo_id: 'repo' },
            false
        );

        const { signature, ...payload } = receipt;
        const canonical = toCanonicalJson(payload);
        expect(canonical).not.toContain('signature');
        expectValidSignature(payload, signature);
    });
});
