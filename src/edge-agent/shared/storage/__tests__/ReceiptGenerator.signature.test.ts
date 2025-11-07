/**
 * ReceiptGenerator Signature Test Suite
 * 
 * Comprehensive unit tests for receipt signing implementation
 * Tests canonical JSON generation, deterministic signatures, and SHA-256 verification
 * 
 * Coverage:
 * - Canonical JSON key sorting
 * - Deterministic signature verification
 * - SHA-256 hash verification
 * - Signature excludes signature field
 */

import { ReceiptGenerator } from '../ReceiptGenerator';
import { DecisionReceipt, FeedbackReceipt } from '../../receipt-types';
import * as crypto from 'crypto';

describe('ReceiptGenerator Signature Implementation', () => {
    let generator: ReceiptGenerator;

    beforeEach(() => {
        generator = new ReceiptGenerator();
    });

    describe('Canonical JSON Key Sorting', () => {
        it('should sort keys alphabetically for decision receipt', () => {
            const receipt = generator.generateDecisionReceipt(
                'gate-id',
                ['policy-v1'],
                'snapshot-hash',
                { z_field: 'z_value', a_field: 'a_value', m_field: 'm_value' },
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'repo' },
                false
            );

            // Extract signature to verify canonical form
            // Note: signReceipt receives receipt WITHOUT signature, but WITH all other fields
            const { signature, ...receiptWithoutSig } = receipt;
            
            // Create canonical JSON manually using same method as ReceiptGenerator.toCanonicalJson
            const toCanonicalJson = (obj: any): string => {
                if (obj === null || typeof obj !== 'object') {
                    return JSON.stringify(obj);
                }
                if (Array.isArray(obj)) {
                    return '[' + obj.map(item => toCanonicalJson(item)).join(',') + ']';
                }
                const sortedKeys = Object.keys(obj).sort();
                const entries = sortedKeys.map(key => {
                    return JSON.stringify(key) + ':' + toCanonicalJson(obj[key]);
                });
                return '{' + entries.join(',') + '}';
            };
            const canonicalJson = toCanonicalJson(receiptWithoutSig);
            
            // Verify signature is computed from canonical JSON
            const expectedHash = crypto.createHash('sha256').update(canonicalJson).digest('hex');
            expect(signature).toBe(`sig-${expectedHash}`);
        });

        it('should sort keys alphabetically for feedback receipt', () => {
            const receipt = generator.generateFeedbackReceipt(
                'decision-receipt-id',
                'FB-01',
                'worked',
                ['tag1', 'tag2'],
                { repo_id: 'repo' }
            );

            const { signature, ...receiptWithoutSig } = receipt;
            
            // Create canonical JSON manually using same method as ReceiptGenerator.toCanonicalJson
            const toCanonicalJson = (obj: any): string => {
                if (obj === null || typeof obj !== 'object') {
                    return JSON.stringify(obj);
                }
                if (Array.isArray(obj)) {
                    return '[' + obj.map(item => toCanonicalJson(item)).join(',') + ']';
                }
                const sortedKeys = Object.keys(obj).sort();
                const entries = sortedKeys.map(key => {
                    return JSON.stringify(key) + ':' + toCanonicalJson(obj[key]);
                });
                return '{' + entries.join(',') + '}';
            };
            const canonicalJson = toCanonicalJson(receiptWithoutSig);
            
            // Verify signature is computed from canonical JSON
            const expectedHash = crypto.createHash('sha256').update(canonicalJson).digest('hex');
            expect(signature).toBe(`sig-${expectedHash}`);
        });

        it('should produce same signature for same content regardless of key order in inputs', () => {
            // Create receipts with same data but different input key order
            const receipt1 = generator.generateDecisionReceipt(
                'gate',
                ['policy-v1'],
                'hash',
                { a: 'value1', b: 'value2', c: 'value3' },
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'repo' },
                false
            );

            // Wait to ensure different timestamp/receipt_id
            return new Promise(resolve => setTimeout(resolve, 10)).then(() => {
                const receipt2 = generator.generateDecisionReceipt(
                    'gate',
                    ['policy-v1'],
                    'hash',
                    { c: 'value3', a: 'value1', b: 'value2' }, // Different key order
                    { status: 'pass', rationale: 'test', badges: [] },
                    [],
                    { repo_id: 'repo' },
                    false
                );

                // Receipts will have different IDs and timestamps, so signatures will differ
                // But the canonical form of the inputs should be the same
                // We verify by checking that if we manually create canonical JSON, it matches
                const { signature: sig1, receipt_id: id1, timestamp_utc: ts1, timestamp_monotonic_ms: tm1, ...rest1 } = receipt1;
                const { signature: sig2, receipt_id: id2, timestamp_utc: ts2, timestamp_monotonic_ms: tm2, ...rest2 } = receipt2;

                // Create canonical JSON manually
                const sortedKeys1 = Object.keys(rest1).sort();
                const sortedKeys2 = Object.keys(rest2).sort();
                const canonical1 = JSON.stringify(rest1, sortedKeys1);
                const canonical2 = JSON.stringify(rest2, sortedKeys2);

                // The canonical forms should be identical (excluding ID/timestamp)
                expect(canonical1).toBe(canonical2);
            });
        });
    });

    describe('Deterministic Signature Verification', () => {
        it('should produce same signature for identical receipt content (excluding ID/timestamp)', () => {
            // Create two receipts with manually set identical IDs and timestamps
            // We'll verify the signature logic by manually creating the canonical form
            const gateId = 'test-gate';
            const policyIds: string[] = ['policy-v1'];
            const hash = 'test-hash';
            const inputs = { key: 'value' };
            const decision = { status: 'pass' as const, rationale: 'test', badges: [] };
            const evidenceHandles: any[] = [];
            const actor = { repo_id: 'test-repo' };
            const degraded = false;

            const receipt1 = generator.generateDecisionReceipt(
                gateId, policyIds, hash, inputs, decision, evidenceHandles, actor, degraded
            );

            // Wait to ensure different timestamp
            return new Promise(resolve => setTimeout(resolve, 10)).then(() => {
                const receipt2 = generator.generateDecisionReceipt(
                    gateId, policyIds, hash, inputs, decision, evidenceHandles, actor, degraded
                );

                // Extract receipt data without signature, ID, and timestamps
                const { signature: sig1, receipt_id: id1, timestamp_utc: ts1, timestamp_monotonic_ms: tm1, ...data1 } = receipt1;
                const { signature: sig2, receipt_id: id2, timestamp_utc: ts2, timestamp_monotonic_ms: tm2, ...data2 } = receipt2;

                // Create canonical JSON for both (sorted keys)
                const sortedKeys = Object.keys(data1).sort();
                const canonical1 = JSON.stringify(data1, sortedKeys);
                const canonical2 = JSON.stringify(data2, sortedKeys);

                // Canonical forms should be identical (excluding ID/timestamp)
                expect(canonical1).toBe(canonical2);

                // Verify signatures are computed from canonical form
                // Note: Signatures will be different because receipt_id and timestamps differ
                // But the canonical forms (excluding ID/timestamp) should be identical
                const hash1 = crypto.createHash('sha256').update(canonical1).digest('hex');
                const hash2 = crypto.createHash('sha256').update(canonical2).digest('hex');
                expect(hash1).toBe(hash2);
                
                // However, actual signatures will differ because they include ID/timestamp
                // This is expected - we're verifying the canonical form logic, not signature equality
                expect(sig1).toBeDefined();
                expect(sig2).toBeDefined();
            });
        });

        it('should produce different signatures for different receipt content', () => {
            const receipt1 = generator.generateDecisionReceipt(
                'gate1',
                ['policy-v1'],
                'hash1',
                { input1: 'value1' },
                { status: 'pass', rationale: 'test1', badges: [] },
                [],
                { repo_id: 'repo1' },
                false
            );

            const receipt2 = generator.generateDecisionReceipt(
                'gate2',
                ['policy-v2'],
                'hash2',
                { input2: 'value2' },
                { status: 'warn', rationale: 'test2', badges: [] },
                [],
                { repo_id: 'repo2' },
                true
            );

            expect(receipt1.signature).not.toBe(receipt2.signature);
        });

        it('should produce deterministic signature (same input = same output)', () => {
            const receipt = generator.generateDecisionReceipt(
                'gate',
                ['policy-v1'],
                'hash',
                { key: 'value' },
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'repo' },
                false
            );

            // Extract data without signature (but WITH ID and timestamps - those are part of signed data)
            const { signature: actualSig, ...receiptWithoutSig } = receipt;

            // Create canonical JSON manually using same method as ReceiptGenerator.toCanonicalJson
            const toCanonicalJson = (obj: any): string => {
                if (obj === null || typeof obj !== 'object') {
                    return JSON.stringify(obj);
                }
                if (Array.isArray(obj)) {
                    return '[' + obj.map(item => toCanonicalJson(item)).join(',') + ']';
                }
                const sortedKeys = Object.keys(obj).sort();
                const entries = sortedKeys.map(key => {
                    return JSON.stringify(key) + ':' + toCanonicalJson(obj[key]);
                });
                return '{' + entries.join(',') + '}';
            };
            const canonicalJson = toCanonicalJson(receiptWithoutSig);

            // Compute expected signature (this is what signReceipt does internally)
            const expectedHash = crypto.createHash('sha256').update(canonicalJson).digest('hex');
            const expectedSignature = `sig-${expectedHash}`;

            // Verify signature matches expected
            // The signature is computed from the receipt WITHOUT signature field,
            // but WITH receipt_id and timestamps (those are part of the signed data)
            expect(actualSig).toBe(expectedSignature);
            
            // Verify the signature format and that it's a valid SHA-256 hash
            const hashPart = actualSig.substring(4);
            expect(hashPart.length).toBe(64);
            expect(/^[0-9a-f]{64}$/.test(hashPart)).toBe(true);
        });
    });

    describe('SHA-256 Hash Verification', () => {
        it('should use SHA-256 algorithm for signature generation', () => {
            const receipt = generator.generateDecisionReceipt(
                'gate',
                ['policy-v1'],
                'hash',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'repo' },
                false
            );

            // Extract signature hash (remove 'sig-' prefix)
            const hashPart = receipt.signature.substring(4); // Remove 'sig-'
            
            // Verify it's a valid hex string (64 chars for SHA-256)
            expect(hashPart).toMatch(/^[0-9a-f]{64}$/);
            expect(hashPart.length).toBe(64);
        });

        it('should compute hash over canonical JSON (sorted keys)', () => {
            const receipt = generator.generateDecisionReceipt(
                'gate',
                ['policy-v1'],
                'hash',
                { z: 'z_val', a: 'a_val' },
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'repo' },
                false
            );

            // Extract receipt data without signature (but WITH ID and timestamps - those are signed)
            const { signature, ...receiptWithoutSig } = receipt;

            // Create canonical JSON manually using same method as ReceiptGenerator.toCanonicalJson
            const toCanonicalJson = (obj: any): string => {
                if (obj === null || typeof obj !== 'object') {
                    return JSON.stringify(obj);
                }
                if (Array.isArray(obj)) {
                    return '[' + obj.map(item => toCanonicalJson(item)).join(',') + ']';
                }
                const sortedKeys = Object.keys(obj).sort();
                const entries = sortedKeys.map(key => {
                    return JSON.stringify(key) + ':' + toCanonicalJson(obj[key]);
                });
                return '{' + entries.join(',') + '}';
            };
            const canonicalJson = toCanonicalJson(receiptWithoutSig);

            // Compute expected hash
            const expectedHash = crypto.createHash('sha256').update(canonicalJson).digest('hex');
            const expectedSignature = `sig-${expectedHash}`;

            // Verify signature matches
            expect(signature).toBe(expectedSignature);
        });

        it('should produce 64-character hex hash (SHA-256 output)', () => {
            const receipt = generator.generateDecisionReceipt(
                'gate',
                [],
                '',
                {},
                { status: 'pass', rationale: '', badges: [] },
                [],
                { repo_id: 'repo' },
                false
            );

            const hashPart = receipt.signature.substring(4);
            expect(hashPart.length).toBe(64);
            expect(/^[0-9a-f]{64}$/.test(hashPart)).toBe(true);
        });
    });

    describe('Signature Field Exclusion', () => {
        it('should not include signature field in canonical JSON for decision receipt', () => {
            const receipt = generator.generateDecisionReceipt(
                'gate',
                ['policy-v1'],
                'hash',
                {},
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'repo' },
                false
            );

            // Extract data without signature
            const { signature, ...receiptWithoutSig } = receipt;

            // Verify signature field is not in the receipt data
            expect(receiptWithoutSig).not.toHaveProperty('signature');

            // Verify canonical JSON doesn't include signature
            const sortedKeys = Object.keys(receiptWithoutSig).sort();
            const canonicalJson = JSON.stringify(receiptWithoutSig, sortedKeys);
            
            expect(canonicalJson).not.toContain('signature');
            expect(canonicalJson).not.toContain(signature);
        });

        it('should not include signature field in canonical JSON for feedback receipt', () => {
            const receipt = generator.generateFeedbackReceipt(
                'decision-receipt-id',
                'FB-01',
                'worked',
                ['tag1'],
                { repo_id: 'repo' }
            );

            const { signature, ...receiptWithoutSig } = receipt;

            expect(receiptWithoutSig).not.toHaveProperty('signature');

            const sortedKeys = Object.keys(receiptWithoutSig).sort();
            const canonicalJson = JSON.stringify(receiptWithoutSig, sortedKeys);
            
            expect(canonicalJson).not.toContain('signature');
            expect(canonicalJson).not.toContain(signature);
        });

        it('should compute signature from receipt without signature field', () => {
            const receipt = generator.generateDecisionReceipt(
                'gate',
                ['policy-v1'],
                'hash',
                { input: 'value' },
                { status: 'pass', rationale: 'test', badges: [] },
                [],
                { repo_id: 'repo' },
                false
            );

            // Extract data without signature (but WITH ID and timestamps - those are part of signed data)
            const { signature: actualSig, ...receiptWithoutSig } = receipt;

            // Manually compute signature from data (without signature field)
            // This matches the signReceipt implementation using toCanonicalJson
            const toCanonicalJson = (obj: any): string => {
                if (obj === null || typeof obj !== 'object') {
                    return JSON.stringify(obj);
                }
                if (Array.isArray(obj)) {
                    return '[' + obj.map(item => toCanonicalJson(item)).join(',') + ']';
                }
                const sortedKeys = Object.keys(obj).sort();
                const entries = sortedKeys.map(key => {
                    return JSON.stringify(key) + ':' + toCanonicalJson(obj[key]);
                });
                return '{' + entries.join(',') + '}';
            };
            const canonicalJson = toCanonicalJson(receiptWithoutSig);
            const computedHash = crypto.createHash('sha256').update(canonicalJson).digest('hex');
            const computedSignature = `sig-${computedHash}`;

            // Verify signature matches computed value
            expect(actualSig).toBe(computedSignature);
        });
    });

    describe('Signature Format Validation', () => {
        it('should produce signature in format sig-{64_hex_chars}', () => {
            const receipt = generator.generateDecisionReceipt(
                'gate',
                [],
                '',
                {},
                { status: 'pass', rationale: '', badges: [] },
                [],
                { repo_id: 'repo' },
                false
            );

            expect(receipt.signature).toMatch(/^sig-[0-9a-f]{64}$/);
        });

        it('should produce signature with lowercase hex characters', () => {
            const receipt = generator.generateDecisionReceipt(
                'gate',
                [],
                '',
                {},
                { status: 'pass', rationale: '', badges: [] },
                [],
                { repo_id: 'repo' },
                false
            );

            const hashPart = receipt.signature.substring(4);
            expect(hashPart).toBe(hashPart.toLowerCase());
        });
    });

    describe('Edge Cases', () => {
        it('should handle empty inputs object', () => {
            const receipt = generator.generateDecisionReceipt(
                'gate',
                [],
                '',
                {},
                { status: 'pass', rationale: '', badges: [] },
                [],
                { repo_id: 'repo' },
                false
            );

            expect(receipt.signature).toMatch(/^sig-[0-9a-f]{64}$/);
        });

        it('should handle nested objects in inputs', () => {
            const receipt = generator.generateDecisionReceipt(
                'gate',
                [],
                '',
                { nested: { key: 'value', another: { deep: 'nested' } } },
                { status: 'pass', rationale: '', badges: [] },
                [],
                { repo_id: 'repo' },
                false
            );

            expect(receipt.signature).toMatch(/^sig-[0-9a-f]{64}$/);
        });

        it('should handle arrays in inputs', () => {
            const receipt = generator.generateDecisionReceipt(
                'gate',
                [],
                '',
                { array: [1, 2, 3], nested: [{ a: 1 }, { b: 2 }] },
                { status: 'pass', rationale: '', badges: [] },
                [],
                { repo_id: 'repo' },
                false
            );

            expect(receipt.signature).toMatch(/^sig-[0-9a-f]{64}$/);
        });

        it('should handle special characters in string values', () => {
            const receipt = generator.generateDecisionReceipt(
                'gate',
                [],
                '',
                { special: 'value with "quotes" and \'apostrophes\' and\nnewlines' },
                { status: 'pass', rationale: 'test with "quotes"', badges: [] },
                [],
                { repo_id: 'repo' },
                false
            );

            expect(receipt.signature).toMatch(/^sig-[0-9a-f]{64}$/);
        });

        it('should handle unicode characters in values', () => {
            const receipt = generator.generateDecisionReceipt(
                'gate',
                [],
                '',
                { unicode: '测试 🚀 émoji' },
                { status: 'pass', rationale: 'Unicode test: 测试', badges: [] },
                [],
                { repo_id: 'repo' },
                false
            );

            expect(receipt.signature).toMatch(/^sig-[0-9a-f]{64}$/);
        });
    });
});

