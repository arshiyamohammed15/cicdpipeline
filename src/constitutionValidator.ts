/**
 * Constitution Validator for ZEROUI Extension
 * Following Constitution Rules:
 * - Rule 1: Do Exactly What's Asked
 * - Rule 2: Only Use Information You're Given
 * - Rule 3: Protect People's Privacy
 * - Rule 4: Use Settings Files, Not Hardcoded Numbers
 * - Rule 5: Keep Good Records + Keep Good Logs
 * - Rule 7: Never Break Things During Updates
 * - Rule 8: Make Things Fast + Respect People's Time
 * - Rule 10: Be Honest About AI Decisions + Explain Clearly
 */

import * as vscode from 'vscode';
import { ConfigManager } from './configManager';

export interface Violation {
    ruleNumber: number;
    ruleName: string;
    severity: 'error' | 'warning' | 'info';
    message: string;
    lineNumber: number;
    columnNumber: number;
    codeSnippet: string;
    fixSuggestion: string;
    confidence: number; // Rule 10: Be Honest About AI Decisions
    explanation: string; // Rule 10: Explain Clearly
}

export class ConstitutionValidator {
    private diagnosticCollection: vscode.DiagnosticCollection;
    private configManager: ConfigManager;
    private logger: vscode.OutputChannel;

    constructor(configManager: ConfigManager) {
        this.configManager = configManager;
        this.diagnosticCollection = vscode.languages.createDiagnosticCollection('zeroui');
        
        // Rule 5: Keep Good Records + Logs
        this.logger = vscode.window.createOutputChannel('ZEROUI Validator');
        this.logger.appendLine('Constitution Validator initialized');
    }

    public validateFile(document: vscode.TextDocument): void {
        // Rule 4: Check if validation is enabled from configuration
        const enableValidation = this.configManager.getConfig('runtime_config', 'enable_validation', 'true');
        if (enableValidation !== 'true') {
            return;
        }

        // Rule 5: Log validation start
        this.logger.appendLine(`Validating file: ${document.fileName}`);
        
        const violations = this.checkConstitutionRules(document);
        this.showDiagnostics(document, violations);
        
        // Rule 5: Log validation results
        this.logger.appendLine(`Found ${violations.length} violations in ${document.fileName}`);
    }

    public validateWorkspace(): void {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showWarningMessage('No workspace folder found');
            return;
        }

        // Rule 5: Log workspace validation
        this.logger.appendLine('Starting workspace validation');

        for (const folder of workspaceFolders) {
            this.validateWorkspaceFolder(folder);
        }
        
