/**
 * LocalDRPlan
 *
 * Local file-based implementation of DRPlanPort.
 * Implements drills: backup-verify, queue-drain.
 */
import { DRPlanPort, DRPlan, DRPlanExecuteOptions, DRPlanExecutionResult, DRPlanTestResult, DRPlanHistoryOptions, DRPlanExecution } from '../../ports/DRPlanPort';
import { BackupPort } from '../../ports/BackupPort';
import { QueuePort } from '../../ports/QueuePort';
export declare class LocalDRPlan implements DRPlanPort {
    private baseDir;
    private plansFile;
    private executionsFile;
    private plans;
    private backupPort;
    private queuePort;
    constructor(baseDir: string, backupPort: BackupPort, queuePort: QueuePort);
    createPlan(plan: DRPlan): Promise<string>;
    getPlan(planId: string): Promise<DRPlan>;
    deletePlan(planId: string): Promise<void>;
    executePlan(planId: string, options?: DRPlanExecuteOptions): Promise<DRPlanExecutionResult>;
    testPlan(planId: string): Promise<DRPlanTestResult>;
    getExecutionHistory(planId: string, options?: DRPlanHistoryOptions): Promise<DRPlanExecution[]>;
    private executeStep;
    private executeBackupStep;
    private executeReplicateStep;
    private executeFailoverStep;
    private executeValidateStep;
    private executeNotifyStep;
    private loadPlans;
    private appendToJsonl;
    private ensureDirectory;
    private generatePlanId;
    private generateExecutionId;
    private sleep;
}
//# sourceMappingURL=LocalDRPlan.d.ts.map