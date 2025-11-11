import * as vscode from 'vscode';

type PreCommitStatus = 'pass' | 'warn' | 'soft_block' | 'hard_block' | 'unknown';

export class StatusBarManager implements vscode.Disposable {
    private readonly statusBarItem: vscode.StatusBarItem;
    private readonly commandId = 'zeroui.showDecisionCard';

    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
        this.statusBarItem.command = this.commandId;
    }

    public initialize(): void {
        this.statusBarItem.text = "$(check) ZeroUI Ready";
        this.statusBarItem.tooltip = "ZeroUI 2.0 - Click to show decision card";
        this.statusBarItem.show();
    }

    public setPreCommitStatus(status: PreCommitStatus, tooltip?: string): void {
        switch (status) {
            case 'pass':
                this.statusBarItem.text = '$(check) Pre-commit: PASS';
                this.statusBarItem.backgroundColor = undefined;
                break;
            case 'warn':
                this.statusBarItem.text = '$(warning) Pre-commit: WARN';
                this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
                break;
            case 'soft_block':
            case 'hard_block':
                this.statusBarItem.text = '$(error) Pre-commit: BLOCK';
                this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
                break;
            default:
                this.statusBarItem.text = "$(check) ZeroUI Ready";
                this.statusBarItem.backgroundColor = undefined;
        }

        if (tooltip) {
            this.statusBarItem.tooltip = tooltip;
        } else {
            this.statusBarItem.tooltip = "ZeroUI 2.0 - Click to show decision card";
        }
    }

    public dispose(): void {
        this.statusBarItem.dispose();
    }
}
