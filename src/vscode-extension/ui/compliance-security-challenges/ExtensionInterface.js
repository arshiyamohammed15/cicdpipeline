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
exports.ComplianceSecurityExtensionInterface = void 0;
const vscode = __importStar(require("vscode"));
const UIComponentManager_1 = require("./UIComponentManager");
class ComplianceSecurityExtensionInterface {
    constructor() {
        this.disposables = [];
        this.uiManager = new UIComponentManager_1.ComplianceSecurityUIComponentManager();
    }
    registerCommands(context) {
        // Register Compliance & Security specific commands
        const showComplianceDashboard = vscode.commands.registerCommand('zeroui.compliance.showDashboard', () => {
            this.uiManager.showComplianceSecurityDashboard();
        });
        const runSecurityScan = vscode.commands.registerCommand('zeroui.compliance.runSecurityScan', () => {
            this.runSecurityScan();
        });
        const checkCompliance = vscode.commands.registerCommand('zeroui.compliance.checkCompliance', () => {
            this.checkCompliance();
        });
        const exportSecurityReport = vscode.commands.registerCommand('zeroui.compliance.exportReport', () => {
            this.exportSecurityReport();
        });
        this.disposables.push(showComplianceDashboard, runSecurityScan, checkCompliance, exportSecurityReport);
        context.subscriptions.push(...this.disposables);
    }
    registerViews(context) {
        // Register Compliance & Security specific views
        const complianceTreeProvider = new ComplianceTreeDataProvider();
        const complianceTreeView = vscode.window.createTreeView('zerouiComplianceSecurity', {
            treeDataProvider: complianceTreeProvider,
            showCollapseAll: true
        });
        this.disposables.push(complianceTreeView);
        context.subscriptions.push(...this.disposables);
    }
    runSecurityScan() {
        vscode.window.showInformationMessage('Running security scan...');
    }
    checkCompliance() {
        vscode.window.showInformationMessage('Checking compliance status...');
    }
    exportSecurityReport() {
        vscode.window.showInformationMessage('Exporting security report...');
    }
    dispose() {
        this.disposables.forEach(d => d.dispose());
        this.uiManager.dispose();
    }
}
exports.ComplianceSecurityExtensionInterface = ComplianceSecurityExtensionInterface;
class ComplianceTreeDataProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
    }
    getTreeItem(element) {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.compliance.showDashboard',
            title: 'Show Compliance Dashboard'
        };
        return treeItem;
    }
    getChildren(element) {
        return [
            { label: 'Security Score' },
            { label: 'Compliance Level' },
            { label: 'Security Challenges' },
            { label: 'Compliance Issues' }
        ];
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
}
//# sourceMappingURL=ExtensionInterface.js.map