/**
 * Detection Engine Core Quick Actions
 * 
 * Implements quick actions per PRD Section 3.8
 * Provides actionable quick fixes for detection issues
 */

import * as vscode from 'vscode';

export interface QuickAction {
    id: string;
    label: string;
    command: string;
    args?: any[];
}

export function getQuickActions(): QuickAction[] {
    return [
        {
            id: 'zeroui.m05.quickFix.viewDetails',
            label: 'View Detection Details',
            command: 'zeroui.m05.showDecisionCard'
        },
        {
            id: 'zeroui.m05.quickFix.viewReceipt',
            label: 'View Receipt',
            command: 'zeroui.m05.viewReceipt'
        },
        {
            id: 'zeroui.m05.quickFix.refresh',
            label: 'Refresh Detection Status',
            command: 'zeroui.detection.engine.core.refresh'
        },
        {
            id: 'zeroui.m05.quickFix.openDashboard',
            label: 'Open Dashboard',
            command: 'zeroui.detection.engine.core.showDashboard'
        }
    ];
}

// Legacy export for backward compatibility
export function getQuickActionsLegacy(): any[] {
    return getQuickActions().map(action => ({
        id: action.id,
        label: action.label
    }));
}
