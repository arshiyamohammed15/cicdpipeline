import { PlaceholderUIComponentManager } from '../common/PlaceholderUIComponentManager';

export class ReleaseFailuresRollbacksUIComponentManager extends PlaceholderUIComponentManager {
    constructor() {
        super('Release Failures & Rollbacks');
    }

    public showReleaseFailuresRollbacksDashboard(): void {
        this.showDashboard();
    }

    public updateReleaseFailuresRollbacksData(payload: unknown): void {
        this.updateData(payload);
    }
}
