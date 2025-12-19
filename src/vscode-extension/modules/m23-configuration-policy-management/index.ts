/**
 * Module entry point for Configuration & Policy Management (EPC-3).
 *
 * Per PRD: Registers module with VS Code extension.
 */

import * as vscode from 'vscode';
import { ConfigurationPolicyManagementExtensionInterface } from '../../ui/configuration-policy-management/ExtensionInterface';

export function activate(context: vscode.ExtensionContext): void {
    const extensionInterface = new ConfigurationPolicyManagementExtensionInterface();

    // Register commands and views
    extensionInterface.registerCommands(context);
    extensionInterface.registerViews(context);

    context.subscriptions.push(extensionInterface);
}

export function deactivate(): void {
    // Cleanup if needed
}
