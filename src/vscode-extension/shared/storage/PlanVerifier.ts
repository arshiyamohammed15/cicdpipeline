import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';
import { StoragePathResolver } from './StoragePathResolver';
import { PolicySnapshotReader } from './PolicySnapshotReader';
import { PSCLArtifactWriterOptions } from './PSCLArtifactWriter';

export interface PlanVerifierIssue {
    category: 'missing-file' | 'hash-mismatch' | 'missing-artifact' | 'policy';
    detail: string;
}

export interface PlanVerifierResult {
    ok: boolean;
    issues: PlanVerifierIssue[];
}

export interface PlanVerifierOptions extends PSCLArtifactWriterOptions {
    envelopeName?: string;
    buildPlanName?: string;
}

interface EnvelopeFileEntry {
    path: string;
    sha256: string;
}

interface FileEnvelope {
    policy_snapshot_id: string;
    files: Array<{ path: string; sha256: string; mode?: string }>;
    sbom_expected?: boolean;
    immutable_registry_required?: boolean;
}

export interface BuildPlan {
    policy_snapshot_id: string;
    artifact_id?: string;
    expected_artifact_digest?: string;
    expected_sbom_digest?: string;
    build_inputs?: string[];
    cost_profile?: string;
    routing?: string;
    canary?: {
        stages: number[];
    };
    model_cache_hints?: unknown;
    model_cache_hint?: unknown;
    modelCacheHints?: unknown;
    modelCacheHint?: unknown;
    [key: string]: unknown;
}

interface ReadJsonResult<T> {
    value: T | null;
    issue?: PlanVerifierIssue;
}

export class PlanVerifier {
    private readonly repoId: string;
    private readonly workspaceRoot: string;
    private readonly resolver: StoragePathResolver;
    private readonly policyReader: PolicySnapshotReader;
    private readonly envelopeName: string;
    private readonly buildPlanName: string;
    private lastEnvelope: FileEnvelope | null = null;
    private lastBuildPlan: BuildPlan | null = null;
    private lastPolicySnapshotId: string | null = null;

    constructor(private readonly options: PlanVerifierOptions = {}) {
        this.repoId = (options.repoId ?? 'default').trim() || 'default';
        this.workspaceRoot = path.resolve(options.workspaceRoot ?? '.');
        this.resolver = new StoragePathResolver(options.zuRoot);
        this.policyReader =
            options.readerInstance ?? new PolicySnapshotReader(options.policyReaderOptions);
        this.envelopeName = options.envelopeName ?? 'FileEnvelope.json';
        this.buildPlanName = options.buildPlanName ?? 'BuildPlan.json';
    }

    public verify(): PlanVerifierResult {
        const issues: PlanVerifierIssue[] = [];
        const psclDir = this.resolver.getPsclTempDir(this.repoId, {
            workspaceRoot: this.workspaceRoot
        });
        this.lastEnvelope = null;
        this.lastBuildPlan = null;

        const envelopePath = path.join(psclDir, this.envelopeName);
        const buildPlanPath = path.join(psclDir, this.buildPlanName);

        const envelope = this.readJson<FileEnvelope>(
            envelopePath,
            'missing-artifact',
            `PSCL envelope missing at ${envelopePath}`
        );

        if (envelope.issue) {
            issues.push(envelope.issue);
        }
        this.lastEnvelope = envelope.value ?? null;

        const buildPlan = this.readJson<BuildPlan>(
            buildPlanPath,
            'missing-artifact',
            `PSCL build plan missing at ${buildPlanPath}`
        );

        if (buildPlan.issue) {
            issues.push(buildPlan.issue);
        }
        this.lastBuildPlan = buildPlan.value ?? null;

        if (envelope.value && buildPlan.value) {
            this.checkHashes(envelope.value.files ?? [], issues);
            this.checkPolicySnapshot(envelope.value.policy_snapshot_id, buildPlan.value.policy_snapshot_id, issues);
        }

        return {
            ok: issues.length === 0,
            issues
        };
    }

    private readJson<T>(filePath: string, category: PlanVerifierIssue['category'], message: string): ReadJsonResult<T> {
        if (!fs.existsSync(filePath)) {
            return { value: null, issue: { category, detail: message } };
        }

        try {
            const content = fs.readFileSync(filePath, 'utf-8');
            return { value: JSON.parse(content) as T };
        } catch (error) {
            return {
                value: null,
                issue: {
                    category,
                    detail: `${message} (invalid JSON: ${(error as Error).message})`
                }
            };
        }
    }

    private checkHashes(files: EnvelopeFileEntry[], issues: PlanVerifierIssue[]): void {
        for (const file of files) {
            const absolutePath = path.resolve(this.workspaceRoot, file.path);
            if (!fs.existsSync(absolutePath) || fs.statSync(absolutePath).isDirectory()) {
                issues.push({
                    category: 'missing-file',
                    detail: `File missing: ${file.path}`
                });
                continue;
            }

            const actualHash = crypto
                .createHash('sha256')
                .update(fs.readFileSync(absolutePath))
                .digest('hex');

            if (actualHash !== file.sha256) {
                issues.push({
                    category: 'hash-mismatch',
                    detail: `Hash mismatch for ${file.path}: expected ${file.sha256}, actual ${actualHash}`
                });
            }
        }
    }

    private checkPolicySnapshot(envelopeId: string, planId: string, issues: PlanVerifierIssue[]): void {
        if (envelopeId !== planId) {
            issues.push({
                category: 'policy',
                detail: `Envelope/build plan snapshot mismatch: ${envelopeId} vs ${planId}`
            });
        }

        const snapshotResult = this.policyReader.getCurrentSnapshotId();
        if (!snapshotResult.found) {
            issues.push({
                category: 'policy',
                detail: `Policy snapshot unavailable locally (${snapshotResult.policy_snapshot_id})`
            });
            this.lastPolicySnapshotId = null;
            return;
        }

        if (snapshotResult.policy_snapshot_id !== envelopeId) {
            issues.push({
                category: 'policy',
                detail: `Policy snapshot mismatch: cached ${snapshotResult.policy_snapshot_id}, plan ${envelopeId}`
            });
        }

        this.lastPolicySnapshotId = snapshotResult.policy_snapshot_id;
    }

    public getEnvelope(): FileEnvelope | null {
        return this.lastEnvelope;
    }

    public getBuildPlan(): BuildPlan | null {
        return this.lastBuildPlan;
    }

    public getCachedPolicySnapshotId(): string | null {
        return this.lastPolicySnapshotId;
    }
}
