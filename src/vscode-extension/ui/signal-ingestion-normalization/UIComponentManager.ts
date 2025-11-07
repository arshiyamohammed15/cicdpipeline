import { PlaceholderUIComponentManager } from '../common/PlaceholderUIComponentManager';

export class SignalIngestionNormalizationUIComponentManager extends PlaceholderUIComponentManager {
    constructor() {
        super('Signal Ingestion & Normalization');
    }

    public showSignalIngestionNormalizationDashboard(): void {
        this.showDashboard();
    }

    public updateSignalIngestionNormalizationData(payload: unknown): void {
        this.updateData(payload);
    }
}


