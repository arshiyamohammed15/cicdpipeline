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
import * as fs from 'fs';
import * as path from 'path';

export interface ReceiptGeneratorOptions {
    privateKey?: string | Buffer;
    privateKeyPath?: string;
    keyId?: string;
}

/**
 * Receipt generator for Edge Agent
 * Creates and signs receipts before storage
 */
export class ReceiptGenerator {
    private readonly privateKey: crypto.KeyObject;
    private readonly keyId: string;

    constructor(options: ReceiptGeneratorOptions = {}) {
        const material =
            options.privateKey ??
            (options.privateKeyPath ? this.loadKeyFromPath(options.privateKeyPath) : undefined) ??
            this.loadKeyFromEnv();

        if (!material) {
            throw new Error(
                'ReceiptGenerator requires an Ed25519 private key. Provide via options or set EDGE_AGENT_SIGNING_KEY or EDGE_AGENT_SIGNING_KEY_PATH.'
            );
        }

        this.privateKey = crypto.createPrivateKey(material);
        this.keyId =
            options.keyId ??
            this.inferKeyId(options.privateKeyPath) ??
            process.env.EDGE_AGENT_SIGNING_KEY_ID ??
            'edge-agent';
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
     * @param actor Actor information (may include type for TR-6.2)
     * @param degraded Whether operation was degraded
     * @param evaluationPoint Evaluation point (pre-commit, pre-merge, etc.)
     * @param context Optional context information (TR-1.2.3)
     * @param override Optional override information (TR-3.2.1)
     * @param dataCategory Optional data category classification (TR-4.4.1)
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
            type?: 'human' | 'ai' | 'automated'; // TR-6.2.1
        },
        degraded: boolean = false,
        evaluationPoint: DecisionReceipt['evaluation_point'] = 'pre-commit',
        context?: {
            surface?: 'ide' | 'pr' | 'ci';
            branch?: string;
            commit?: string;
            pr_id?: string;
        },
        override?: {
            reason: string;
            approver: string;
            timestamp: string;
            override_id?: string;
        },
        dataCategory?: 'public' | 'internal' | 'confidential' | 'restricted',
        timestampOverride?: { utc: string; monotonicMs?: number }
    ): DecisionReceipt {
        const now = timestampOverride?.utc ? new Date(timestampOverride.utc) : new Date();
        const receiptId = this.generateReceiptId();
        const monotonicMs =
            timestampOverride?.monotonicMs !== undefined ? timestampOverride.monotonicMs : Date.now();

        // Create receipt without signature
        const receipt: Omit<DecisionReceipt, 'signature'> = {
            receipt_id: receiptId,
            gate_id: gateId,
            policy_version_ids: policyVersionIds,
            snapshot_hash: snapshotHash,
            timestamp_utc: now.toISOString(),
            timestamp_monotonic_ms: monotonicMs,
            evaluation_point: evaluationPoint,
            inputs: inputs,
            decision: decision,
            evidence_handles: evidenceHandles,
            actor: actor,
            degraded: degraded
        };

        // Add optional fields if provided (TR-1.2.1 schema extensions)
        if (context !== undefined) {
            (receipt as any).context = context;
        }
        if (override !== undefined) {
            (receipt as any).override = override;
        }
        if (dataCategory !== undefined) {
            (receipt as any).data_category = dataCategory;
        }

        return {
            ...receipt,
            signature: this.signReceipt(receipt)
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

        return {
            ...receipt,
            signature: this.signReceipt(receipt)
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

    private signReceipt(receipt: Record<string, unknown>): string {
        const canonicalJson = this.toCanonicalJson(receipt);
        const buffer = Buffer.from(canonicalJson, 'utf-8');
        const signature = crypto.sign(null, buffer, this.privateKey);
        return `sig-ed25519:${this.keyId}:${signature.toString('base64')}`;
    }

    private loadKeyFromPath(filePath: string): string {
        return fs.readFileSync(filePath, 'utf-8');
    }

    private loadKeyFromEnv(): string | Buffer | undefined {
        const inline = process.env.EDGE_AGENT_SIGNING_KEY;
        if (inline && inline.trim().length > 0) {
            return inline;
        }

        const keyPath = process.env.EDGE_AGENT_SIGNING_KEY_PATH;
        if (keyPath) {
            try {
                return fs.readFileSync(keyPath, 'utf-8');
            } catch (error) {
                throw new Error(`Failed to read EDGE_AGENT_SIGNING_KEY_PATH (${keyPath}): ${(error as Error).message}`);
            }
        }

        return undefined;
    }

    private inferKeyId(privateKeyPath?: string): string | undefined {
        if (!privateKeyPath) {
            return undefined;
        }
        return path.parse(privateKeyPath).name;
    }
}
