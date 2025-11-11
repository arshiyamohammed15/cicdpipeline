import { PreCommitValidationPipeline, ValidationStageResult } from '../PreCommitValidationPipeline';
import { PlanVerifierIssue } from '../../storage/PlanVerifier';

describe('PreCommitValidationPipeline', () => {
    const createPlanVerifierMock = (
        issues: PlanVerifierIssue[],
        envelope: any,
        buildPlan: any
    ) => {
        return {
            verify: jest.fn(() => ({ ok: issues.length === 0, issues })),
            getEnvelope: jest.fn(() => envelope),
            getBuildPlan: jest.fn(() => buildPlan)
        };
    };

    const createBuildSandboxMock = (result: { artifact_digest: string; sbom_digest: string }) => {
        return {
            run: jest.fn(() => result)
        };
    };

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('runs PSCL first and continues with additional validators when not hard_block', async () => {
        const planVerifier = createPlanVerifierMock([], { policy_snapshot_id: 'SNAP', files: [] }, {
            policy_snapshot_id: 'SNAP',
            expected_artifact_digest: '<TBD>',
            expected_sbom_digest: '<TBD>',
            build_inputs: ['src/**']
        });

        const sandbox = createBuildSandboxMock({
            artifact_digest: 'sha256:abc',
            sbom_digest: 'sha256:def'
        });

        const validatorOne = jest.fn<Promise<ValidationStageResult>, []>(async () => ({
            stage: 'unit-tests',
            status: 'warn',
            issues: ['unit test failures']
        }));

        const validatorTwo = jest.fn<Promise<ValidationStageResult>, []>(async () => ({
            stage: 'lint',
            status: 'pass'
        }));

        const pipeline = new PreCommitValidationPipeline(
            {
                repoId: 'demo-repo',
                workspaceRoot: '/workspace',
                validators: [validatorOne, validatorTwo]
            },
            {
                createPlanVerifier: () => planVerifier,
                createBuildSandbox: () => sandbox
            }
        );

        const result = await pipeline.run();

        expect(planVerifier.verify).toHaveBeenCalledTimes(1);
        expect(sandbox.run).toHaveBeenCalledTimes(1);
        expect(validatorOne).toHaveBeenCalledTimes(1);
        expect(validatorTwo).toHaveBeenCalledTimes(1);

        expect(result.status).toBe('warn');
        expect(result.stages[0].stage).toBe('pscl');
        expect(result.stages[1].stage).toBe('unit-tests');
        expect(result.stages[2].stage).toBe('lint');
    });

    it('short-circuits remaining validations when PSCL returns hard_block', async () => {
        const issues: PlanVerifierIssue[] = [
            {
                category: 'hash-mismatch',
                detail: 'Digest mismatch detected'
            }
        ];

        const planVerifier = createPlanVerifierMock(issues, null, null);
        const sandbox = createBuildSandboxMock({
            artifact_digest: 'sha256:abc',
            sbom_digest: 'sha256:def'
        });

        const validator = jest.fn<Promise<ValidationStageResult>, []>(async () => ({
            stage: 'secondary',
            status: 'pass'
        }));

        const pipeline = new PreCommitValidationPipeline(
            {
                repoId: 'demo-repo',
                workspaceRoot: '/workspace',
                validators: [validator]
            },
            {
                createPlanVerifier: () => planVerifier,
                createBuildSandbox: () => sandbox
            }
        );

        const result = await pipeline.run();

        expect(planVerifier.verify).toHaveBeenCalledTimes(1);
        expect(sandbox.run).not.toHaveBeenCalled();
        expect(validator).not.toHaveBeenCalled();

        expect(result.status).toBe('hard_block');
        expect(result.stages).toHaveLength(1);
        expect(result.stages[0].stage).toBe('pscl');
        expect(result.stages[0].issues).toContain('Digest mismatch detected');
    });
});

