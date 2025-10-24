import * as vscode from 'vscode';
import { ComplianceSecurityData } from './types';
export declare class ComplianceSecurityUIComponentManager implements vscode.Disposable {
    private webviewPanel;
    private uiComponent;
    constructor();
    showComplianceSecurityDashboard(data?: ComplianceSecurityData): void;
    updateComplianceSecurityData(data: ComplianceSecurityData): void;
    dispose(): void;
}
//# sourceMappingURL=UIComponentManager.d.ts.map