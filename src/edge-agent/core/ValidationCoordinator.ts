import { ValidationInterface, ValidationRule } from '../interfaces/core/ValidationInterface';
import { DelegationManager } from './DelegationManager';
import { DelegationResult } from '../interfaces/core/DelegationInterface';

export class ValidationCoordinator {
    private delegationManager: DelegationManager | null = null;
    private validationRules: Map<string, ValidationRule> = new Map();
    private validationHistory: any[] = [];

    public setDelegationManager(delegationManager: DelegationManager): void {
        this.delegationManager = delegationManager;
    }

    public async initialize(): Promise<void> {
        console.log('Validation Coordinator initializing...');
        this.setupValidationRules();
        console.log('Validation Coordinator initialized');
    }

    public async shutdown(): Promise<void> {
        console.log('Validation Coordinator shutting down...');
        this.validationHistory = [];
        console.log('Validation Coordinator shut down');
    }

    public async validate(result: DelegationResult): Promise<boolean> {
        console.log('Validating result...');

        const validationResult = {
            result,
            timestamp: new Date().toISOString(),
            validations: [],
            isValid: true
        };

        // Run validation rules
        for (const [ruleName, rule] of this.validationRules) {
            try {
                const ruleResult = await rule.validate(result);
                validationResult.validations.push({
                    rule: ruleName,
                    passed: ruleResult,
                    message: ruleResult ? 'Passed' : 'Failed'
                });

                if (!ruleResult) {
                    validationResult.isValid = false;
                }
            } catch (error) {
                validationResult.validations.push({
                    rule: ruleName,
                    passed: false,
                    message: `Error: ${error.message}`
                });
                validationResult.isValid = false;
            }
        }

        // Record validation
        this.validationHistory.push(validationResult);

        console.log(`Validation result: ${validationResult.isValid ? 'PASSED' : 'FAILED'}`);
        return validationResult.isValid;
    }

    private setupValidationRules(): void {
        // Security validation
        this.validationRules.set('security', {
            name: 'security',
            description: 'Validates that security checks have passed',
            severity: 'critical',
            category: 'security',
            validate: async (result: DelegationResult) => {
                return result.metadata.securityValidated === true;
            }
        });

        // Data integrity validation
        this.validationRules.set('integrity', {
            name: 'integrity',
            description: 'Validates data integrity checks',
            severity: 'high',
            category: 'data-integrity',
            validate: async (result: DelegationResult) => {
                return result.metadata.dataIntegrity === true;
            }
        });

        // Performance validation
        this.validationRules.set('performance', {
            name: 'performance',
            description: 'Validates performance metrics meet requirements',
            severity: 'medium',
            category: 'performance',
            validate: async (result: DelegationResult) => {
                return result.metadata.performanceMetrics && result.metadata.performanceMetrics.latency < 1000;
            }
        });

        // Compliance validation
        this.validationRules.set('compliance', {
            name: 'compliance',
            description: 'Validates compliance with security and data integrity requirements',
            severity: 'high',
            category: 'compliance',
            validate: async (result: DelegationResult) => {
                // Compliance is validated if security and data integrity are both valid
                return result.metadata.securityValidated === true && result.metadata.dataIntegrity === true;
            }
        });
    }

    public addValidationRule(name: string, rule: ValidationRule): void {
        this.validationRules.set(name, rule);
        console.log(`Added validation rule: ${name}`);
    }

    public removeValidationRule(name: string): void {
        this.validationRules.delete(name);
        console.log(`Removed validation rule: ${name}`);
    }

    public getValidationHistory(): any[] {
        return [...this.validationHistory];
    }

    public getValidationStats(): any {
        const total = this.validationHistory.length;
        const passed = this.validationHistory.filter(entry => entry.isValid).length;
        const failed = total - passed;

        return {
            total,
            passed,
            failed,
            successRate: total > 0 ? (passed / total) * 100 : 0
        };
    }

    public getValidationRules(): string[] {
        return Array.from(this.validationRules.keys());
    }
}
