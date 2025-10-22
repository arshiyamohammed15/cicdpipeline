import * as vscode from 'vscode';
import { StatusBarManager } from './ui/status-bar/StatusBarManager';
import { ProblemsPanelManager } from './ui/problems-panel/ProblemsPanelManager';
import { DecisionCardManager } from './ui/decision-card/DecisionCardManager';
import { EvidenceDrawerManager } from './ui/evidence-drawer/EvidenceDrawerManager';
import { ToastManager } from './ui/toast/ToastManager';
import { ReceiptViewerManager } from './ui/receipt-viewer/ReceiptViewerManager';
import { ReceiptParser } from './shared/receipt-parser/ReceiptParser';

// Import UI Module Extension Interfaces
import { MMMEngineExtensionInterface } from './ui/mmm-engine/ExtensionInterface';
import { CrossCuttingConcernsExtensionInterface } from './ui/cross-cutting-concerns/ExtensionInterface';
import { ReleaseFailuresRollbacksExtensionInterface } from './ui/release-failures-rollbacks/ExtensionInterface';
import { SignalIngestionNormalizationExtensionInterface } from './ui/signal-ingestion-normalization/ExtensionInterface';
import { DetectionEngineCoreExtensionInterface } from './ui/detection-engine-core/ExtensionInterface';
import { LegacySystemsSafetyExtensionInterface } from './ui/legacy-systems-safety/ExtensionInterface';
import { TechnicalDebtAccumulationExtensionInterface } from './ui/technical-debt-accumulation/ExtensionInterface';
import { MergeConflictsDelaysExtensionInterface } from './ui/merge-conflicts-delays/ExtensionInterface';
import { ComplianceSecurityChallengesExtensionInterface } from './ui/compliance-security-challenges/ExtensionInterface';
import { IntegrationAdaptersExtensionInterface } from './ui/integration-adapters/ExtensionInterface';
import { FeatureDevelopmentBlindSpotsExtensionInterface } from './ui/feature-development-blind-spots/ExtensionInterface';
import { KnowledgeSiloPreventionExtensionInterface } from './ui/knowledge-silo-prevention/ExtensionInterface';
import { MonitoringObservabilityGapsExtensionInterface } from './ui/monitoring-observability-gaps/ExtensionInterface';
import { ClientAdminDashboardExtensionInterface } from './ui/client-admin-dashboard/ExtensionInterface';
import { ProductSuccessMonitoringExtensionInterface } from './ui/product-success-monitoring/ExtensionInterface';
import { ROIDashboardExtensionInterface } from './ui/roi-dashboard/ExtensionInterface';
import { GoldStandardsExtensionInterface } from './ui/gold-standards/ExtensionInterface';
import { KnowledgeIntegrityDiscoveryExtensionInterface } from './ui/knowledge-integrity-discovery/ExtensionInterface';
import { ReportingExtensionInterface } from './ui/reporting/ExtensionInterface';
import { QATestingDeficienciesExtensionInterface } from './ui/qa-testing-deficiencies/ExtensionInterface';

export function activate(context: vscode.ExtensionContext) {
    console.log('ZeroUI 2.0 Extension activated - Presentation-only mode');
    
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
    const complianceSecurityChallengesInterface = new ComplianceSecurityChallengesExtensionInterface();
    const integrationAdaptersInterface = new IntegrationAdaptersExtensionInterface();
    const featureDevelopmentBlindSpotsInterface = new FeatureDevelopmentBlindSpotsExtensionInterface();
    const knowledgeSiloPreventionInterface = new KnowledgeSiloPreventionExtensionInterface();
    const monitoringObservabilityGapsInterface = new MonitoringObservabilityGapsExtensionInterface();
    const clientAdminDashboardInterface = new ClientAdminDashboardExtensionInterface();
    const productSuccessMonitoringInterface = new ProductSuccessMonitoringExtensionInterface();
    const roiDashboardInterface = new ROIDashboardExtensionInterface();
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
    complianceSecurityChallengesInterface.registerCommands(context);
    complianceSecurityChallengesInterface.registerViews(context);
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
        complianceSecurityChallengesInterface,
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
