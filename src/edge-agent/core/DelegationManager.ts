import { DelegationInterface } from '../interfaces/core/DelegationInterface';
import { AgentOrchestrator } from './AgentOrchestrator';

export class DelegationManager {
    private orchestrator: AgentOrchestrator | null = null;
    private delegationHistory: any[] = [];

    public setOrchestrator(orchestrator: AgentOrchestrator): void {
        this.orchestrator = orchestrator;
    }

    public async initialize(): Promise<void> {
        console.log('Delegation Manager initializing...');
        // Initialize delegation capabilities
        console.log('Delegation Manager initialized');
    }

    public async shutdown(): Promise<void> {
        console.log('Delegation Manager shutting down...');
        this.delegationHistory = [];
        console.log('Delegation Manager shut down');
    }

    public async delegate(task: any): Promise<any> {
        if (!this.orchestrator) {
            throw new Error('Orchestrator not set');
        }

        console.log('Delegating task:', task.type || 'unknown');

        // Record delegation
        this.delegationHistory.push({
            task,
            timestamp: new Date().toISOString(),
            status: 'delegated'
        });

        // Determine appropriate module for delegation
        const targetModule = this.determineTargetModule(task);
        
        if (!targetModule) {
            throw new Error(`No suitable module found for task: ${task.type}`);
        }

        // Delegate to appropriate module
        const result = await this.executeDelegation(targetModule, task);
        
        // Update delegation history
        this.updateDelegationHistory(task, result);

        return result;
    }

    private determineTargetModule(task: any): string | null {
        // Determine which module should handle this task
        const taskType = task.type || 'unknown';

        switch (taskType) {
            case 'security':
                return 'security';
            case 'cache':
                return 'cache';
            case 'inference':
                return 'inference';
            case 'model':
                return 'models';
            case 'resource':
                return 'resources';
            case 'hybrid':
                return 'hybrid';
            default:
                return 'hybrid'; // Default to hybrid orchestrator
        }
    }

    private async executeDelegation(moduleName: string, task: any): Promise<any> {
        const module = this.orchestrator?.getModule(moduleName);
        
        if (!module) {
            throw new Error(`Module ${moduleName} not found`);
        }

        if (!module.delegate || typeof module.delegate !== 'function') {
            throw new Error(`Module ${moduleName} does not support delegation`);
        }

        return await module.delegate(task);
    }

    private updateDelegationHistory(task: any, result: any): void {
        const lastEntry = this.delegationHistory[this.delegationHistory.length - 1];
        if (lastEntry) {
            lastEntry.result = result;
            lastEntry.status = 'completed';
            lastEntry.completedAt = new Date().toISOString();
        }
    }

    public getDelegationHistory(): any[] {
        return [...this.delegationHistory];
    }

    public getDelegationStats(): any {
        const total = this.delegationHistory.length;
        const completed = this.delegationHistory.filter(entry => entry.status === 'completed').length;
        const failed = this.delegationHistory.filter(entry => entry.status === 'failed').length;

        return {
            total,
            completed,
            failed,
            successRate: total > 0 ? (completed / total) * 100 : 0
        };
    }
}
