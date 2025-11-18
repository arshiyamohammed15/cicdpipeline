import { PlaceholderUIComponentManager } from '../common/PlaceholderUIComponentManager';

export class GoldStandardsUIComponentManager extends PlaceholderUIComponentManager {
    constructor() {
        super('Gold Standards');
    }

    public showGoldStandardsDashboard(): void {
        this.showDashboard();
    }

    public updateGoldStandardsData(payload: unknown): void {
        this.updateData(payload);
    }
}
