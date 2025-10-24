import * as vscode from 'vscode';
export declare class MMMEngineExtensionInterface implements vscode.Disposable {
    private uiManager;
    private disposables;
    constructor();
    registerCommands(context: vscode.ExtensionContext): void;
    registerViews(context: vscode.ExtensionContext): void;
    private exportMMMReport;
    dispose(): void;
}
//# sourceMappingURL=ExtensionInterface.d.ts.map