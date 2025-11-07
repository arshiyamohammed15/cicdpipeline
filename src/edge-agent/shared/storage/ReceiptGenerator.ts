/**
 * Receipt Generator
 * 
 * Generates signed receipts for Edge Agent operations.
 * 
 * Compliance:
 * - Rule 219: JSONL receipts (signed, append-only)
 * - Rule 224: Receipts validation (signed)
 * 
 * @module storage
 */

import { DecisionReceipt, FeedbackReceipt } from '../receipt-types';
import * as crypto from 'crypto';

/**
 * Receipt generator for Edge Agent
 * Creates and signs receipts before storage
 */
export class ReceiptGenerator {
    private privateKey?: crypto.KeyObject;

    constructor(privateKeyPath?: string) {
        // Note: Private key loading from secure storage (per Rule 218: No secrets on disk)
        // In production, this should use secrets manager/HSM/KMS
        // For development/testing, private key can be provided via environment variable or secure config
        // This implementation uses deterministic signing for development (can be upgraded to cryptographic signing)
        if (privateKeyPath) {
            // Future: Load private key from secure location (secrets manager)
            // this.privateKey = await secretsManager.getPrivateKey(privateKeyPath);
        }
    }

    /**
     * Generate a decision receipt
     * 
     * @param gateId Gate identifier
     * @param policyVersionIds Policy version IDs
     * @param snapshotHash Snapshot hash
     * @param inputs Input data
     * @param decision Decision result
     * @param evidenceHandles Evidence handles
     * @param actor Actor information
     * @param degraded Whether operation was degraded
     * @returns DecisionReceipt Signed receipt
     */
    public generateDecisionReceipt(
        gateId: string,
        policyVersionIds: string[],
        snapshotHash: string,
        inputs: Record<string, any>,
        decision: {
            status: 'pass' | 'warn' | 'soft_block' | 'hard_block';
            rationale: string;
            badges: string[];
        },
        evidenceHandles: Array<{
            url: string;
            type: string;
            description: string;
            expires_at?: string;
        }>,
        actor: {
            repo_id: string;
            machine_fingerprint?: string;
        },
        degraded: boolean = false
    ): DecisionReceipt {
        const now = new Date();
        const receiptId = this.generateReceiptId();

        // Create receipt without signature
        const receipt: Omit<DecisionReceipt, 'signature'> = {
            receipt_id: receiptId,
            gate_id: gateId,
            policy_version_ids: policyVersionIds,
            snapshot_hash: snapshotHash,
            timestamp_utc: now.toISOString(),
            timestamp_monotonic_ms: Date.now(),
            inputs: inputs,
            decision: decision,
            evidence_handles: evidenceHandles,
            actor: actor,
            degraded: degraded
        };

        // Sign receipt
        const signature = this.signReceipt(receipt);

        return {
            ...receipt,
            signature: signature
        };
    }

    /**
     * Generate a feedback receipt
     * 
     * @param decisionReceiptId Decision receipt ID this feedback relates to
     * @param patternId Feedback pattern ID
     * @param choice User choice
     * @param tags Tags
     * @param actor Actor information
     * @returns FeedbackReceipt Signed receipt
     */
    public generateFeedbackReceipt(
        decisionReceiptId: string,
        patternId: 'FB-01' | 'FB-02' | 'FB-03' | 'FB-04',
        choice: 'worked' | 'partly' | 'didnt',
        tags: string[],
        actor: {
            repo_id: string;
            machine_fingerprint?: string;
        }
    ): FeedbackReceipt {
        const now = new Date();
        const feedbackId = this.generateReceiptId();

        // Create receipt without signature
        const receipt: Omit<FeedbackReceipt, 'signature'> = {
            feedback_id: feedbackId,
            decision_receipt_id: decisionReceiptId,
            pattern_id: patternId,
            choice: choice,
            tags: tags,
            actor: actor,
            timestamp_utc: now.toISOString()
        };

        // Sign receipt
        const signature = this.signReceipt(receipt);

        return {
            ...receipt,
            signature: signature
        };
    }

    /**
     * Generate unique receipt ID
     * 
     * Format: receipt-{timestamp}-{random}
     * Uses 8 bytes (16 hex chars) for randomness to minimize collision risk
     */
    private generateReceiptId(): string {
        const timestamp = Date.now();
        const random = crypto.randomBytes(8).toString('hex'); // 16 hex chars = 2^64 possibilities
        return `receipt-${timestamp}-${random}`;
    }

    /**
     * Sign receipt (Rule 224: receipts must be signed)
     * 
     * Implementation: Deterministic signing using SHA-256 hash of canonical JSON
     * 
     * Production Note: In production, this should use cryptographic signing (Ed25519) with private key
     * from secrets manager/HSM/KMS. The current implementation provides deterministic, verifiable
     * signatures suitable for development and testing. Upgrade path:
     * 1. Load private key from secrets manager (per Rule 218)
     * 2. Use Ed25519 or similar signing algorithm
     * 3. Include key ID (kid) in signature for verification
     * 
     * @param receipt Receipt to sign (without signature field)
     * @returns string Signature string (format: sig-{sha256_hash})
     */
    /**
     * Create canonical JSON with sorted keys recursively
     * This ensures deterministic output for signature generation
     */
    private toCanonicalJson(obj: any): string {
        if (obj === null || typeof obj !== 'object') {
            return JSON.stringify(obj);
        }

        if (Array.isArray(obj)) {
            return '[' + obj.map(item => this.toCanonicalJson(item)).join(',') + ']';
        }

        const sortedKeys = Object.keys(obj).sort();
        const sortedObj: any = {};
        for (const key of sortedKeys) {
            sortedObj[key] = obj[key];
        }

        const entries = sortedKeys.map(key => {
            const value = sortedObj[key];
            return JSON.stringify(key) + ':' + this.toCanonicalJson(value);
        });

        return '{' + entries.join(',') + '}';
    }

    private signReceipt(receipt: any): string {
        // Create canonical JSON (sorted keys for deterministic output)
        // Note: Receipt is already without signature field (passed from generateDecisionReceipt/generateFeedbackReceipt)
        // Sort keys recursively for consistent canonical form (matches ReceiptStorageService.toCanonicalJson())
        const canonicalJson = this.toCanonicalJson(receipt);

        // Generate deterministic signature using SHA-256 hash
        // This provides integrity verification and deterministic signing
        // In production, replace with cryptographic signing (Ed25519) using private key
        const hash = crypto.createHash('sha256').update(canonicalJson).digest('hex');
        return `sig-${hash}`;
    }
}

