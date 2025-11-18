import { PlanVerifier, PlanVerifierOptions, PlanVerifierIssue, PlanVerifierResult } from '../storage/PlanVerifier';
import { BuildSandbox, BuildSandboxInputs, BuildSandboxResult } from '../storage/BuildSandbox';

export type ValidationStatus = 'pass' | 'warn' | 'soft_block' | 'hard_block';

export interface ValidationStageResult {
    stage: string;
    status: ValidationStatus;
    issues?: string[];
}

export type ValidationStep = () => Promise<ValidationStageResult>;

export interface PreCommitValidationOptions extends PlanVerifierOptions {
    validators?: ValidationStep[];
}

interface PlanVerifierLike {
    verify(): PlanVerifierResult;
    getEnvelope(): ReturnType<PlanVerifier['getEnvelope']>;
    getBuildPlan(): ReturnType<PlanVerifier['getBuildPlan']>;
}

interface BuildSandboxLike {
    run(): BuildSandboxResult;
}

export interface PreCommitValidationDependencies {
    createPlanVerifier?: (options: PlanVerifierOptions) => PlanVerifierLike;
    createBuildSandbox?: (inputs: BuildSandboxInputs) => BuildSandboxLike;
}

export interface PreCommitValidationResult {
    status: ValidationStatus;
    stages: ValidationStageResult[];
}

const severityOrder: Record<ValidationStatus, number> = {
    pass: 0,
    warn: 1,
    soft_block: 2,
    hard_block: 3
};

const isPlaceholderDigest = (value: string | undefined): boolean =>
    !value || value.trim() === '' || value.trim().toUpperCase() === '<TBD>';

const determineStatus = (issues: PlanVerifierIssue[]): ValidationStatus => {
    if (issues.length === 0) {
        return 'pass';
    }
    if (issues.some(issue => issue.category === 'hash-mismatch' || issue.category === 'policy')) {
        return 'hard_block';
    }
    if (issues.some(issue => issue.category === 'missing-file' || issue.category === 'missing-artifact')) {
        return 'soft_block';
    }
    return 'warn';
};

export class PreCommitValidationPipeline {
    private readonly options: PreCommitValidationOptions;
    private readonly dependencies: PreCommitValidationDependencies;

    constructor(
        options: PreCommitValidationOptions,
        dependencies: PreCommitValidationDependencies = {}
    ) {
        this.options = options;
        this.dependencies = dependencies;
    }

    public async run(): Promise<PreCommitValidationResult> {
        const stages: ValidationStageResult[] = [];

        const verifier = this.createPlanVerifier();
        const verification = verifier.verify();

        const issues = [...verification.issues];
        const envelope = verifier.getEnvelope();
        const buildPlan = verifier.getBuildPlan();

        if (envelope && buildPlan) {
            const sandbox = this.createBuildSandbox({
                workspaceRoot: this.options.workspaceRoot ?? process.cwd(),
                buildInputs: buildPlan.build_inputs ?? []
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
        }

        const psclStatus = determineStatus(issues);

        stages.push({
            stage: 'pscl',
            status: psclStatus,
            issues: issues.map(issue => issue.detail)
        });

        if (psclStatus === 'hard_block') {
            return {
                status: 'hard_block',
                stages
            };
        }

        const validators = this.options.validators ?? [];
        let overallStatus: ValidationStatus = psclStatus;

        for (const validator of validators) {
            const result = await validator();
            stages.push(result);
            if (severityOrder[result.status] > severityOrder[overallStatus]) {
                overallStatus = result.status;
            }
            if (result.status === 'hard_block') {
                break;
            }
        }

        return {
            status: overallStatus,
            stages
        };
    }

    private createPlanVerifier(): PlanVerifierLike {
        if (this.dependencies.createPlanVerifier) {
            return this.dependencies.createPlanVerifier(this.options);
        }
        return new PlanVerifier(this.options);
    }

    private createBuildSandbox(inputs: BuildSandboxInputs): BuildSandboxLike {
        if (this.dependencies.createBuildSandbox) {
            return this.dependencies.createBuildSandbox(inputs);
        }
        return new BuildSandbox(inputs);
    }
}
