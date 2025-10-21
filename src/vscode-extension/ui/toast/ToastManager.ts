import * as vscode from 'vscode';

export class ToastManager implements vscode.Disposable {
    private activeToasts: vscode.Disposable[] = [];

    constructor() {
        // Initialize toast manager
    }

    public showToast(message: string, type: 'info' | 'warning' | 'error' | 'success' = 'info', actions?: string[]): void {
        const toast = vscode.window.showInformationMessage(message, ...(actions || []));
        this.activeToasts.push(toast);
    }

    public showFeedbackToast(decisionId: string): void {
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

    private handleFeedback(decisionId: string, feedback: string): void {
        // Send feedback to Edge Agent
        console.log(`Feedback for decision ${decisionId}: ${feedback}`);
        
        // Show follow-up toast for tags if needed
        if (feedback === 'Partly' || feedback === "Didn't Work") {
            this.showTagSelectionToast(decisionId, feedback);
        }
    }

    private showTagSelectionToast(decisionId: string, feedback: string): void {
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

    public dispose(): void {
        this.activeToasts.forEach(toast => toast.dispose());
        this.activeToasts = [];
    }
}
