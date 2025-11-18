import { PlaceholderUIComponentManager } from '../common/PlaceholderUIComponentManager';

export class RoiDashboardUIComponentManager extends PlaceholderUIComponentManager {
    constructor() {
        super('ROI Dashboard');
    }

    public showRoiDashboardDashboard(): void {
        this.showDashboard();
    }

    public updateRoiDashboardData(payload: unknown): void {
        this.updateData(payload);
    }
}
