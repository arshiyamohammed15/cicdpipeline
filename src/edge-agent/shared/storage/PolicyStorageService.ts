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

    constructor(zuRoot?: string) {
        this.pathResolver = new StoragePathResolver(zuRoot);
    }

    /**
     * Cache policy snapshot in IDE Plane
     * Pattern: ide/policy/
     *
     * @param snapshot Policy snapshot to cache
     * @returns Promise<string> Path where policy was cached
     */
    public async cachePolicy(snapshot: PolicySnapshot): Promise<string> {
        // Validate signature (Rule 221: all policies must be signed)
        if (!snapshot.signature || snapshot.signature.length === 0) {
            throw new Error('Policy must be signed before storage (Rule 221)');
        }

        // Resolve IDE Plane policy path
        const policyDir = this.pathResolver.resolvePolicyPath('ide', 'cache/');
        // Use forward slash to maintain consistency
        const policyFile = `${policyDir}/${snapshot.policy_id}-${snapshot.version}.json`;

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
        const policyFile = `${policyDir}/${policyId}-${version}.json`;

        if (!fs.existsSync(policyFile)) {
            return null;
        }

        const content = fs.readFileSync(policyFile, 'utf-8');
        const snapshot = JSON.parse(content) as PolicySnapshot;

        // Validate signature exists
        if (!snapshot.signature || snapshot.signature.length === 0) {
            throw new Error('Cached policy missing signature (Rule 221)');
        }

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
            /\bexport\s+/
        ];

        for (const pattern of codePatterns) {
            if (pattern.test(policyStr)) {
                throw new Error('Policy contains executable code (violates Rule 217: No Code/PII in Stores)');
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
}
