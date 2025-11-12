import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import { PlanVerifier, PlanVerifierOptions, PlanVerifierResult, PlanVerifierIssue, BuildPlan } from './PlanVerifier';
import { BuildSandbox } from './BuildSandbox';
import { ReceiptGenerator } from './ReceiptGenerator';
import { Ed25519ReceiptSigner } from './ReceiptSigner';
import { ReceiptStorageService } from './ReceiptStorageService';
import { StoragePathResolver } from './StoragePathResolver';
import { WorkloadRouter } from '../../../platform/router/WorkloadRouter';

type EvaluationPoint = 'pre-commit' | 'pre-merge' | 'pre-deploy' | 'post-deploy';

export interface PlanExecutionAgentOptions extends PlanVerifierOptions {
    gateId?: string;
    evaluationPoint?: EvaluationPoint;
    repoId?: string;
    signingKeyId: string;
    signingKeyPath?: string;
    signingKeyData?: string | Buffer;
    actorMachineFingerprint?: string;
}

export interface PlanExecutionResult {
    receiptPath: string;
    receiptStatus: 'pass' | 'warn' | 'soft_block' | 'hard_block';
    issues: PlanVerifierIssue[];
}

const sanitizeRepoId = (value: string): string =>
    value
        .toLowerCase()
        .replace(/[^a-z0-9-]/g, '-')
        .replace(/^-+|-+$/g, '') || 'default';

const isPlaceholderDigest = (value: string | undefined): boolean =>
    !value || value.trim() === '' || value.trim().toUpperCase() === '<TBD>';

export class PlanExecutionAgent {
    private readonly workspaceRoot: string;
    private readonly repoId: string;
    private readonly zuRoot: string;
    private readonly gateId: string;
    private readonly evaluationPoint: EvaluationPoint;

    constructor(private readonly options: PlanExecutionAgentOptions) {
        this.workspaceRoot = path.resolve(options.workspaceRoot ?? '.');
        const inferredRepoId =
            options.repoId && options.repoId.trim().length > 0
                ? options.repoId.trim()
                : vscode.workspace.workspaceFolders?.[0]?.name ?? 'default';
        this.repoId = sanitizeRepoId(inferredRepoId);
        this.zuRoot = path.resolve(options.zuRoot ?? process.env.ZU_ROOT ?? '');
        if (!this.zuRoot) {
            throw new Error('ZU_ROOT is required for PlanExecutionAgent');
        }
        this.gateId = options.gateId ?? 'zeroui.pscl.precommit';
        this.evaluationPoint = options.evaluationPoint ?? 'pre-commit';
    }

    public async execute(): Promise<PlanExecutionResult> {
        const planVerifier = new PlanVerifier({
            ...this.options,
            repoId: this.repoId,
            workspaceRoot: this.workspaceRoot,
            zuRoot: this.zuRoot
        });

        const verification = planVerifier.verify();
        const envelope = planVerifier.getEnvelope();
        const buildPlan = planVerifier.getBuildPlan();
        const issues = [...verification.issues];

        if (!envelope || !buildPlan) {
            return this.storeReceipt(issues, null, null, null);
        }

        const buildInputs = buildPlan.build_inputs ?? [];
        const sandbox = new BuildSandbox({
            workspaceRoot: this.workspaceRoot,
            buildInputs
        });
        const sandboxResult = sandbox.run();

        if (!isPlaceholderDigest(buildPlan.expected_artifact_digest) &&
            buildPlan.expected_artifact_digest !== sandboxResult.artifact_digest) {
            issues.push({
                category: 'hash-mismatch',
                detail: `Artifact digest mismatch: expected ${buildPlan.expected_artifact_digest}, actual ${sandboxResult.artifact_digest}`
            });
        }

        if (!isPlaceholderDigest(buildPlan.expected_sbom_digest) &&
            buildPlan.expected_sbom_digest !== sandboxResult.sbom_digest) {
            issues.push({
                category: 'hash-mismatch',
                detail: `SBOM digest mismatch: expected ${buildPlan.expected_sbom_digest}, actual ${sandboxResult.sbom_digest}`
            });
        }

        return this.storeReceipt(
            issues,
            envelope,
            buildPlan,
            sandboxResult
        );
    }

    private determineStatus(issues: PlanVerifierIssue[]): 'pass' | 'warn' | 'soft_block' | 'hard_block' {
        if (issues.length === 0) {
            return 'pass';
        }
        const hasHard = issues.some(issue => issue.category === 'hash-mismatch' || issue.category === 'policy');
        if (hasHard) {
            return 'hard_block';
        }
        const hasMissing = issues.some(issue => issue.category === 'missing-file' || issue.category === 'missing-artifact');
        if (hasMissing) {
            return 'soft_block';
        }
        return 'warn';
    }

    private loadPrivateKey(keyId: string): Buffer | string {
        if (this.options.signingKeyData) {
            return this.options.signingKeyData;
        }
        if (this.options.signingKeyPath) {
            return fs.readFileSync(this.options.signingKeyPath, 'utf-8');
        }
        const defaultPath = path.join(this.zuRoot, 'ide', 'trust', 'private', `${keyId}.pem`);
        return fs.readFileSync(defaultPath, 'utf-8');
    }

    private buildPolicyVersionIds(envelope: { policy_snapshot_id: string } | null): string[] {
        if (!envelope) {
            return [];
        }
        return [envelope.policy_snapshot_id];
    }

