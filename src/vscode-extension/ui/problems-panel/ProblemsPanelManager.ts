import * as vscode from 'vscode';

export class ProblemsPanelManager implements vscode.Disposable {
    private readonly problemsProvider: ProblemsProvider;
    private problemsView: vscode.TreeView<any>;

    constructor() {
        this.problemsProvider = new ProblemsProvider();
        this.problemsView = vscode.window.createTreeView('zerouiProblems', {
            treeDataProvider: this.problemsProvider,
            showCollapseAll: true
        });
    }

    public initialize(): void {
        // Initialize problems panel
        this.refresh();
    }

    public refresh(): void {
        this.problemsProvider.refresh();
    }

    public addProblem(problem: any): void {
        this.problemsProvider.addProblem(problem);
    }

    public clearProblems(): void {
        this.problemsProvider.clearProblems();
    }

    public dispose(): void {
        this.problemsView.dispose();
    }
}

class ProblemsProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;
    private problems: any[] = [];

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.showDecisionCard',
            title: 'Show Decision Card',
            arguments: [element]
        };
        return treeItem;
    }

    getChildren(element?: any): any[] {
        return this.problems;
    }

    public refresh(): void {
        this._onDidChangeTreeData.fire(undefined);
    }

    public addProblem(problem: any): void {
        this.problems.push(problem);
        this.refresh();
    }

    public clearProblems(): void {
        this.problems = [];
        this.refresh();
    }
}
