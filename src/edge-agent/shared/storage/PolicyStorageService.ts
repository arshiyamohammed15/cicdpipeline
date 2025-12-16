/**
 * Policy Storage Service
 *
 * Handles policy storage according to 4-Plane Storage Architecture rules.
 *
 * Compliance:
 * - Rule 221: Policy Signatures (all policies must be signed)
 * - Rule 223: Path resolution via ZU_ROOT
 * - Rule 217: No code/PII in stores
 *
 * Storage locations:
 * - IDE Plane: ide/policy/ (cache, signed snapshots)
 * - Product Plane: product/policy/registry/ (authoritative releases, templates, revocations)
 *
 * @module storage
 */

import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';
import { StoragePathResolver } from './StoragePathResolver';

/**
 * Policy snapshot interface
 */
export interface PolicySnapshot {
    policy_id: string;
    version: string;
    snapshot_hash: string;
    policy_content: Record<string, any>;
    timestamp_utc: string;
    signature: string;
    metadata?: {
        author?: string;
        description?: string;
        tags?: string[];
    };
}

/**
 * Policy storage service for Edge Agent
 * Stores policies in IDE Plane (cache) and Product Plane (registry)
 */
export class PolicyStorageService {
    private pathResolver: StoragePathResolver;
    private verificationKey?: crypto.KeyObject;

    constructor(zuRoot?: string, options: { verificationKey?: string | Buffer | crypto.KeyObject } = {}) {
        this.pathResolver = new StoragePathResolver(zuRoot);
        if (options.verificationKey) {
            this.verificationKey = this.toPublicKey(options.verificationKey);
        }
    }

    /**
     * Cache policy snapshot in IDE Plane
     * Pattern: ide/policy/
     *
     * @param snapshot Policy snapshot to cache
     * @returns Promise<string> Path where policy was cached
     */
    public async cachePolicy(snapshot: PolicySnapshot): Promise<string> {
        // Validate signature (Rule 221: all policies must be signed and verifiable)
        this.verifyPolicySignature(snapshot);

        // Resolve IDE Plane policy path
        const policyDir = this.pathResolver.resolvePolicyPath('ide', 'cache/');
        // Use forward slash to maintain consistency
        const policyFile = path.posix.join(
            policyDir,
            `${this.safePolicyId(snapshot.policy_id)}-${this.safePolicyVersion(snapshot.version)}.json`
        );

        // Ensure directory exists
        await this.ensureDirectoryExists(policyDir);

        // Validate no code/PII in policy (Rule 217)
        this.validateNoCodeOrPII(snapshot);

        // Write policy as signed JSON
        const policyJson = JSON.stringify(snapshot, null, 2);
        fs.writeFileSync(policyFile, policyJson, 'utf-8');

        return policyFile;
    }

    /**
     * Read cached policy from IDE Plane
     *
     * @param policyId Policy identifier
     * @param version Policy version
     * @returns Promise<PolicySnapshot | null> Policy snapshot or null if not found
     */
    public async readCachedPolicy(policyId: string, version: string): Promise<PolicySnapshot | null> {
        const policyDir = this.pathResolver.resolvePolicyPath('ide', 'cache/');
        // Use forward slash to maintain consistency
        const policyFile = path.posix.join(
            policyDir,
            `${this.safePolicyId(policyId)}-${this.safePolicyVersion(version)}.json`
        );

        if (!fs.existsSync(policyFile)) {
            return null;
        }

        const content = fs.readFileSync(policyFile, 'utf-8');
        const snapshot = JSON.parse(content) as PolicySnapshot;

        // Validate signature exists and is verifiable
        this.verifyPolicySignature(snapshot);

        return snapshot;
    }

    /**
     * Read current policy pointer
     * Pattern: ide/policy/current
     *
     * @param policyId Policy identifier
     * @returns Promise<string | null> Current version or null if not set
     */
    public async readCurrentPolicyVersion(policyId: string): Promise<string | null> {
        const policyDir = this.pathResolver.resolvePolicyPath('ide', '');
        // Use forward slash to maintain consistency
        const currentFile = `${policyDir}/current/${policyId}.json`;

        if (!fs.existsSync(currentFile)) {
            return null;
        }

        const content = fs.readFileSync(currentFile, 'utf-8');
        const current = JSON.parse(content);

        return current.version || null;
    }

