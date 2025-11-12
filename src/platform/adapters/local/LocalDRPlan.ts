/**
 * LocalDRPlan
 * 
 * Local file-based implementation of DRPlanPort.
 * Implements drills: backup-verify, queue-drain.
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  DRPlanPort,
  DRPlan,
  DRPlanExecuteOptions,
  DRPlanExecutionResult,
  DRPlanTestResult,
  DRPlanHistoryOptions,
  DRPlanExecution,
  DRPlanStepExecution,
} from '../../ports/DRPlanPort';
import { BackupPort } from '../../ports/BackupPort';
import { QueuePort } from '../../ports/QueuePort';

interface DRPlanRecord extends DRPlan {
  id: string;
}

interface DRPlanExecutionRecord extends DRPlanExecution {
  stepsExecuted: DRPlanStepExecution[];
}

export class LocalDRPlan implements DRPlanPort {
  private baseDir: string;
  private plansFile: string;
  private executionsFile: string;
  private plans: Map<string, DRPlanRecord> = new Map();
  private backupPort: BackupPort;
  private queuePort: QueuePort;

  constructor(baseDir: string, backupPort: BackupPort, queuePort: QueuePort) {
    this.baseDir = baseDir;
    this.plansFile = path.join(baseDir, 'dr-plans.jsonl');
    this.executionsFile = path.join(baseDir, 'dr-executions.jsonl');
    this.backupPort = backupPort;
    this.queuePort = queuePort;
    this.loadPlans();
  }

  async createPlan(plan: DRPlan): Promise<string> {
    const planId = plan.id || this.generatePlanId();
    const planRecord: DRPlanRecord = {
      ...plan,
      id: planId,
      status: plan.status || 'active',
    };

    this.plans.set(planId, planRecord);
    await this.appendToJsonl(this.plansFile, JSON.stringify(planRecord));

    return planId;
  }

  async getPlan(planId: string): Promise<DRPlan> {
    const plan = this.plans.get(planId);
    if (!plan) {
      throw new Error(`DR plan ${planId} not found`);
    }
    return plan;
  }

  async deletePlan(planId: string): Promise<void> {
    const plan = this.plans.get(planId);
    if (!plan) {
      throw new Error(`DR plan ${planId} not found`);
    }

    plan.status = 'inactive';
    await this.appendToJsonl(this.plansFile, JSON.stringify(plan));
    this.plans.delete(planId);
  }

  async executePlan(
    planId: string,
    options?: DRPlanExecuteOptions
  ): Promise<DRPlanExecutionResult> {
    const plan = this.plans.get(planId);
    if (!plan) {
      throw new Error(`DR plan ${planId} not found`);
    }

    const executionId = this.generateExecutionId();
    const startedAt = new Date();
    const stepsToExecute = options?.stepIds || plan.steps.map((s) => s.id);
    const stepsExecuted: DRPlanStepExecution[] = [];

    try {
      // Sort steps by order and filter by stepIds
      const sortedSteps = plan.steps
        .filter((step) => stepsToExecute.includes(step.id))
        .sort((a, b) => a.order - b.order);

      for (const step of sortedSteps) {
        // Check dependencies
        if (step.dependencies) {
          const dependencyResults = stepsExecuted.filter((se) =>
            step.dependencies!.includes(se.stepId)
          );
          const failedDeps = dependencyResults.filter((se) => se.status === 'failed');
          if (failedDeps.length > 0) {
            stepsExecuted.push({
              stepId: step.id,
              status: 'skipped',
              error: 'Dependency failed',
            });
            continue;
          }
        }

        const stepStart = new Date();
        let stepStatus: DRPlanStepExecution['status'] = 'running';
        let stepError: string | undefined;

        try {
          await this.executeStep(step, options?.dryRun || false);
          stepStatus = 'success';
        } catch (error) {
          stepStatus = 'failed';
          stepError = error instanceof Error ? error.message : String(error);
        }

        const stepEnd = new Date();
        const durationSeconds = (stepEnd.getTime() - stepStart.getTime()) / 1000;

        stepsExecuted.push({
          stepId: step.id,
          status: stepStatus,
          startedAt: stepStart,
          completedAt: stepEnd,
          durationSeconds,
          error: stepError,
        });

        // Check timeout
        if (options?.timeoutSeconds) {
          const totalDuration = (stepEnd.getTime() - startedAt.getTime()) / 1000;
          if (totalDuration > options.timeoutSeconds) {
            break;
          }
        }
      }

      const completedAt = new Date();
      const durationSeconds = (completedAt.getTime() - startedAt.getTime()) / 1000;
      const allSuccess = stepsExecuted.every((se) => se.status === 'success' || se.status === 'skipped');
      const anyFailed = stepsExecuted.some((se) => se.status === 'failed');

      const result: DRPlanExecutionResult = {
        executionId,
        status: allSuccess ? 'success' : anyFailed ? 'failed' : 'partial',
        startedAt,
        completedAt,
        durationSeconds,
        stepsExecuted,
        rpoAchieved: durationSeconds <= plan.rpoSeconds ? durationSeconds : undefined,
        rtoAchieved: durationSeconds <= plan.rtoSeconds ? durationSeconds : undefined,
      };

      // Save execution record
      const executionRecord: DRPlanExecutionRecord = {
        executionId,
        planId,
        status: result.status,
        startedAt,
        completedAt,
        durationSeconds,
        stepsExecuted,
      };
      await this.appendToJsonl(this.executionsFile, JSON.stringify(executionRecord));

      return result;
    } catch (error) {
      const completedAt = new Date();
      const durationSeconds = (completedAt.getTime() - startedAt.getTime()) / 1000;

      const result: DRPlanExecutionResult = {
        executionId,
        status: 'failed',
        startedAt,
        completedAt,
        durationSeconds,
        stepsExecuted,
        error: error instanceof Error ? error.message : String(error),
      };

      await this.appendToJsonl(this.executionsFile, JSON.stringify({
        executionId,
        planId,
        status: result.status,
        startedAt,
        completedAt,
        durationSeconds,
        stepsExecuted,
      }));

      return result;
    }
  }

  async testPlan(planId: string): Promise<DRPlanTestResult> {
    const testStart = new Date();
    const result = await this.executePlan(planId, { dryRun: true });
    const testEnd = new Date();
    const durationSeconds = (testEnd.getTime() - testStart.getTime()) / 1000;

    const warnings: string[] = [];
    const errors: string[] = [];

    for (const step of result.stepsExecuted) {
      if (step.status === 'failed') {
        errors.push(`Step ${step.stepId}: ${step.error || 'Unknown error'}`);
      } else if (step.status === 'skipped') {
        warnings.push(`Step ${step.stepId}: Skipped`);
      }
    }

    return {
      status: errors.length > 0 ? 'failed' : warnings.length > 0 ? 'warning' : 'passed',
      testedAt: testStart,
      durationSeconds,
      stepResults: result.stepsExecuted,
      warnings: warnings.length > 0 ? warnings : undefined,
      errors: errors.length > 0 ? errors : undefined,
    };
  }

  async getExecutionHistory(
    planId: string,
    options?: DRPlanHistoryOptions
  ): Promise<DRPlanExecution[]> {
    if (!fs.existsSync(this.executionsFile)) {
      return [];
    }

    const content = fs.readFileSync(this.executionsFile, 'utf-8');
    const lines = content.split('\n').filter((line) => line.trim());
    const executions: DRPlanExecution[] = [];

    for (const line of lines) {
      try {
        const record: DRPlanExecutionRecord = JSON.parse(line);
        
        // Filter by plan ID
        if (record.planId !== planId) {
          continue;
        }

        // Filter by start time
        if (options?.startTime && record.startedAt < options.startTime) {
          continue;
        }

        // Filter by end time
        if (options?.endTime && record.startedAt > options.endTime) {
          continue;
        }

        // Filter by status
        if (options?.status && record.status !== options.status) {
          continue;
        }

        executions.push({
          executionId: record.executionId,
          planId: record.planId,
          status: record.status,
          startedAt: record.startedAt,
          completedAt: record.completedAt,
          durationSeconds: record.durationSeconds,
        });
      } catch (error) {
        // Skip invalid lines
        continue;
      }
    }

    // Sort by start time (newest first)
    executions.sort((a, b) => b.startedAt.getTime() - a.startedAt.getTime());

    // Limit results
    if (options?.maxResults) {
      return executions.slice(0, options.maxResults);
    }

    return executions;
  }

  private async executeStep(step: DRPlan['steps'][0], dryRun: boolean): Promise<void> {
    if (dryRun) {
      // Simulate step execution
      await this.sleep(100);
      return;
    }

    switch (step.type) {
      case 'backup':
        await this.executeBackupStep(step);
        break;
      case 'replicate':
        await this.executeReplicateStep(step);
        break;
      case 'failover':
        await this.executeFailoverStep(step);
        break;
      case 'validate':
        await this.executeValidateStep(step);
        break;
      case 'notify':
        await this.executeNotifyStep(step);
        break;
      default:
        throw new Error(`Unknown step type: ${(step as { type: string }).type}`);
    }
  }

  private async executeBackupStep(step: DRPlan['steps'][0]): Promise<void> {
    // Drill: backup-verify
    const resourceId = step.config.resourceId as string;
    const resourceType = step.config.resourceType as string;

    if (!resourceId || !resourceType) {
      throw new Error('Backup step requires resourceId and resourceType');
    }

    // Create backup
    const backup = await this.backupPort.createBackup({
      resourceId,
      resourceType,
      name: step.name,
      description: step.description,
    });

    // Verify backup
    const verification = await this.backupPort.verifyBackup(backup.id);
    if (verification.status !== 'valid') {
      throw new Error(`Backup verification failed: ${verification.error}`);
    }
  }

  private async executeReplicateStep(step: DRPlan['steps'][0]): Promise<void> {
    // Simulate replication
    await this.sleep(500);
  }

  private async executeFailoverStep(step: DRPlan['steps'][0]): Promise<void> {
    // Simulate failover
    await this.sleep(1000);
  }

  private async executeValidateStep(step: DRPlan['steps'][0]): Promise<void> {
    // Drill: queue-drain
    const queueName = step.config.queueName as string;
    if (queueName) {
      // Drain queue
      let messages = await this.queuePort.receive(queueName, 10);
      while (messages.length > 0) {
        for (const message of messages) {
          await this.queuePort.delete(queueName, message.receiptHandle);
        }
        messages = await this.queuePort.receive(queueName, 10);
      }
    }
  }

  private async executeNotifyStep(step: DRPlan['steps'][0]): Promise<void> {
    // Simulate notification
    await this.sleep(100);
  }

  private loadPlans(): void {
    if (!fs.existsSync(this.plansFile)) {
      return;
    }

    const content = fs.readFileSync(this.plansFile, 'utf-8');
    const lines = content.split('\n').filter((line) => line.trim());

    for (const line of lines) {
      try {
        const plan: DRPlanRecord = JSON.parse(line);
        // Keep latest plan for each plan ID
        if (!this.plans.has(plan.id) || plan.status !== 'inactive') {
          this.plans.set(plan.id, plan);
        }
      } catch (error) {
        // Skip invalid lines
        continue;
      }
    }
  }

  private async appendToJsonl(filePath: string, jsonContent: string): Promise<void> {
    await this.ensureDirectory(path.dirname(filePath));

    try {
      await fs.promises.open(filePath, 'ax').then((handle) => handle.close());
    } catch (error) {
      const err = error as NodeJS.ErrnoException;
      if (err.code !== 'EEXIST') {
        throw err;
      }
    }

    const line = `${jsonContent}\n`;
    const handle = await fs.promises.open(filePath, 'a');
    try {
      await handle.write(line);
      await handle.sync();
    } finally {
      await handle.close();
    }
  }

  private async ensureDirectory(dirPath: string): Promise<void> {
    await fs.promises.mkdir(dirPath, { recursive: true });
  }

  private generatePlanId(): string {
    return `dr-plan-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
  }

  private generateExecutionId(): string {
    return `dr-exec-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

