import * as vscode from 'vscode';
export declare class ReceiptViewerManager implements vscode.Disposable {
    private webviewPanel;
    constructor();
    showReceiptViewer(receiptData?: any): void;
    private getWebviewContent;
    private renderReceiptContent;
    dispose(): void;
}
//# sourceMappingURL=ReceiptViewerManager.d.ts.map