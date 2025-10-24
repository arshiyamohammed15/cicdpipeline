import * as vscode from 'vscode';
export declare class StatusBarManager implements vscode.Disposable {
    private statusBarItem;
    private readonly commandId;
    constructor();
    initialize(): void;
    updateStatus(hasReceipts: boolean, severity?: 'info' | 'warning' | 'error'): void;
    dispose(): void;
}
//# sourceMappingURL=StatusBarManager.d.ts.map