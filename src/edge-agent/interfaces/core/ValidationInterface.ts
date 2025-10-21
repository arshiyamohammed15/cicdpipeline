export interface ValidationInterface {
    /**
     * Validate a result against this module's validation rules
     * @param result The result to validate
     * @returns Promise<boolean> True if validation passes
     */
    validate(result: any): Promise<boolean>;

    /**
     * Get the validation rules for this module
     * @returns ValidationRule[] Array of validation rules
     */
    getValidationRules(): ValidationRule[];

    /**
     * Add a new validation rule
     * @param rule The validation rule to add
     */
    addValidationRule(rule: ValidationRule): void;

    /**
     * Remove a validation rule
     * @param ruleName The name of the rule to remove
     */
    removeValidationRule(ruleName: string): void;
}

export interface ValidationRule {
    name: string;
    description: string;
    validate: (result: any) => Promise<boolean>;
    severity: 'low' | 'medium' | 'high' | 'critical';
    category: 'security' | 'performance' | 'compliance' | 'data-integrity';
}

export interface ValidationResult {
    isValid: boolean;
    ruleResults: RuleResult[];
    overallScore: number;
    timestamp: Date;
    module: string;
}

export interface RuleResult {
    ruleName: string;
    passed: boolean;
    message: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    category: 'security' | 'performance' | 'compliance' | 'data-integrity';
}

export interface ValidationMetrics {
    totalValidations: number;
    passedValidations: number;
    failedValidations: number;
    averageScore: number;
    criticalFailures: number;
    securityFailures: number;
    performanceFailures: number;
    complianceFailures: number;
}
