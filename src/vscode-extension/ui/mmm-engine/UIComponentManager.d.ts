import * as vscode from 'vscode';
import { MMMEngineData } from './types';
export declare class MMMEngineUIComponentManager implements vscode.Disposable {
    private webviewPanel;
    private uiComponent;
    constructor();
    showMMMEngineDashboard(data?: MMMEngineData): void;
    updateMMMEngineData(data: MMMEngineData): void;
    dispose(): void;
}
//# sourceMappingURL=UIComponentManager.d.ts.map