    /**
     * Set current policy pointer
     *
     * @param policyId Policy identifier
     * @param version Policy version to set as current
     */
    public async setCurrentPolicyVersion(policyId: string, version: string): Promise<void> {
        const policyDir = this.pathResolver.resolvePolicyPath('ide', 'current/');
        // Use forward slash to maintain consistency
        const currentFile = `${policyDir}/${policyId}.json`;

        await this.ensureDirectoryExists(policyDir);

        const current = {
            policy_id: policyId,
            version: version,
            timestamp_utc: new Date().toISOString()
        };

        fs.writeFileSync(currentFile, JSON.stringify(current, null, 2), 'utf-8');
    }

    /**
     * Get active policy information for receipt generation
     * Returns policy version IDs and snapshot hash from current cached policies
     *
     * @param policyIds List of policy identifiers to get active versions for
     * @returns Promise<{policy_version_ids: string[], snapshot_hash: string}>
     */
    public async getActivePolicyInfo(policyIds: string[] = ['default']): Promise<{
        policy_version_ids: string[];
        snapshot_hash: string;
    }> {
        const policyVersionIds: string[] = [];
        const snapshotHashes: string[] = [];

        for (const policyId of policyIds) {
            const version = await this.readCurrentPolicyVersion(policyId);
            if (version) {
                const snapshot = await this.readCachedPolicy(policyId, version);
                if (snapshot) {
                    // Format: policy_id-version
                    policyVersionIds.push(`${policyId}-${version}`);
                    snapshotHashes.push(snapshot.snapshot_hash);
                }
            }
        }

        // If no policies found, return defaults
        if (policyVersionIds.length === 0) {
            return {
                policy_version_ids: [],
                snapshot_hash: ''
            };
        }

        // Combine snapshot hashes into a single hash (deterministic)
        // In production, this might use a Merkle tree or similar structure
        const combinedHash = snapshotHashes.sort().join('|');
        const finalHash = crypto.createHash('sha256')
            .update(combinedHash)
            .digest('hex');

        return {
            policy_version_ids: policyVersionIds,
            snapshot_hash: `sha256:${finalHash}`
        };
    }