    private async storeReceipt(
        issues: PlanVerifierIssue[],
        envelope: { policy_snapshot_id: string } | null,
        buildPlan: BuildPlan | null,
        sandboxResult: { artifact_digest: string; sbom_digest: string } | null
    ): Promise<PlanExecutionResult> {
        const status = this.determineStatus(issues);
        const rationale =
            issues.length === 0
                ? 'All PSCL plan validations passed.'
                : issues.map(issue => issue.detail).join('; ');

        const policySnapshotId = envelope?.policy_snapshot_id ?? 'MISSING';
        const artifactDigest = sandboxResult?.artifact_digest ?? 'sha256:unavailable';
        const sbomDigest = sandboxResult?.sbom_digest ?? 'sha256:unavailable';
        const expectedArtifact = buildPlan?.expected_artifact_digest ?? '<TBD>';
        const expectedSbom = buildPlan?.expected_sbom_digest ?? '<TBD>';
        const buildInputs = buildPlan?.build_inputs ?? [];
        const artifactId =
            typeof buildPlan?.artifact_id === 'string' && buildPlan.artifact_id.trim().length > 0
                ? buildPlan.artifact_id.trim()
                : undefined;

        const extractPathFromDetail = (detail: string): string | undefined => {
            const hashMatch = detail.match(/Hash mismatch for\s+(.+?):\s+expected/i);
            if (hashMatch?.[1]) {
                return hashMatch[1];
            }
            const missingMatch = detail.match(/File missing:\s+(.+)/i);
            if (missingMatch?.[1]) {
                return missingMatch[1];
            }
            return undefined;
        };

        const mismatches = issues
            .filter(issue => issue.category === 'hash-mismatch' || issue.category === 'missing-file')
            .map(issue => ({
                category: issue.category,
                detail: issue.detail,
                path: extractPathFromDetail(issue.detail)
            }));
        const labels: Record<string, unknown> = {};

        const costProfile = typeof buildPlan?.cost_profile === 'string' ? buildPlan.cost_profile : undefined;
        const routing = typeof buildPlan?.routing === 'string' ? buildPlan.routing : undefined;
        const modelCacheHints =
            buildPlan?.model_cache_hints ??
            buildPlan?.model_cache_hint ??
            (buildPlan && ('modelCacheHints' in buildPlan ? (buildPlan as any).modelCacheHints : undefined)) ??
            (buildPlan && ('modelCacheHint' in buildPlan ? (buildPlan as any).modelCacheHint : undefined));

        if (costProfile && costProfile.trim().length > 0) {
            labels.cost_profile = costProfile;
        }

        if (routing && routing.trim().length > 0) {
            labels.routing = routing;
        }

        if (modelCacheHints !== undefined) {
            labels.model_cache_hints = modelCacheHints;
        }

        // Add infra labels from WorkloadRouter if buildPlan exists
        // Check if labels field exists in inputs (schema allows it via Record<string, any>)
        // If schema forbids labels and they don't exist, we would STOP here, but since
        // inputs is Record<string, any>, labels are allowed
        if (buildPlan) {
            try {
                const routerBaseDir = path.join(this.zuRoot, 'ide', 'router');
                const router = new WorkloadRouter(routerBaseDir, 'development');
                const routingDecision = router.decide(buildPlan);
                
                // Generate decision ID (deterministic based on timestamp and routing)
                const decisionId = `infra-${Date.now()}-${routingDecision.route}-${routingDecision.adapter}`;
                
                // Extend existing labels object (labels already exists from above)
                labels.infra_route = routingDecision.route;
                labels.infra_cost_profile = costProfile || (typeof buildPlan.cost_profile === 'string' ? buildPlan.cost_profile : 'default');
                labels.infra_adapter = routingDecision.adapter;
                labels.infra_decision_id = decisionId;
            } catch (error) {
                // If WorkloadRouter fails, continue without infra labels
                // This is a non-blocking enhancement
                // In production, this would be logged but not block receipt generation
                // Error might be: infra config not found, adapters disabled, etc.
            }
        }

        const signer = new Ed25519ReceiptSigner({
            privateKey: this.loadPrivateKey(this.options.signingKeyId),
            keyId: this.options.signingKeyId
        });

        const generator = new ReceiptGenerator(signer);
        const receiptInputs: Record<string, unknown> = {
            evaluation_point: this.evaluationPoint,
            policy_snapshot_id: policySnapshotId,
            artifact_digest: artifactDigest,
            expected_artifact_digest: expectedArtifact,
            sbom_digest: sbomDigest,
            expected_sbom_digest: expectedSbom,
            build_inputs: buildInputs
        };

        if (artifactId) {
            receiptInputs.artifact_id = artifactId;
        }

        if (Object.keys(labels).length > 0) {
            receiptInputs.labels = labels;
        }

        if (mismatches.length > 0) {
            receiptInputs.mismatches = mismatches;
        }

        const actor: { repo_id: string; machine_fingerprint?: string } = {
            repo_id: this.repoId
        };
        const fingerprint = this.options.actorMachineFingerprint;
        if (typeof fingerprint === 'string' && fingerprint.trim().length > 0) {
            actor.machine_fingerprint = fingerprint;
        }

        const receipt = generator.generateDecisionReceipt(
            this.gateId,
            this.buildPolicyVersionIds(envelope),
            policySnapshotId,
            receiptInputs,
            {
                status,
                rationale,
                badges: ['pscl-plan', status]
            },
            [],
            actor,
            status !== 'pass',
            this.evaluationPoint
        );

        const storage = new ReceiptStorageService(this.zuRoot);
        const receiptPath = await storage.storeDecisionReceipt(receipt, this.repoId);

        return {
            receiptPath,
            receiptStatus: status,
            issues
        };
    }
}

