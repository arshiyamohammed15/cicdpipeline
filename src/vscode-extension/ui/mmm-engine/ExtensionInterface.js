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
exports.MMMEngineExtensionInterface = void 0;
const vscode = __importStar(require("vscode"));
const UIComponentManager_1 = require("./UIComponentManager");
class MMMEngineExtensionInterface {
    constructor() {
        this.disposables = [];
        this.uiManager = new UIComponentManager_1.MMMEngineUIComponentManager();
    }
    registerCommands(context) {
        // Register MMM Engine specific commands
        const showMMMDashboard = vscode.commands.registerCommand('zeroui.mmm.showDashboard', () => {
            this.uiManager.showMMMEngineDashboard();
        });
        const refreshMMMData = vscode.commands.registerCommand('zeroui.mmm.refresh', () => {
            this.uiManager.updateMMMEngineData({}); // Will be replaced with actual data
        });
        const exportMMMReport = vscode.commands.registerCommand('zeroui.mmm.exportReport', () => {
            this.exportMMMReport();
        });
        this.disposables.push(showMMMDashboard, refreshMMMData, exportMMMReport);
        context.subscriptions.push(...this.disposables);
    }
    registerViews(context) {
        // Register MMM Engine specific views
        const mmmTreeProvider = new MMMTreeDataProvider();
        const mmmTreeView = vscode.window.createTreeView('zerouiMMMEngine', {
            treeDataProvider: mmmTreeProvider,
            showCollapseAll: true
        });
        this.disposables.push(mmmTreeView);
        context.subscriptions.push(...this.disposables);
    }
    exportMMMReport() {
        vscode.window.showInformationMessage('MMM Engine report export functionality');
    }
    dispose() {
        this.disposables.forEach(d => d.dispose());
        this.uiManager.dispose();
    }
}
exports.MMMEngineExtensionInterface = MMMEngineExtensionInterface;
class MMMTreeDataProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
    }
    getTreeItem(element) {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.mmm.showDashboard',
            title: 'Show MMM Dashboard'
        };
        return treeItem;
    }
    getChildren(element) {
        return [
            { label: 'Metrics Overview' },
            { label: 'Measurements' },
            { label: 'Monitoring Status' }
        ];
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
}
//# sourceMappingURL=ExtensionInterface.js.map