        this.logger.appendLine('Workspace validation completed');
    }

    private validateWorkspaceFolder(folder: vscode.WorkspaceFolder): void {
        // Rule 4: Get file patterns from configuration
        const filePatterns = this.configManager.getConfig(
            'runtime_config',
            'file_patterns',
            '**/*.{py,js,ts,jsx,tsx,html,css,json,yaml,yml}'
        );
        
        const pattern = new vscode.RelativePattern(folder, filePatterns);
        
        vscode.workspace.findFiles(pattern).then(files => {
            for (const file of files) {
                vscode.workspace.openTextDocument(file).then(doc => {
                    this.validateFile(doc);
                });
            }
        });
    }

    private checkConstitutionRules(document: vscode.TextDocument): Violation[] {
        const violations: Violation[] = [];
        const text = document.getText();
        const lines = text.split('\n');

        // Rule 1: Do Exactly What's Asked - Check for incomplete implementations
        this.checkIncompleteImplementations(lines, violations);

        // Rule 2: Only Use Information You're Given - Check for assumptions and magic numbers
        this.checkAssumptionsAndMagicNumbers(lines, violations);

        // Rule 3: Protect People's Privacy - Check for hardcoded credentials
        this.checkHardcodedCredentials(lines, violations);

        // Rule 4: Use Settings Files - Check for hardcoded values
        this.checkHardcodedValues(lines, violations);

        // Rule 5: Keep Good Records + Logs - Check for logging patterns
        this.checkLoggingPatterns(lines, violations);

        // Rule 7: Never Break Things During Updates - Check for rollback mechanisms
        this.checkRollbackMechanisms(lines, violations);

        // Rule 8: Make Things Fast - Check for performance issues
        this.checkPerformanceIssues(lines, violations);

        // Rule 10: Be Honest About AI Decisions - Check for AI transparency
        this.checkAITransparency(lines, violations);

        // New Constitution Categories
        this.checkCodeReviewRules(lines, violations);
        this.checkAPIContractsRules(lines, violations);
        this.checkCodingStandardsRules(lines, violations);
        this.checkCommentsRules(lines, violations);
        this.checkFolderStandardsRules(lines, violations);
        this.checkLoggingRules(lines, violations);

        return violations;
    }

    private checkIncompleteImplementations(lines: string[], violations: Violation[]): void {
        const incompletePatterns = [
            { pattern: /TODO|FIXME|HACK|XXX|TEMP/i, rule: 1, name: "Do Exactly What's Asked" },
            { pattern: /NotImplementedError|raise NotImplementedError/i, rule: 1, name: "Do Exactly What's Asked" },
            { pattern: /placeholder|stub|mock/i, rule: 1, name: "Do Exactly What's Asked" }
        ];

        for (let i = 0; i < lines.length; i++) {
            for (const { pattern, rule, name } of incompletePatterns) {
                if (pattern.test(lines[i])) {
                    violations.push({
                        ruleNumber: rule,
                        ruleName: name,
                        severity: 'warning',
                        message: 'Incomplete implementation detected - may not meet exact requirements',
                        lineNumber: i + 1,
                        columnNumber: 0,
                        codeSnippet: lines[i].trim(),
                        fixSuggestion: 'Complete the implementation according to requirements',
                        confidence: 0.85, // Rule 10: Be Honest About AI Decisions
                        explanation: 'This pattern typically indicates incomplete or temporary code that may not fully implement the requested functionality' // Rule 10: Explain Clearly
                    });
                }
            }
        }
    }

    private checkAssumptionsAndMagicNumbers(lines: string[], violations: Violation[]): void {
        const assumptionPatterns = [
            { pattern: /assume|assumption|guess|probably|maybe/i, rule: 2, name: "Only Use Information You're Given" },
            { pattern: /\b\d{2,}\b/, rule: 2, name: "Only Use Information You're Given" } // Magic numbers
        ];

        for (let i = 0; i < lines.length; i++) {
            for (const { pattern, rule, name } of assumptionPatterns) {
                if (pattern.test(lines[i])) {
                    violations.push({
                        ruleNumber: rule,
                        ruleName: name,
                        severity: 'warning',
                        message: 'Assumption or magic number detected - should only use given information',
                        lineNumber: i + 1,
                        columnNumber: 0,
                        codeSnippet: lines[i].trim(),
                        fixSuggestion: 'Use configuration values or constants instead of assumptions',
                        confidence: 0.90, // Rule 10: Be Honest About AI Decisions
                        explanation: 'Magic numbers and assumptions can lead to incorrect behavior when requirements change' // Rule 10: Explain Clearly
                    });
                }
            }
        }
    }

    private checkHardcodedCredentials(lines: string[], violations: Violation[]): void {
        const credentialPatterns = [
            { pattern: /password\s*=\s*["'][^"']+["']/i, rule: 3, name: "Protect People's Privacy" },
            { pattern: /api_key\s*=\s*["'][^"']+["']/i, rule: 3, name: "Protect People's Privacy" },
            { pattern: /secret\s*=\s*["'][^"']+["']/i, rule: 3, name: "Protect People's Privacy" },
            { pattern: /token\s*=\s*["'][^"']+["']/i, rule: 3, name: "Protect People's Privacy" }
        ];

        for (let i = 0; i < lines.length; i++) {
            for (const { pattern, rule, name } of credentialPatterns) {
                if (pattern.test(lines[i])) {
                    violations.push({
                        ruleNumber: rule,
                        ruleName: name,
                        severity: 'error',
                        message: 'Hardcoded credentials detected - use environment variables or secure config',
                        lineNumber: i + 1,
                        columnNumber: 0,
                        codeSnippet: lines[i].trim(),
                        fixSuggestion: 'Use environment variables or secure configuration management',
                        confidence: 0.95, // Rule 10: Be Honest About AI Decisions
                        explanation: 'Hardcoded credentials pose a significant security risk and should never be stored in source code' // Rule 10: Explain Clearly
                    });
                }
            }
        }
    }

    private checkHardcodedValues(lines: string[], violations: Violation[]): void {
        const hardcodedPatterns = [
            { pattern: /["']\w+["']\s*=\s*["']\w+["']/, rule: 4, name: "Use Settings Files + Easy Undo" },
            { pattern: /localhost|127\.0\.0\.1|0\.0\.0\.0/, rule: 4, name: "Use Settings Files + Easy Undo" }
        ];

        for (let i = 0; i < lines.length; i++) {
            for (const { pattern, rule, name } of hardcodedPatterns) {
                if (pattern.test(lines[i])) {
                    violations.push({
                        ruleNumber: rule,
                        ruleName: name,
                        severity: 'warning',
                        message: 'Hardcoded value detected - should use settings file',
                        lineNumber: i + 1,
                        columnNumber: 0,
                        codeSnippet: lines[i].trim(),
                        fixSuggestion: 'Move hardcoded values to configuration files',
                        confidence: 0.80, // Rule 10: Be Honest About AI Decisions
                        explanation: 'Hardcoded values make the system less flexible and harder to maintain' // Rule 10: Explain Clearly
                    });
                }
            }
        }
    }

    private checkLoggingPatterns(lines: string[], violations: Violation[]): void {
        const text = lines.join('\n');
        const loggingPatterns = ['log', 'logging', 'logger', 'audit', 'record', 'track'];
        const hasLogging = loggingPatterns.some(pattern => text.toLowerCase().includes(pattern));

        if (!hasLogging) {
            violations.push({
                ruleNumber: 5,
                ruleName: "Keep Good Records + Logs",
                severity: 'warning',
                message: 'No logging patterns detected',
                lineNumber: 1,
                columnNumber: 0,
                codeSnippet: 'Logging',
                fixSuggestion: 'Add proper logging for monitoring and debugging',
                confidence: 0.75, // Rule 10: Be Honest About AI Decisions
                explanation: 'Logging is essential for debugging and monitoring system behavior' // Rule 10: Explain Clearly
            });
        }
    }

    private checkRollbackMechanisms(lines: string[], violations: Violation[]): void {
        const text = lines.join('\n');
        const rollbackPatterns = ['rollback', 'undo', 'revert', 'backup', 'restore'];
        const hasRollback = rollbackPatterns.some(pattern => text.toLowerCase().includes(pattern));

        if (!hasRollback) {
            violations.push({
                ruleNumber: 7,
                ruleName: "Never Break Things During Updates",
                severity: 'info',
                message: 'No rollback mechanism detected',
                lineNumber: 1,
                columnNumber: 0,
                codeSnippet: 'Rollback mechanism',
                fixSuggestion: 'Add rollback mechanisms for safe updates',
                confidence: 0.70, // Rule 10: Be Honest About AI Decisions
                explanation: 'Rollback mechanisms are crucial for maintaining system reliability during updates' // Rule 10: Explain Clearly
            });
        }
    }

    private checkPerformanceIssues(lines: string[], violations: Violation[]): void {
        const performancePatterns = [
            { pattern: /for\s+.*for\s+.*:/, rule: 8, name: "Make Things Fast + Respect Time" },
            { pattern: /while\s+True:/, rule: 8, name: "Make Things Fast + Respect Time" },
            { pattern: /time\.sleep\(/, rule: 8, name: "Make Things Fast + Respect Time" }
        ];

        for (let i = 0; i < lines.length; i++) {
            for (const { pattern, rule, name } of performancePatterns) {
                if (pattern.test(lines[i])) {
                    violations.push({
                        ruleNumber: rule,
                        ruleName: name,
                        severity: 'warning',
                        message: 'Performance issue detected - may be slow',
                        lineNumber: i + 1,
                        columnNumber: 0,
                        codeSnippet: lines[i].trim(),
                        fixSuggestion: 'Consider optimizing for better performance',
                        confidence: 0.85, // Rule 10: Be Honest About AI Decisions
                        explanation: 'This pattern may indicate performance bottlenecks that could slow down the system' // Rule 10: Explain Clearly
                    });
                }
            }
        }
    }

    private checkAITransparency(lines: string[], violations: Violation[]): void {
        const text = lines.join('\n');
        const aiPatterns = ['ai_model', 'predict', 'classify', 'recommend', 'neural', 'machine_learning'];
        const hasAI = aiPatterns.some(pattern => text.toLowerCase().includes(pattern));

        if (hasAI) {
            const transparencyPatterns = ['confidence', 'explanation', 'reasoning', 'uncertainty', 'version'];
            const hasTransparency = transparencyPatterns.some(pattern => text.toLowerCase().includes(pattern));

            if (!hasTransparency) {
                violations.push({
                    ruleNumber: 10,
                    ruleName: "Be Honest About AI Decisions + Explain Clearly",
                    severity: 'warning',
                    message: 'AI code detected without transparency patterns',
                    lineNumber: 1,
                    columnNumber: 0,
                    codeSnippet: 'AI transparency',
                    fixSuggestion: 'Add confidence levels, explanations, and model version tracking',
                    confidence: 0.90, // Rule 10: Be Honest About AI Decisions
                    explanation: 'AI systems should provide transparency about their decision-making process' // Rule 10: Explain Clearly
                });
            }
        }
    }

    private showDiagnostics(document: vscode.TextDocument, violations: Violation[]): void {
        const diagnostics: vscode.Diagnostic[] = [];

        for (const violation of violations) {
            const range = new vscode.Range(
                violation.lineNumber - 1,
                violation.columnNumber,
                violation.lineNumber - 1,
                violation.columnNumber + violation.codeSnippet.length
            );

            // Rule 10: Be Honest About AI Decisions + Explain Clearly
            const diagnosticMessage = `[Rule ${violation.ruleNumber}] ${violation.message}\nFix: ${violation.fixSuggestion}\nConfidence: ${Math.round(violation.confidence * 100)}%\nExplanation: ${violation.explanation}`;

            const diagnostic = new vscode.Diagnostic(
                range,
                diagnosticMessage,
                this.getDiagnosticSeverity(violation.severity)
            );

            diagnostic.source = 'ZEROUI Constitution';
            diagnostic.code = violation.ruleNumber;
            diagnostics.push(diagnostic);
        }

        this.diagnosticCollection.set(document.uri, diagnostics);
    }

    private getDiagnosticSeverity(severity: string): vscode.DiagnosticSeverity {
        switch (severity) {
            case 'error':
                return vscode.DiagnosticSeverity.Error;
            case 'warning':
                return vscode.DiagnosticSeverity.Warning;
            case 'info':
                return vscode.DiagnosticSeverity.Information;
            default:
                return vscode.DiagnosticSeverity.Warning;
        }
    }

    // New Constitution Categories Validation Methods

    private checkCodeReviewRules(lines: string[], violations: Violation[]): void {
        const text = lines.join('\n');
        
        // Check for PR size indicators
        if (lines.length > 300) {
            violations.push({
                ruleNumber: 2,
                ruleName: "PR Size Guidance",
                severity: 'warning',
                message: 'PR size ≤ 300 LOC changed (tests excluded), include Rollout Plan if larger',
                lineNumber: 1,
                columnNumber: 0,
                codeSnippet: 'Large PR',
                fixSuggestion: 'Break into smaller, focused changes',
                confidence: 0.85,
                explanation: 'Large PRs are harder to review and increase risk of introducing bugs'
            });
        }

        // Check for CODEOWNERS approval requirements
        const sensitiveKeywords = ['auth', 'policy', 'contracts', 'receipts', 'migrations'];
        const hasSensitiveContent = sensitiveKeywords.some(keyword => text.toLowerCase().includes(keyword));
        
        if (hasSensitiveContent) {
            violations.push({
                ruleNumber: 3,
                ruleName: "CODEOWNERS Approval",
                severity: 'error',
                message: 'Sensitive areas require CODEOWNERS approval and may need two reviewers',
                lineNumber: 1,
                columnNumber: 0,
                codeSnippet: 'Sensitive content',
                fixSuggestion: 'Ensure CODEOWNERS approval for sensitive changes',
                confidence: 0.90,
                explanation: 'Sensitive areas require additional review to maintain security and compliance'
            });
        }
    }

    private checkAPIContractsRules(lines: string[], violations: Violation[]): void {
        const text = lines.join('\n');
        
        // Check for API versioning
        if (text.includes('/api/') && !text.includes('/v')) {
            violations.push({
                ruleNumber: 14,
                ruleName: "API Versioning",
                severity: 'error',
                message: 'URI versioning required: /v1, /v2...',
                lineNumber: 1,
                columnNumber: 0,
                codeSnippet: 'API endpoint',
                fixSuggestion: 'Use versioned API endpoints',
                confidence: 0.85,
                explanation: 'API versioning ensures backward compatibility and smooth transitions'
            });
        }

        // Check for idempotency
        if (text.includes('post') || text.includes('put') || text.includes('patch')) {
            if (!text.toLowerCase().includes('idempotency')) {
                violations.push({
                    ruleNumber: 15,
                    ruleName: "Idempotency",
                    severity: 'error',
                    message: 'All mutating routes must accept Idempotency-Key',
                    lineNumber: 1,
                    columnNumber: 0,
                    codeSnippet: 'Mutating operation',
                    fixSuggestion: 'Add idempotency support for mutating operations',
                    confidence: 0.80,
                    explanation: 'Idempotency prevents duplicate operations and improves reliability'
                });
            }
        }
    }

    private checkCodingStandardsRules(lines: string[], violations: Violation[]): void {
        const text = lines.join('\n');
        
        // Check for Python standards
        if (text.includes('import') && !text.includes('ruff') && !text.includes('black')) {
            violations.push({
                ruleNumber: 27,
                ruleName: "Python Standards",
                severity: 'error',
                message: 'ruff + black (line-length 100) + mypy --strict; Python 3.11+',
                lineNumber: 1,
                columnNumber: 0,
                codeSnippet: 'Python code',
                fixSuggestion: 'Use ruff, black, and mypy for code quality',
                confidence: 0.85,
                explanation: 'Consistent code formatting and type checking improve maintainability'
            });
        }

        // Check for TypeScript standards
        if (text.includes('function') && !text.includes('eslint') && !text.includes('prettier')) {
            violations.push({
                ruleNumber: 28,
                ruleName: "TypeScript Standards",
                severity: 'error',
                message: 'eslint + prettier; tsconfig strict: true, exactOptionalPropertyTypes',
                lineNumber: 1,
                columnNumber: 0,
                codeSnippet: 'TypeScript code',
                fixSuggestion: 'Use eslint and prettier for TypeScript code quality',
                confidence: 0.85,
                explanation: 'Consistent formatting and linting improve code quality and team collaboration'
            });
        }
    }

    private checkCommentsRules(lines: string[], violations: Violation[]): void {
        const text = lines.join('\n');
        
        // Check for simple English in comments
        const bannedWords = ['utilize', 'leverage', 'aforementioned', 'herein', 'thusly', 'performant', 'instantiate'];
        const hasBannedWords = bannedWords.some(word => text.toLowerCase().includes(word));
        
        if (hasBannedWords) {
            violations.push({
                ruleNumber: 8,
                ruleName: "Simple English Comments",
                severity: 'warning',
                message: 'Use simple English comments (grade 8 level)',
                lineNumber: 1,
                columnNumber: 0,
                codeSnippet: 'Complex comment',
                fixSuggestion: 'Use simpler, clearer language in comments',
                confidence: 0.80,
                explanation: 'Simple English makes code more accessible to all team members'
            });
        }

        // Check for TODO format
        const todoPattern = /TODO\s*[:(]?\s*([^\n]*)/i;
        const todoMatch = text.match(todoPattern);
        if (todoMatch && !todoMatch[1].includes('(')) {
            violations.push({
                ruleNumber: 89,
                ruleName: "TODO Policy",
                severity: 'warning',
                message: 'TODO(owner): description [ticket] [date] format required',
                lineNumber: 1,
                columnNumber: 0,
                codeSnippet: 'TODO comment',
                fixSuggestion: 'Use proper TODO format with owner and context',
                confidence: 0.90,
                explanation: 'Proper TODO format helps track and prioritize technical debt'
            });
        }
    }

    private checkFolderStandardsRules(lines: string[], violations: Violation[]): void {
        const text = lines.join('\n');
        
        // Check for hardcoded paths
        const hardcodedPathPattern = /["']\/[^"']*["']/;
        if (hardcodedPathPattern.test(text) && !text.includes('ZEROUI_ROOT')) {
            violations.push({
                ruleNumber: 54,
                ruleName: "File Naming",
                severity: 'error',
                message: 'Resolve all paths via ZEROUI_ROOT + config/paths.json; never hardcode paths',
                lineNumber: 1,
                columnNumber: 0,
                codeSnippet: 'Hardcoded path',
                fixSuggestion: 'Use ZEROUI_ROOT for path resolution',
                confidence: 0.85,
                explanation: 'Hardcoded paths make the system less portable and harder to maintain'
            });
        }

        // Check for storage rule
        if (text.includes('database') && text.includes('256')) {
            violations.push({
                ruleNumber: 82,
                ruleName: "Storage Rule",
                severity: 'error',
                message: 'Database vs files choice follows Storage Constitution (≤256KB in DB)',
                lineNumber: 1,
                columnNumber: 0,
                codeSnippet: 'Storage decision',
                fixSuggestion: 'Follow storage constitution guidelines',
                confidence: 0.80,
                explanation: 'Proper storage decisions improve performance and maintainability'
            });
        }
    }

    private checkLoggingRules(lines: string[], violations: Violation[]): void {
        const text = lines.join('\n');
        
        // Check for structured logging
        if (text.includes('log') && !text.includes('json') && !text.includes('structured')) {
            violations.push({
                ruleNumber: 43,
                ruleName: "Structured Logging",
                severity: 'error',
                message: 'Logs are structured JSON with required fields and schema version',
                lineNumber: 1,
                columnNumber: 0,
                codeSnippet: 'Logging code',
                fixSuggestion: 'Use structured JSON logging',
                confidence: 0.85,
                explanation: 'Structured logging improves observability and debugging capabilities'
            });
        }

        // Check for log levels
        const validLogLevels = ['TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'];
        const logLevelPattern = /\.(trace|debug|info|warn|error|fatal)\s*\(/i;
        const logMatch = text.match(logLevelPattern);
        
        if (logMatch) {
            const logLevel = logMatch[1].toUpperCase();
            if (!validLogLevels.includes(logLevel)) {
                violations.push({
                    ruleNumber: 44,
                    ruleName: "Log Levels",
                    severity: 'warning',
                    message: 'Use appropriate log levels: TRACE|DEBUG|INFO|WARN|ERROR|FATAL',
                    lineNumber: 1,
                    columnNumber: 0,
                    codeSnippet: 'Invalid log level',
                    fixSuggestion: 'Use standard log levels',
                    confidence: 0.90,
                    explanation: 'Standard log levels improve log filtering and analysis'
                });
            }
        }

        // Check for PII protection
        const piiPattern = /(password|secret|key|token|pii)\s*[:=]\s*["'][^"']+["']/i;
        if (piiPattern.test(text)) {
            violations.push({
                ruleNumber: 71,
                ruleName: "Log Security",
                severity: 'error',
                message: 'Never log secrets/PII; redact tokens, passwords, keys',
                lineNumber: 1,
                columnNumber: 0,
                codeSnippet: 'PII in logs',
                fixSuggestion: 'Remove or redact sensitive information from logs',
                confidence: 0.95,
                explanation: 'Logging sensitive information poses a security risk'
            });
        }
    }
}
