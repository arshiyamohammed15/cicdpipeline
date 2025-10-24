import * as vscode from 'vscode';
export declare class ProblemsPanelManager implements vscode.Disposable {
    private problemsProvider;
    private problemsView;
    constructor();
    initialize(): void;
    refresh(): void;
    addProblem(problem: any): void;
    clearProblems(): void;
    dispose(): void;
}
//# sourceMappingURL=ProblemsPanelManager.d.ts.map