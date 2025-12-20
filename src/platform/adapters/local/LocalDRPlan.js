"use strict";
/**
 * LocalDRPlan
 *
 * Local file-based implementation of DRPlanPort.
 * Implements drills: backup-verify, queue-drain.
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.LocalDRPlan = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class LocalDRPlan {
    constructor(baseDir, backupPort, queuePort) {
        this.plans = new Map();
        this.baseDir = baseDir;
        this.plansFile = path.join(baseDir, 'dr-plans.jsonl');
        this.executionsFile = path.join(baseDir, 'dr-executions.jsonl');
        this.backupPort = backupPort;
        this.queuePort = queuePort;
        this.loadPlans();
    }
    async createPlan(plan) {
        const planId = plan.id || this.generatePlanId();
        const planRecord = {
            ...plan,
            id: planId,
            status: plan.status || 'active',
        };
        this.plans.set(planId, planRecord);
        await this.appendToJsonl(this.plansFile, JSON.stringify(planRecord));
        return planId;
    }
    async getPlan(planId) {
        const plan = this.plans.get(planId);
        if (!plan) {
            throw new Error(`DR plan ${planId} not found`);
        }
        return plan;
    }
    async deletePlan(planId) {
        const plan = this.plans.get(planId);
        if (!plan) {
            throw new Error(`DR plan ${planId} not found`);
        }
        plan.status = 'inactive';
        await this.appendToJsonl(this.plansFile, JSON.stringify(plan));
        this.plans.delete(planId);
    }
    async executePlan(planId, options) {
        const plan = this.plans.get(planId);
        if (!plan) {
            throw new Error(`DR plan ${planId} not found`);
        }
        const executionId = this.generateExecutionId();
        const startedAt = new Date();
        const stepsToExecute = options?.stepIds || plan.steps.map((s) => s.id);
        const stepsExecuted = [];
        try {
            // Sort steps by order and filter by stepIds
            const sortedSteps = plan.steps
                .filter((step) => stepsToExecute.includes(step.id))
                .sort((a, b) => a.order - b.order);
            for (const step of sortedSteps) {
                // Check dependencies
                if (step.dependencies) {
                    const dependencyResults = stepsExecuted.filter((se) => step.dependencies.includes(se.stepId));
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
                let stepStatus = 'running';
                let stepError;
                try {
                    await this.executeStep(step, options?.dryRun || false);
                    stepStatus = 'success';
                }
                catch (error) {
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
            const result = {
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
            const executionRecord = {
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
        }
        catch (error) {
            const completedAt = new Date();
            const durationSeconds = (completedAt.getTime() - startedAt.getTime()) / 1000;
            const result = {
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
    async testPlan(planId) {
        const testStart = new Date();
        const result = await this.executePlan(planId, { dryRun: true });
        const testEnd = new Date();
        const durationSeconds = (testEnd.getTime() - testStart.getTime()) / 1000;
        const warnings = [];
        const errors = [];
        for (const step of result.stepsExecuted) {
            if (step.status === 'failed') {
                errors.push(`Step ${step.stepId}: ${step.error || 'Unknown error'}`);
            }
            else if (step.status === 'skipped') {
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
    async getExecutionHistory(planId, options) {
        if (!fs.existsSync(this.executionsFile)) {
            return [];
        }
        const content = fs.readFileSync(this.executionsFile, 'utf-8');
        const lines = content.split('\n').filter((line) => line.trim());
        const executions = [];
        for (const line of lines) {
            try {
                const record = JSON.parse(line);
                // Filter by plan ID
                if (record.planId !== planId) {
                    continue;
                }
                const startedAt = new Date(record.startedAt);
                const completedAt = record.completedAt ? new Date(record.completedAt) : undefined;
                // Filter by start time
                if (options?.startTime && startedAt < options.startTime) {
                    continue;
                }
                // Filter by end time
                if (options?.endTime && startedAt > options.endTime) {
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
                    startedAt,
                    completedAt,
                    durationSeconds: record.durationSeconds,
                });
            }
            catch (error) {
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
    async executeStep(step, dryRun) {
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
                throw new Error(`Unknown step type: ${step.type}`);
        }
    }
    async executeBackupStep(step) {
        // Drill: backup-verify
        const resourceId = step.config.resourceId;
        const resourceType = step.config.resourceType;
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
    async executeReplicateStep(step) {
        // Simulate replication
        await this.sleep(500);
    }
    async executeFailoverStep(step) {
        // Simulate failover
        await this.sleep(1000);
    }
    async executeValidateStep(step) {
        // Drill: queue-drain
        const queueName = step.config.queueName;
        if (queueName) {
            // Drain queue efficiently: use larger batch size to reduce file I/O operations
            const batchSize = 50; // Increased from 10 to reduce number of receive operations
            let messages = await this.queuePort.receive(queueName, batchSize);
            while (messages.length > 0) {
                // Delete messages immediately to free up queue space
                for (const message of messages) {
                    await this.queuePort.delete(queueName, message.receiptHandle);
                }
                // Receive next batch
                messages = await this.queuePort.receive(queueName, batchSize);
            }
        }
    }
    async executeNotifyStep(step) {
        // Simulate notification
        await this.sleep(100);
    }
    loadPlans() {
        if (!fs.existsSync(this.plansFile)) {
            return;
        }
        const content = fs.readFileSync(this.plansFile, 'utf-8');
        const lines = content.split('\n').filter((line) => line.trim());
        for (const line of lines) {
            try {
                const plan = JSON.parse(line);
                // Keep latest plan for each plan ID
                if (!this.plans.has(plan.id) || plan.status !== 'inactive') {
                    this.plans.set(plan.id, plan);
                }
            }
            catch (error) {
                // Skip invalid lines
                continue;
            }
        }
    }
    async appendToJsonl(filePath, jsonContent) {
        await this.ensureDirectory(path.dirname(filePath));
        try {
            await fs.promises.open(filePath, 'ax').then((handle) => handle.close());
        }
        catch (error) {
            const err = error;
            if (err.code !== 'EEXIST') {
                throw err;
            }
        }
        const line = `${jsonContent}\n`;
        const handle = await fs.promises.open(filePath, 'a');
        try {
            await handle.write(line);
            await handle.sync();
        }
        finally {
            await handle.close();
        }
    }
    async ensureDirectory(dirPath) {
        await fs.promises.mkdir(dirPath, { recursive: true });
    }
    generatePlanId() {
        return `dr-plan-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
    }
    generateExecutionId() {
        return `dr-exec-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
    }
    sleep(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }
}
exports.LocalDRPlan = LocalDRPlan;
//# sourceMappingURL=LocalDRPlan.js.map