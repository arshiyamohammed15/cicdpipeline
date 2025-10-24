import * as vscode from 'vscode';
export declare class ToastManager implements vscode.Disposable {
    private activeToasts;
    constructor();
    showToast(message: string, type?: 'info' | 'warning' | 'error' | 'success', actions?: string[]): void;
    showFeedbackToast(decisionId: string): void;
    private handleFeedback;
    private showTagSelectionToast;
    dispose(): void;
}
//# sourceMappingURL=ToastManager.d.ts.map