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
exports.KnowledgeSiloPreventionExtensionInterface = void 0;
const vscode = __importStar(require("vscode"));
const UIComponentManager_1 = require("./UIComponentManager");
class KnowledgeSiloPreventionExtensionInterface {
    constructor() {
        this.disposables = [];
        this.uiManager = new UIComponentManager_1.KnowledgeSiloPreventionUIComponentManager();
    }
    registerCommands(context) {
        const showDashboard = vscode.commands.registerCommand('zeroui.knowledge.silo.prevention.showDashboard', () => {
            this.uiManager.showKnowledgeSiloPreventionDashboard();
        });
        const refresh = vscode.commands.registerCommand('zeroui.knowledge.silo.prevention.refresh', () => {
            this.uiManager.updateKnowledgeSiloPreventionData({});
        });
        this.disposables.push(showDashboard, refresh);
        context.subscriptions.push(...this.disposables);
    }
    registerViews(context) {
        const treeProvider = new KnowledgeSiloPreventionTreeDataProvider();
        const treeView = vscode.window.createTreeView('zerouiKnowledgeSiloPrevention', {
            treeDataProvider: treeProvider,
            showCollapseAll: true
        });
        this.disposables.push(treeView);
        context.subscriptions.push(...this.disposables);
    }
    dispose() {
        this.disposables.forEach(d => d.dispose());
        this.uiManager.dispose();
    }
}
exports.KnowledgeSiloPreventionExtensionInterface = KnowledgeSiloPreventionExtensionInterface;
class KnowledgeSiloPreventionTreeDataProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
    }
    getTreeItem(element) {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.knowledge.silo.prevention.showDashboard',
            title: 'Show KnowledgeSiloPrevention Dashboard'
        };
        return treeItem;
    }
    getChildren(element) {
        return [
            { label: 'Overview' },
            { label: 'Details' },
            { label: 'Reports' }
        ];
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
}
//# sourceMappingURL=ExtensionInterface.js.map