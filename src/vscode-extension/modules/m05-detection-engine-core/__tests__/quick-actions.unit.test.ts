/**
 * Unit Tests for Detection Engine Core Quick Actions
 * 
 * Tests quick actions per PRD §3.8
 * Coverage: 100% of quick-actions.ts
 */

import { getQuickActions, getQuickActionsLegacy, QuickAction } from '../actions/quick-actions';

describe('Detection Engine Core Quick Actions - Unit Tests', () => {
    describe('getQuickActions', () => {
        it('should return array of quick actions', () => {
            const actions = getQuickActions();
            expect(Array.isArray(actions)).toBe(true);
            expect(actions.length).toBe(4);
        });

        it('should return actions with correct structure', () => {
            const actions = getQuickActions();
            actions.forEach(action => {
                expect(action).toHaveProperty('id');
                expect(action).toHaveProperty('label');
                expect(action).toHaveProperty('command');
            });
        });

        it('should return viewDetails action', () => {
            const actions = getQuickActions();
            const viewDetails = actions.find(a => a.id === 'zeroui.m05.quickFix.viewDetails');
            expect(viewDetails).toBeDefined();
            expect(viewDetails?.label).toBe('View Detection Details');
            expect(viewDetails?.command).toBe('zeroui.m05.showDecisionCard');
        });

        it('should return viewReceipt action', () => {
            const actions = getQuickActions();
            const viewReceipt = actions.find(a => a.id === 'zeroui.m05.quickFix.viewReceipt');
            expect(viewReceipt).toBeDefined();
            expect(viewReceipt?.label).toBe('View Receipt');
            expect(viewReceipt?.command).toBe('zeroui.m05.viewReceipt');
        });

        it('should return refresh action', () => {
            const actions = getQuickActions();
            const refresh = actions.find(a => a.id === 'zeroui.m05.quickFix.refresh');
            expect(refresh).toBeDefined();
            expect(refresh?.label).toBe('Refresh Detection Status');
            expect(refresh?.command).toBe('zeroui.detection.engine.core.refresh');
        });

        it('should return openDashboard action', () => {
            const actions = getQuickActions();
            const openDashboard = actions.find(a => a.id === 'zeroui.m05.quickFix.openDashboard');
            expect(openDashboard).toBeDefined();
            expect(openDashboard?.label).toBe('Open Dashboard');
            expect(openDashboard?.command).toBe('zeroui.detection.engine.core.showDashboard');
        });

        it('should return same actions on multiple calls', () => {
            const actions1 = getQuickActions();
            const actions2 = getQuickActions();
            expect(actions1).toEqual(actions2);
        });
    });

    describe('getQuickActionsLegacy', () => {
        it('should return array of quick actions', () => {
            const actions = getQuickActionsLegacy();
            expect(Array.isArray(actions)).toBe(true);
            expect(actions.length).toBe(4);
        });

        it('should return actions with id and label only', () => {
            const actions = getQuickActionsLegacy();
            actions.forEach(action => {
                expect(action).toHaveProperty('id');
                expect(action).toHaveProperty('label');
                expect(action).not.toHaveProperty('command');
            });
        });

        it('should map all actions from getQuickActions', () => {
            const legacyActions = getQuickActionsLegacy();
            const regularActions = getQuickActions();
            
            expect(legacyActions.length).toBe(regularActions.length);
            legacyActions.forEach((legacyAction, index) => {
                expect(legacyAction.id).toBe(regularActions[index].id);
                expect(legacyAction.label).toBe(regularActions[index].label);
            });
        });

        it('should return same actions on multiple calls', () => {
            const actions1 = getQuickActionsLegacy();
            const actions2 = getQuickActionsLegacy();
            expect(actions1).toEqual(actions2);
        });
    });
});

