import * as vscode from 'vscode';
import axios from 'axios';
import { StatusBarManager } from './ui/status-bar/StatusBarManager';
import { ProblemsPanelManager } from './ui/problems-panel/ProblemsPanelManager';
import { DecisionCardManager } from './ui/decision-card/DecisionCardManager';
import { EvidenceDrawerManager } from './ui/evidence-drawer/EvidenceDrawerManager';
import { ToastManager } from './ui/toast/ToastManager';
import { ReceiptViewerManager } from './ui/receipt-viewer/ReceiptViewerManager';
import { ReceiptParser } from './shared/receipt-parser/ReceiptParser';

// Constitution Validation Service
class ConstitutionValidator {
    private validationServiceUrl: string;

    constructor(serviceUrl: string) {
        this.validationServiceUrl = serviceUrl;
    }

    async validateBeforeGeneration(prompt: string, fileType?: string, taskType?: string): Promise<boolean> {
        try {
            const response = await axios.post(`${this.validationServiceUrl}/validate`, {
                prompt,
                file_type: fileType || 'typescript',
                task_type: taskType || 'general'
            });

            const result = response.data;

            if (!result.valid) {
                this.showViolations(result.violations);
                this.showRecommendations(result.recommendations);
                return false;
            }

            vscode.window.showInformationMessage(
                `✅ Prompt validated against ${result.total_rules_checked} rules`
            );
            return true;

        } catch (error) {
            console.error('Validation service error:', error);
            // Allow generation if service fails to avoid blocking users
            vscode.window.showWarningMessage('Constitution validation service unavailable - proceeding with generation');
            return true;
        }
    }

    async generateWithValidation(service: string, prompt: string, context: any): Promise<string | null> {
        try {
            const response = await axios.post(`${this.validationServiceUrl}/generate`, {
                prompt,
                service,
                ...context
            });

            const result = response.data;

            if (!result.success) {
                vscode.window.showErrorMessage(`Generation failed: ${result.error}`);
                return null;
            }

            return result.generated_code;

        } catch (error) {
            console.error('Generation service error:', error);
            vscode.window.showErrorMessage('AI code generation service unavailable');
            return null;
        }
    }

    private showViolations(violations: any[]): void {
        const message = `Found ${violations.length} constitution violations`;
        vscode.window.showErrorMessage(message);

        // Add to problems panel
        violations.forEach(violation => {
            const diagnostic = new vscode.Diagnostic(
                new vscode.Range(violation.line_number - 1, 0, violation.line_number - 1, 100),
                violation.message,
                vscode.DiagnosticSeverity.Error
            );
            // Add diagnostic to appropriate file
        });
    }

    private showRecommendations(recommendations: string[]): void {
        if (recommendations.length > 0) {
            vscode.window.showInformationMessage(
                `Recommendations: ${recommendations[0]}`
            );
        }
    }
}

// Import UI Module Extension Interfaces
import { MMMEngineExtensionInterface } from './ui/mmm-engine/ExtensionInterface';
import { CrossCuttingConcernsExtensionInterface } from './ui/cross-cutting-concerns/ExtensionInterface';
import { ReleaseFailuresRollbacksExtensionInterface } from './ui/release-failures-rollbacks/ExtensionInterface';
import { SignalIngestionNormalizationExtensionInterface } from './ui/signal-ingestion-normalization/ExtensionInterface';
import { DetectionEngineCoreExtensionInterface } from './ui/detection-engine-core/ExtensionInterface';
import { LegacySystemsSafetyExtensionInterface } from './ui/legacy-systems-safety/ExtensionInterface';
import { TechnicalDebtAccumulationExtensionInterface } from './ui/technical-debt-accumulation/ExtensionInterface';
import { MergeConflictsDelaysExtensionInterface } from './ui/merge-conflicts-delays/ExtensionInterface';
import { ComplianceSecurityExtensionInterface } from './ui/compliance-security-challenges/ExtensionInterface';
import { IntegrationAdaptersExtensionInterface } from './ui/integration-adapters/ExtensionInterface';
import { FeatureDevelopmentBlindSpotsExtensionInterface } from './ui/feature-development-blind-spots/ExtensionInterface';
import { KnowledgeSiloPreventionExtensionInterface } from './ui/knowledge-silo-prevention/ExtensionInterface';
import { MonitoringObservabilityGapsExtensionInterface } from './ui/monitoring-observability-gaps/ExtensionInterface';
import { ClientAdminDashboardExtensionInterface } from './ui/client-admin-dashboard/ExtensionInterface';
import { ProductSuccessMonitoringExtensionInterface } from './ui/product-success-monitoring/ExtensionInterface';
import { RoiDashboardExtensionInterface } from './ui/roi-dashboard/ExtensionInterface';
import { GoldStandardsExtensionInterface } from './ui/gold-standards/ExtensionInterface';
import { KnowledgeIntegrityDiscoveryExtensionInterface } from './ui/knowledge-integrity-discovery/ExtensionInterface';
import { ReportingExtensionInterface } from './ui/reporting/ExtensionInterface';
import { QATestingDeficienciesExtensionInterface } from './ui/qa-testing-deficiencies/ExtensionInterface';

