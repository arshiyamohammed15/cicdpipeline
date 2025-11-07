import { PlaceholderUIComponentManager } from '../common/PlaceholderUIComponentManager';

export class DetectionEngineCoreUIComponentManager extends PlaceholderUIComponentManager {
    constructor() {
        super('Detection Engine Core');
    }

    public showDetectionEngineCoreDashboard(): void {
        this.showDashboard();
    }

    public updateDetectionEngineCoreData(payload: unknown): void {
        this.updateData(payload);
    }
}

