"use strict";
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
exports.deactivate = exports.activate = void 0;
const vscode = __importStar(require("vscode"));
const StatusBarManager_1 = require("./ui/status-bar/StatusBarManager");
const ProblemsPanelManager_1 = require("./ui/problems-panel/ProblemsPanelManager");
const DecisionCardManager_1 = require("./ui/decision-card/DecisionCardManager");
const EvidenceDrawerManager_1 = require("./ui/evidence-drawer/EvidenceDrawerManager");
const ToastManager_1 = require("./ui/toast/ToastManager");
const ReceiptViewerManager_1 = require("./ui/receipt-viewer/ReceiptViewerManager");
const ReceiptParser_1 = require("./shared/receipt-parser/ReceiptParser");
// Import UI Module Extension Interfaces
const ExtensionInterface_1 = require("./ui/mmm-engine/ExtensionInterface");
const ExtensionInterface_2 = require("./ui/cross-cutting-concerns/ExtensionInterface");
const ExtensionInterface_3 = require("./ui/release-failures-rollbacks/ExtensionInterface");
const ExtensionInterface_4 = require("./ui/signal-ingestion-normalization/ExtensionInterface");
const ExtensionInterface_5 = require("./ui/detection-engine-core/ExtensionInterface");
const ExtensionInterface_6 = require("./ui/legacy-systems-safety/ExtensionInterface");
const ExtensionInterface_7 = require("./ui/technical-debt-accumulation/ExtensionInterface");
const ExtensionInterface_8 = require("./ui/merge-conflicts-delays/ExtensionInterface");
const ExtensionInterface_9 = require("./ui/compliance-security-challenges/ExtensionInterface");
const ExtensionInterface_10 = require("./ui/integration-adapters/ExtensionInterface");
const ExtensionInterface_11 = require("./ui/feature-development-blind-spots/ExtensionInterface");
const ExtensionInterface_12 = require("./ui/knowledge-silo-prevention/ExtensionInterface");
const ExtensionInterface_13 = require("./ui/monitoring-observability-gaps/ExtensionInterface");
const ExtensionInterface_14 = require("./ui/client-admin-dashboard/ExtensionInterface");
const ExtensionInterface_15 = require("./ui/product-success-monitoring/ExtensionInterface");
const ExtensionInterface_16 = require("./ui/roi-dashboard/ExtensionInterface");
const ExtensionInterface_17 = require("./ui/gold-standards/ExtensionInterface");
const ExtensionInterface_18 = require("./ui/knowledge-integrity-discovery/ExtensionInterface");
const ExtensionInterface_19 = require("./ui/reporting/ExtensionInterface");
const ExtensionInterface_20 = require("./ui/qa-testing-deficiencies/ExtensionInterface");
function activate(context) {
    console.log('ZeroUI 2.0 Extension activated - Presentation-only mode');
    // Initialize core UI managers
    const statusBarManager = new StatusBarManager_1.StatusBarManager();
    const problemsPanelManager = new ProblemsPanelManager_1.ProblemsPanelManager();
    const decisionCardManager = new DecisionCardManager_1.DecisionCardManager();
    const evidenceDrawerManager = new EvidenceDrawerManager_1.EvidenceDrawerManager();
    const toastManager = new ToastManager_1.ToastManager();
    const receiptViewerManager = new ReceiptViewerManager_1.ReceiptViewerManager();
    const receiptParser = new ReceiptParser_1.ReceiptParser();
    // Initialize UI Module Extension Interfaces
    const mmmEngineInterface = new ExtensionInterface_1.MMMEngineExtensionInterface();
    const crossCuttingConcernsInterface = new ExtensionInterface_2.CrossCuttingConcernsExtensionInterface();
    const releaseFailuresRollbacksInterface = new ExtensionInterface_3.ReleaseFailuresRollbacksExtensionInterface();
    const signalIngestionNormalizationInterface = new ExtensionInterface_4.SignalIngestionNormalizationExtensionInterface();
    const detectionEngineCoreInterface = new ExtensionInterface_5.DetectionEngineCoreExtensionInterface();
    const legacySystemsSafetyInterface = new ExtensionInterface_6.LegacySystemsSafetyExtensionInterface();
    const technicalDebtAccumulationInterface = new ExtensionInterface_7.TechnicalDebtAccumulationExtensionInterface();
    const mergeConflictsDelaysInterface = new ExtensionInterface_8.MergeConflictsDelaysExtensionInterface();
    const complianceSecurityChallengesInterface = new ExtensionInterface_9.ComplianceSecurityChallengesExtensionInterface();
    const integrationAdaptersInterface = new ExtensionInterface_10.IntegrationAdaptersExtensionInterface();
    const featureDevelopmentBlindSpotsInterface = new ExtensionInterface_11.FeatureDevelopmentBlindSpotsExtensionInterface();
    const knowledgeSiloPreventionInterface = new ExtensionInterface_12.KnowledgeSiloPreventionExtensionInterface();
    const monitoringObservabilityGapsInterface = new ExtensionInterface_13.MonitoringObservabilityGapsExtensionInterface();
    const clientAdminDashboardInterface = new ExtensionInterface_14.ClientAdminDashboardExtensionInterface();
    const productSuccessMonitoringInterface = new ExtensionInterface_15.ProductSuccessMonitoringExtensionInterface();
    const roiDashboardInterface = new ExtensionInterface_16.ROIDashboardExtensionInterface();
    const goldStandardsInterface = new ExtensionInterface_17.GoldStandardsExtensionInterface();
    const knowledgeIntegrityDiscoveryInterface = new ExtensionInterface_18.KnowledgeIntegrityDiscoveryExtensionInterface();
    const reportingInterface = new ExtensionInterface_19.ReportingExtensionInterface();
    const qaTestingDeficienciesInterface = new ExtensionInterface_20.QATestingDeficienciesExtensionInterface();
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
    context.subscriptions.push(showDecisionCard, showEvidenceDrawer, showReceiptViewer, refresh, statusBarManager, problemsPanelManager, decisionCardManager, evidenceDrawerManager, toastManager, receiptViewerManager, mmmEngineInterface, crossCuttingConcernsInterface, releaseFailuresRollbacksInterface, signalIngestionNormalizationInterface, detectionEngineCoreInterface, legacySystemsSafetyInterface, technicalDebtAccumulationInterface, mergeConflictsDelaysInterface, complianceSecurityChallengesInterface, integrationAdaptersInterface, featureDevelopmentBlindSpotsInterface, knowledgeSiloPreventionInterface, monitoringObservabilityGapsInterface, clientAdminDashboardInterface, productSuccessMonitoringInterface, roiDashboardInterface, goldStandardsInterface, knowledgeIntegrityDiscoveryInterface, reportingInterface, qaTestingDeficienciesInterface);
    // Initialize core UI components
    statusBarManager.initialize();
    problemsPanelManager.initialize();
    console.log('ZeroUI 2.0 Extension initialized - All UI components ready');
}
exports.activate = activate;
function deactivate() {
    console.log('ZeroUI 2.0 Extension deactivated');
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map