export function activate(context: vscode.ExtensionContext) {
    console.log('ZeroUI 2.0 Extension activated with Constitution Validation');

    // Initialize constitution validation service
    const validationServiceUrl = vscode.workspace.getConfiguration('zeroui').get('validationServiceUrl', 'http://localhost:5000');
    const constitutionValidator = new ConstitutionValidator(validationServiceUrl);

    // Initialize core UI managers
    const statusBarManager = new StatusBarManager();
    const problemsPanelManager = new ProblemsPanelManager();
    const decisionCardManager = new DecisionCardManager();
    const evidenceDrawerManager = new EvidenceDrawerManager();
    const toastManager = new ToastManager();
    const receiptViewerManager = new ReceiptViewerManager();
    const receiptParser = new ReceiptParser();
    
    // Initialize UI Module Extension Interfaces
    const mmmEngineInterface = new MMMEngineExtensionInterface();
    const crossCuttingConcernsInterface = new CrossCuttingConcernsExtensionInterface();
    const releaseFailuresRollbacksInterface = new ReleaseFailuresRollbacksExtensionInterface();
    const signalIngestionNormalizationInterface = new SignalIngestionNormalizationExtensionInterface();
    const detectionEngineCoreInterface = new DetectionEngineCoreExtensionInterface();
    const legacySystemsSafetyInterface = new LegacySystemsSafetyExtensionInterface();
    const technicalDebtAccumulationInterface = new TechnicalDebtAccumulationExtensionInterface();
    const mergeConflictsDelaysInterface = new MergeConflictsDelaysExtensionInterface();
    const complianceSecurityInterface = new ComplianceSecurityExtensionInterface();
    const integrationAdaptersInterface = new IntegrationAdaptersExtensionInterface();
    const featureDevelopmentBlindSpotsInterface = new FeatureDevelopmentBlindSpotsExtensionInterface();
    const knowledgeSiloPreventionInterface = new KnowledgeSiloPreventionExtensionInterface();
    const monitoringObservabilityGapsInterface = new MonitoringObservabilityGapsExtensionInterface();
    const clientAdminDashboardInterface = new ClientAdminDashboardExtensionInterface();
    const productSuccessMonitoringInterface = new ProductSuccessMonitoringExtensionInterface();
    const roiDashboardInterface = new RoiDashboardExtensionInterface();
    const goldStandardsInterface = new GoldStandardsExtensionInterface();
    const knowledgeIntegrityDiscoveryInterface = new KnowledgeIntegrityDiscoveryExtensionInterface();
    const reportingInterface = new ReportingExtensionInterface();
    const qaTestingDeficienciesInterface = new QATestingDeficienciesExtensionInterface();
    
    // Register core commands
    const showDecisionCard = vscode.commands.registerCommand('zeroui.showDecisionCard', () => {
        decisionCardManager.showDecisionCard();
    });
    
    const showEvidenceDrawer = vscode.commands.registerCommand('zeroui.showEvidenceDrawer', () => {
        evidenceDrawerManager.showEvidenceDrawer();
    });
    
    const showReceiptViewer = vscode.commands.registerCommand('zeroui.showReceiptViewer', () => {
        receiptViewerManager.showReceiptViewer();
    });
    
    const refresh = vscode.commands.registerCommand('zeroui.refresh', () => {
        problemsPanelManager.refresh();
    });

    // Constitution validation commands
    const validatePrompt = vscode.commands.registerCommand('zeroui.validatePrompt', async (prompt?: string) => {
        const promptText = prompt || await vscode.window.showInputBox({
            prompt: 'Enter prompt to validate',
            placeHolder: 'Create a function that...'
        });

        if (promptText) {
            const isValid = await constitutionValidator.validateBeforeGeneration(
                promptText,
                'typescript',
                'general'
            );

            if (isValid) {
                vscode.window.showInformationMessage('✅ Prompt validation passed - ready for code generation');
            } else {
                vscode.window.showErrorMessage('❌ Prompt validation failed - fix violations before proceeding');
            }
        }
    });

    const generateWithValidation = vscode.commands.registerCommand('zeroui.generateCode', async () => {
        const prompt = await vscode.window.showInputBox({
            prompt: 'Enter code generation prompt',
            placeHolder: 'Create a React component that...'
        });

        if (prompt) {
            const isValid = await constitutionValidator.validateBeforeGeneration(
                prompt,
                'typescript',
                'component'
            );

            if (isValid) {
                const generatedCode = await constitutionValidator.generateWithValidation(
                    'openai',
                    prompt,
                    {
                        file_type: 'typescript',
                        task_type: 'component',
                        temperature: 0.3
                    }
                );

                if (generatedCode) {
                    // Show generated code in new document
                    const document = await vscode.workspace.openTextDocument({
                        content: generatedCode,
                        language: 'typescript'
                    });
                    await vscode.window.showTextDocument(document);
                }
            }
        }
    });
    
    // Register UI Module commands and views
    mmmEngineInterface.registerCommands(context);
    mmmEngineInterface.registerViews(context);
    crossCuttingConcernsInterface.registerCommands(context);
    crossCuttingConcernsInterface.registerViews(context);
    releaseFailuresRollbacksInterface.registerCommands(context);
    releaseFailuresRollbacksInterface.registerViews(context);
    signalIngestionNormalizationInterface.registerCommands(context);
    signalIngestionNormalizationInterface.registerViews(context);
    detectionEngineCoreInterface.registerCommands(context);
    detectionEngineCoreInterface.registerViews(context);
    legacySystemsSafetyInterface.registerCommands(context);
    legacySystemsSafetyInterface.registerViews(context);
    technicalDebtAccumulationInterface.registerCommands(context);
    technicalDebtAccumulationInterface.registerViews(context);
    mergeConflictsDelaysInterface.registerCommands(context);
    mergeConflictsDelaysInterface.registerViews(context);
    complianceSecurityInterface.registerCommands(context);
    complianceSecurityInterface.registerViews(context);
    integrationAdaptersInterface.registerCommands(context);
    integrationAdaptersInterface.registerViews(context);
    featureDevelopmentBlindSpotsInterface.registerCommands(context);
    featureDevelopmentBlindSpotsInterface.registerViews(context);
    knowledgeSiloPreventionInterface.registerCommands(context);
    knowledgeSiloPreventionInterface.registerViews(context);
    monitoringObservabilityGapsInterface.registerCommands(context);
    monitoringObservabilityGapsInterface.registerViews(context);
    clientAdminDashboardInterface.registerCommands(context);
    clientAdminDashboardInterface.registerViews(context);
    productSuccessMonitoringInterface.registerCommands(context);
    productSuccessMonitoringInterface.registerViews(context);
    roiDashboardInterface.registerCommands(context);
    roiDashboardInterface.registerViews(context);
    goldStandardsInterface.registerCommands(context);
    goldStandardsInterface.registerViews(context);
    knowledgeIntegrityDiscoveryInterface.registerCommands(context);
    knowledgeIntegrityDiscoveryInterface.registerViews(context);
    reportingInterface.registerCommands(context);
    reportingInterface.registerViews(context);
    qaTestingDeficienciesInterface.registerCommands(context);
    qaTestingDeficienciesInterface.registerViews(context);
    
    // Register core disposables
    context.subscriptions.push(
        showDecisionCard,
        showEvidenceDrawer,
        showReceiptViewer,
        refresh,
        validatePrompt,
        generateWithValidation,
        statusBarManager,
        problemsPanelManager,
        decisionCardManager,
        evidenceDrawerManager,
        toastManager,
        receiptViewerManager,
        mmmEngineInterface,
        crossCuttingConcernsInterface,
        releaseFailuresRollbacksInterface,
        signalIngestionNormalizationInterface,
        detectionEngineCoreInterface,
        legacySystemsSafetyInterface,
        technicalDebtAccumulationInterface,
        mergeConflictsDelaysInterface,
        complianceSecurityInterface,
        integrationAdaptersInterface,
        featureDevelopmentBlindSpotsInterface,
        knowledgeSiloPreventionInterface,
        monitoringObservabilityGapsInterface,
        clientAdminDashboardInterface,
        productSuccessMonitoringInterface,
        roiDashboardInterface,
        goldStandardsInterface,
        knowledgeIntegrityDiscoveryInterface,
        reportingInterface,
        qaTestingDeficienciesInterface
    );
    
    // Initialize core UI components
    statusBarManager.initialize();
    problemsPanelManager.initialize();
    
    console.log('ZeroUI 2.0 Extension initialized - All UI components ready');
}

export function deactivate() {
    console.log('ZeroUI 2.0 Extension deactivated');
}
