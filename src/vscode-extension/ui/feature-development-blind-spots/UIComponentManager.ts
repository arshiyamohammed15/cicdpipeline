import { PlaceholderUIComponentManager } from '../common/PlaceholderUIComponentManager';

export class FeatureDevelopmentBlindSpotsUIComponentManager extends PlaceholderUIComponentManager {
    constructor() {
        super('Feature Development Blind Spots');
    }

    public showFeatureDevelopmentBlindSpotsDashboard(): void {
        this.showDashboard();
    }

    public updateFeatureDevelopmentBlindSpotsData(payload: unknown): void {
        this.updateData(payload);
    }
}
