import { PlaceholderUIComponentManager } from '../common/PlaceholderUIComponentManager';

export class MergeConflictsDelaysUIComponentManager extends PlaceholderUIComponentManager {
    constructor() {
        super('Merge Conflicts & Delays');
    }

    public showMergeConflictsDelaysDashboard(): void {
        this.showDashboard();
    }

    public updateMergeConflictsDelaysData(payload: unknown): void {
        this.updateData(payload);
    }
}


