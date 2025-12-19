/**
 * Commands for Configuration & Policy Management (EPC-3).
 *
 * Per PRD: Registers VS Code commands for module operations.
 */

import * as vscode from 'vscode';
import { ConfigurationPolicyManagementExtensionInterface } from '../../ui/configuration-policy-management/ExtensionInterface';

export function registerCommands(context: vscode.ExtensionContext): void {
    const extensionInterface = new ConfigurationPolicyManagementExtensionInterface();
    extensionInterface.registerCommands(context);
}