    /**
     * Validate no code/PII in policy (Rule 217)
     */
    private validateNoCodeOrPII(snapshot: PolicySnapshot): void {
        const policyStr = JSON.stringify(snapshot);

        // Check for code patterns
        const codePatterns = [
            /\bfunction\s+\w+\s*\(/,  // function name()
            /\bfunction\s*\(/,        // function()
            /\bclass\s+\w+/,
            /\bimport\s+.*from/,
            /\bexport\s+/,
            /<script>/i,
            /<style>/i
        ];

        for (const pattern of codePatterns) {
            if (pattern.test(policyStr)) {
                throw new Error('Policy contains executable code (violates Rule 217: No Code/PII in Stores)');
            }
        }

        // Check for PII patterns (email, SSN, credit card, etc.)
        const piiPatterns = [
            /\b\d{3}-\d{2}-\d{4}\b/, // SSN
            /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/, // Credit card
            /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/ // Email
        ];

        for (const pattern of piiPatterns) {
            if (pattern.test(policyStr)) {
                throw new Error('Policy contains PII (violates Rule 217: No Code/PII in Stores)');
            }
        }
    }

    /**
     * Ensure directory exists
     */
    private async ensureDirectoryExists(dirPath: string): Promise<void> {
        return new Promise((resolve, reject) => {
            fs.mkdir(dirPath, { recursive: true }, (err) => {
                if (err) {
                    reject(err);
                } else {
                    resolve();
                }
            });
        });
    }

    /**
     * Ensure policy_id is safe (kebab-case) and not path-traversal capable.
     */
    private safePolicyId(policyId: string): string {
        const normalized = policyId?.trim();
        if (!normalized) {
            throw new Error('Policy ID is required');
        }
        const kebabCasePattern = /^[a-z0-9-]+$/;
        if (!kebabCasePattern.test(normalized)) {
            throw new Error(`Invalid policy_id: ${policyId}. Must be kebab-case [a-z0-9-] only`);
        }
        if (normalized.includes('..') || normalized.includes('/') || normalized.includes('\\')) {
            throw new Error('Invalid policy_id: must not contain path separators or traversal');
        }
        return normalized;
    }

    /**
     * Ensure policy version is safe for filenames.
     * Accepts digits, dots, and hyphens (e.g., 1.0.0, 2.5.3-beta).
     */
    private safePolicyVersion(version: string): string {
        const normalized = version?.trim();
        if (!normalized) {
            throw new Error('Policy version is required');
        }
        const versionPattern = /^[a-z0-9][a-z0-9.-]*$/;
        if (!versionPattern.test(normalized)) {
            throw new Error(`Invalid policy version: ${version}. Allowed characters: [a-z0-9.-]`);
        }
        if (normalized.includes('..') || normalized.includes('/') || normalized.includes('\\')) {
            throw new Error('Invalid policy version: must not contain path separators or traversal');
        }
        return normalized;
    }

    /**
     * Verify policy signature using Ed25519 (sig-ed25519:{kid}:{base64}) over canonical JSON (without signature).
     * Throws if missing or invalid.
     */
    private verifyPolicySignature(snapshot: PolicySnapshot): void {
        if (!snapshot.signature || snapshot.signature.length === 0) {
            throw new Error('Policy must be signed before storage (Rule 221)');
        }

        const verifier = this.getVerificationKey();
        const { signature, ...payload } = snapshot as any;
        const canonical = this.toCanonicalJson(payload);

        const parts = signature.split(':');
        if (parts.length !== 3 || parts[0] !== 'sig-ed25519') {
            throw new Error('Policy signature format must be sig-ed25519:{kid}:{base64}');
        }
        const sigBuffer = Buffer.from(parts[2], 'base64');

        const ok = crypto.verify(null, Buffer.from(canonical, 'utf-8'), verifier, sigBuffer);
        if (!ok) {
            throw new Error('Policy signature verification failed');
        }
    }

    private getVerificationKey(): crypto.KeyObject {
        if (this.verificationKey) {
            return this.verificationKey;
        }

        const fromEnv =
            process.env.EDGE_AGENT_POLICY_PUBLIC_KEY ??
            process.env.EDGE_AGENT_SIGNING_PUBLIC_KEY ??
            process.env.EDGE_AGENT_SIGNING_KEY;
        const fromEnvPath = process.env.EDGE_AGENT_SIGNING_KEY_PATH;

        if (fromEnv) {
            this.verificationKey = this.toPublicKey(fromEnv);
            return this.verificationKey;
        }

        if (fromEnvPath) {
            const pem = fs.readFileSync(fromEnvPath, 'utf-8');
            this.verificationKey = this.toPublicKey(pem);
            return this.verificationKey;
        }

        throw new Error('Policy verification key not configured (set EDGE_AGENT_POLICY_PUBLIC_KEY or EDGE_AGENT_SIGNING_PUBLIC_KEY)');
    }

    private toPublicKey(material: string | Buffer | crypto.KeyObject): crypto.KeyObject {
        if (material instanceof crypto.KeyObject) {
            return material.type === 'public' ? material : crypto.createPublicKey(material);
        }
        const keyObject = crypto.createPublicKey(material);
        return keyObject;
    }

    /**
     * Deep canonical JSON (sorted keys, arrays preserved) to match signing.
     */
    private toCanonicalJson(obj: any): string {
        if (obj === null || typeof obj !== 'object') {
            return JSON.stringify(obj);
        }

        if (Array.isArray(obj)) {
            return '[' + obj.map(item => this.toCanonicalJson(item)).join(',') + ']';
        }

        const sortedKeys = Object.keys(obj).sort();
        const entries = sortedKeys.map(key => {
            const value = obj[key];
            return JSON.stringify(key) + ':' + this.toCanonicalJson(value);
        });

        return '{' + entries.join(',') + '}';
    }
}
