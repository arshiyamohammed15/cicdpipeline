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
        // TODO: Load private key from secure storage (per Rule 218: No secrets on disk)
        // For now, this is a placeholder - actual implementation should use secrets manager
        if (privateKeyPath) {
            // Load private key from secure location
            // this.privateKey = this.loadPrivateKey(privateKeyPath);
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
     * Note: This is a placeholder implementation.
     * Actual implementation should use cryptographic signing with private key.
     * 
     * @param receipt Receipt to sign (without signature field)
     * @returns string Signature string
     */
    private signReceipt(receipt: any): string {
        // Create canonical JSON (sorted keys)
        // Note: Receipt is already without signature field (passed from generateDecisionReceipt/generateFeedbackReceipt)
        // Sort keys for consistent canonical form (matches ReceiptStorageService.toCanonicalJson())
        const sortedKeys = Object.keys(receipt).sort();
        const canonicalJson = JSON.stringify(receipt, sortedKeys);

        // TODO: Implement actual cryptographic signing
        // This should use the private key to sign the canonical JSON
        // For now, return a placeholder signature
        // In production, this should use Ed25519 or similar signing algorithm
        
        // Placeholder: Generate hash-based signature
        const hash = crypto.createHash('sha256').update(canonicalJson).digest('hex');
        return `sig-${hash}`;
    }
}

