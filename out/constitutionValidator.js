"use strict";
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConstitutionValidator = void 0;
const vscode = require("vscode");
class ConstitutionValidator {
    constructor(configManager) {
        this.configManager = configManager;
        this.diagnosticCollection = vscode.languages.createDiagnosticCollection('zeroui');
        // Rule 5: Keep Good Records + Logs
        this.logger = vscode.window.createOutputChannel('ZEROUI Validator');
        this.logger.appendLine('Constitution Validator initialized');
    }
    validateFile(document) {
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
    validateWorkspace() {
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
    validateWorkspaceFolder(folder) {
        // Rule 4: Get file patterns from configuration
        const filePatterns = this.configManager.getConfig('runtime_config', 'file_patterns', '**/*.{py,js,ts,jsx,tsx,html,css,json,yaml,yml}');
        const pattern = new vscode.RelativePattern(folder, filePatterns);
        vscode.workspace.findFiles(pattern).then(files => {
            for (const file of files) {
                vscode.workspace.openTextDocument(file).then(doc => {
                    this.validateFile(doc);
                });
            }
        });
    }
    checkConstitutionRules(document) {
        const violations = [];
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
        return violations;
    }
    checkIncompleteImplementations(lines, violations) {
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
                        confidence: 0.85,
                        explanation: 'This pattern typically indicates incomplete or temporary code that may not fully implement the requested functionality' // Rule 10: Explain Clearly
                    });
                }
            }
        }
    }
    checkAssumptionsAndMagicNumbers(lines, violations) {
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
                        confidence: 0.90,
                        explanation: 'Magic numbers and assumptions can lead to incorrect behavior when requirements change' // Rule 10: Explain Clearly
                    });
                }
            }
        }
    }
    checkHardcodedCredentials(lines, violations) {
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
                        confidence: 0.95,
                        explanation: 'Hardcoded credentials pose a significant security risk and should never be stored in source code' // Rule 10: Explain Clearly
                    });
                }
            }
        }
    }
    checkHardcodedValues(lines, violations) {
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
                        confidence: 0.80,
                        explanation: 'Hardcoded values make the system less flexible and harder to maintain' // Rule 10: Explain Clearly
                    });
                }
            }
        }
    }
    checkLoggingPatterns(lines, violations) {
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
                confidence: 0.75,
                explanation: 'Logging is essential for debugging and monitoring system behavior' // Rule 10: Explain Clearly
            });
        }
    }
    checkRollbackMechanisms(lines, violations) {
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
                confidence: 0.70,
                explanation: 'Rollback mechanisms are crucial for maintaining system reliability during updates' // Rule 10: Explain Clearly
            });
        }
    }
    checkPerformanceIssues(lines, violations) {
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
                        confidence: 0.85,
                        explanation: 'This pattern may indicate performance bottlenecks that could slow down the system' // Rule 10: Explain Clearly
                    });
                }
            }
        }
    }
    checkAITransparency(lines, violations) {
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
                    confidence: 0.90,
                    explanation: 'AI systems should provide transparency about their decision-making process' // Rule 10: Explain Clearly
                });
            }
        }
    }
    showDiagnostics(document, violations) {
        const diagnostics = [];
        for (const violation of violations) {
            const range = new vscode.Range(violation.lineNumber - 1, violation.columnNumber, violation.lineNumber - 1, violation.columnNumber + violation.codeSnippet.length);
            // Rule 10: Be Honest About AI Decisions + Explain Clearly
            const diagnosticMessage = `[Rule ${violation.ruleNumber}] ${violation.message}\nFix: ${violation.fixSuggestion}\nConfidence: ${Math.round(violation.confidence * 100)}%\nExplanation: ${violation.explanation}`;
            const diagnostic = new vscode.Diagnostic(range, diagnosticMessage, this.getDiagnosticSeverity(violation.severity));
            diagnostic.source = 'ZEROUI Constitution';
            diagnostic.code = violation.ruleNumber;
            diagnostics.push(diagnostic);
        }
        this.diagnosticCollection.set(document.uri, diagnostics);
    }
    getDiagnosticSeverity(severity) {
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
}
exports.ConstitutionValidator = ConstitutionValidator;
//# sourceMappingURL=constitutionValidator.js.map