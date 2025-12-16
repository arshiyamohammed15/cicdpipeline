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

/**
 * CR-061: Refined status determination logic considering severity levels.
 * 
 * Determines validation status based on issue categories and severity:
 * - Hard block: Security and integrity issues (hash-mismatch, policy, security, integrity)
 * - Soft block: Missing required artifacts/files (missing-file, missing-artifact, missing-dependency)
 * - Warn: Non-critical issues (warning, deprecation, style)
 * 
 * @param issues - Array of validation issues
 * @returns Validation status based on issue severity
 */
const determineStatus = (issues: PlanVerifierIssue[]): ValidationStatus => {
    if (issues.length === 0) {
        return 'pass';
    }
    
    // Hard block: Security and integrity issues
    const hardBlockCategories = ['hash-mismatch', 'policy', 'security', 'integrity'];
    if (issues.some(issue => hardBlockCategories.includes(issue.category))) {
        return 'hard_block';
    }
    
    // Soft block: Missing required artifacts/files
    const softBlockCategories = ['missing-file', 'missing-artifact', 'missing-dependency'];
    if (issues.some(issue => softBlockCategories.includes(issue.category))) {
        return 'soft_block';
    }
    
    // Warn: Non-critical issues
    const warnCategories = ['warning', 'deprecation', 'style'];
    if (issues.some(issue => warnCategories.includes(issue.category))) {
        return 'warn';
    }
    
    // Default to warn for unknown categories
    return 'warn';
};

/**
 * PreCommitValidationPipeline orchestrates the pre-commit validation process.
 * 
 * Runs a series of validators (PlanVerifier, BuildSandbox, and custom validators)
 * and aggregates their results to determine an overall validation status.
 * 
 * Status determination follows severity ordering:
 * - pass: No issues found
 * - warn: Non-critical issues
 * - soft_block: Missing required artifacts/files
 * - hard_block: Security/integrity issues (stops pipeline)
 */
export class PreCommitValidationPipeline {
    private readonly options: PreCommitValidationOptions;
    private readonly dependencies: PreCommitValidationDependencies;

    /**
     * Creates a new PreCommitValidationPipeline instance.
     * 
     * @param options - Validation options including workspace root and validator functions
     * @param dependencies - Optional dependency injection for testing (PlanVerifier, BuildSandbox factories)
     */
    constructor(
        options: PreCommitValidationOptions,
        dependencies: PreCommitValidationDependencies = {}
    ) {
        this.options = options;
        this.dependencies = dependencies;
    }

    /**
     * Runs the complete validation pipeline.
     * 
     * Executes validators in sequence, stopping early on hard_block status.
     * Each validator's exceptions are caught and logged without stopping the pipeline.
     * 
     * @returns Promise resolving to validation result with overall status and stage results
     */
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

        // CR-060: Catch exceptions per validator and continue pipeline
        for (const validator of validators) {
            try {
                const result = await validator();
                stages.push(result);
                if (severityOrder[result.status] > severityOrder[overallStatus]) {
                    overallStatus = result.status;
                }
                if (result.status === 'hard_block') {
                    break;
                }
            } catch (error) {
                // Log error and add error stage, but continue pipeline
                const errorMessage = error instanceof Error ? error.message : String(error);
                console.error(`Validator failed: ${errorMessage}`, error);
                stages.push({
                    stage: 'validator_error',
                    status: 'warn',
                    issues: [`Validator execution failed: ${errorMessage}`]
                });
                // Don't break pipeline on validator error, continue with other validators
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
