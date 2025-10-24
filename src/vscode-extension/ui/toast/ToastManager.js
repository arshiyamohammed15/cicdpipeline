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
exports.ToastManager = void 0;
const vscode = __importStar(require("vscode"));
class ToastManager {
    constructor() {
        this.activeToasts = [];
        // Initialize toast manager
    }
    showToast(message, type = 'info', actions) {
        const toast = vscode.window.showInformationMessage(message, ...(actions || []));
        this.activeToasts.push(toast);
    }
    showFeedbackToast(decisionId) {
        const message = 'How did this decision work for you?';
        const actions = ['Worked', 'Partly', "Didn't Work"];
        const toast = vscode.window.showInformationMessage(message, ...actions);
        this.activeToasts.push(toast);
        toast.then(selection => {
            if (selection) {
                this.handleFeedback(decisionId, selection);
            }
        });
    }
    handleFeedback(decisionId, feedback) {
        // Send feedback to Edge Agent
        console.log(`Feedback for decision ${decisionId}: ${feedback}`);
        // Show follow-up toast for tags if needed
        if (feedback === 'Partly' || feedback === "Didn't Work") {
            this.showTagSelectionToast(decisionId, feedback);
        }
    }
    showTagSelectionToast(decisionId, feedback) {
        const message = `Please select tags for "${feedback}" feedback:`;
        const actions = ['Too Noisy', 'Not Relevant', 'Incorrect', 'Other'];
        const toast = vscode.window.showInformationMessage(message, ...actions);
        this.activeToasts.push(toast);
        toast.then(selection => {
            if (selection) {
                console.log(`Tags for decision ${decisionId}: ${selection}`);
            }
        });
    }
    dispose() {
        this.activeToasts.forEach(toast => toast.dispose());
        this.activeToasts = [];
    }
}
exports.ToastManager = ToastManager;
//# sourceMappingURL=ToastManager.js.map