import { PlaceholderUIComponentManager } from '../common/PlaceholderUIComponentManager';

export class CrossCuttingConcernsUIComponentManager extends PlaceholderUIComponentManager {
    constructor() {
        super('Cross Cutting Concerns');
    }

    public showCrossCuttingConcernsDashboard(): void {
        this.showDashboard();
    }

    public updateCrossCuttingConcernsData(payload: unknown): void {
        this.updateData(payload);
    }
}
