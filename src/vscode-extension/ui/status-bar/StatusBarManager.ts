import * as vscode from 'vscode';

export class StatusBarManager implements vscode.Disposable {
    private statusBarItem: vscode.StatusBarItem;
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

    public updateStatus(hasReceipts: boolean, severity?: 'info' | 'warning' | 'error'): void {
        if (hasReceipts) {
            switch (severity) {
                case 'error':
                    this.statusBarItem.text = "$(error) ZeroUI Issues";
                    this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
                    break;
                case 'warning':
                    this.statusBarItem.text = "$(warning) ZeroUI Warnings";
                    this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
                    break;
                default:
                    this.statusBarItem.text = "$(info) ZeroUI Active";
                    this.statusBarItem.backgroundColor = undefined;
            }
        } else {
            this.statusBarItem.text = "$(check) ZeroUI Ready";
            this.statusBarItem.backgroundColor = undefined;
        }
    }

    public dispose(): void {
        this.statusBarItem.dispose();
    }
}
