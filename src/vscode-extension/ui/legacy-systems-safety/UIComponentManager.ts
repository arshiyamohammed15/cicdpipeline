import { PlaceholderUIComponentManager } from '../common/PlaceholderUIComponentManager';

export class LegacySystemsSafetyUIComponentManager extends PlaceholderUIComponentManager {
    constructor() {
        super('Legacy Systems Safety');
    }

    public showLegacySystemsSafetyDashboard(): void {
        this.showDashboard();
    }

    public updateLegacySystemsSafetyData(payload: unknown): void {
        this.updateData(payload);
    }
}


