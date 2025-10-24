import * as vscode from 'vscode';
export declare class ComplianceSecurityExtensionInterface implements vscode.Disposable {
    private uiManager;
    private disposables;
    constructor();
    registerCommands(context: vscode.ExtensionContext): void;
    registerViews(context: vscode.ExtensionContext): void;
    private runSecurityScan;
    private checkCompliance;
    private exportSecurityReport;
    dispose(): void;
}
//# sourceMappingURL=ExtensionInterface.d.ts.map