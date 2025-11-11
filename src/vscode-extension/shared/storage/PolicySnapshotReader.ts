import * as fs from 'fs';
import * as path from 'path';
import { StoragePathResolver } from './StoragePathResolver';

export interface PolicySnapshotReaderResult {
    found: boolean;
    policy_snapshot_id: string;
}

export interface PolicySnapshotReaderOptions {
    policyId?: string;
    envVarName?: string;
    zuRoot?: string;
}

/**
 * Reads the active policy snapshot identifier from the IDE-plane cache.
 * Precedence: policy cache → environment variable → default literal.
 */
export class PolicySnapshotReader {
    private readonly policyId: string;
    private readonly envVarName: string;
    private readonly resolver: StoragePathResolver | null;

    constructor(options?: PolicySnapshotReaderOptions) {
        this.policyId = (options?.policyId ?? 'default').trim() || 'default';
        this.envVarName = (options?.envVarName ?? 'POLICY_SNAPSHOT_ID').trim() || 'POLICY_SNAPSHOT_ID';
        this.resolver = this.createResolver(options?.zuRoot);
    }

    public getCurrentSnapshotId(): PolicySnapshotReaderResult {
        const fromPolicy = this.readFromPolicyCache();
        if (fromPolicy) {
            return { found: true, policy_snapshot_id: fromPolicy };
        }

        const fromEnv = this.readFromEnv();
        if (fromEnv) {
            return { found: true, policy_snapshot_id: fromEnv };
        }

        return { found: false, policy_snapshot_id: 'MISSING' };
    }

    private createResolver(zuRoot?: string): StoragePathResolver | null {
        try {
            return new StoragePathResolver(zuRoot);
        } catch {
            return null;
        }
    }

    private readFromPolicyCache(): string | null {
        if (!this.resolver) {
            return null;
        }

        try {
            const policyBase = this.resolver.resolveIdePath('policy');
            const pointerPath = path.resolve(policyBase, 'current', `${this.policyId}.json`);

            if (!fs.existsSync(pointerPath)) {
                return null;
            }

            const pointerJson = this.safeParse(pointerPath);
            const pointerCandidate = this.extractSnapshotId(pointerJson);
            if (pointerCandidate) {
                return pointerCandidate;
            }

            const version = typeof pointerJson?.version === 'string'
                ? pointerJson.version.trim()
                : '';
            if (!version) {
                return null;
            }

            const cachedPath = path.resolve(policyBase, 'cache', `${this.policyId}-${version}.json`);
            if (!fs.existsSync(cachedPath)) {
                return null;
            }

            const cachedJson = this.safeParse(cachedPath);
            const cachedCandidate =
                this.extractSnapshotId(cachedJson) ??
                this.extractSnapshotId(cachedJson?.policy_content);

            return cachedCandidate ?? null;
        } catch {
            return null;
        }
    }

    private readFromEnv(): string | null {
        const value = process.env[this.envVarName];
        if (!value) {
            return null;
        }
        const trimmed = value.trim();
        return trimmed.length > 0 ? trimmed : null;
    }

    private safeParse(filePath: string): any {
        try {
            const content = fs.readFileSync(filePath, 'utf-8');
            return JSON.parse(content);
        } catch {
            return null;
        }
    }

    private extractSnapshotId(input: any): string | undefined {
        if (!input || typeof input !== 'object') {
            return undefined;
        }

        const direct =
            this.ensureString((input as any).policy_snapshot_id) ??
            this.ensureString((input as any).snapshot_id);

        if (direct) {
            return direct;
        }

        if (typeof (input as any).snapshot === 'object' && (input as any).snapshot !== null) {
            const nested =
                this.ensureString((input as any).snapshot.policy_snapshot_id) ??
                this.ensureString((input as any).snapshot.snapshot_id) ??
                this.ensureString((input as any).snapshot.id);
            if (nested) {
                return nested;
            }
        }

        return undefined;
    }

    private ensureString(value: unknown): string | undefined {
        if (typeof value === 'string') {
            const trimmed = value.trim();
            if (trimmed.length > 0) {
                return trimmed;
            }
        }
        return undefined;
    }
}

