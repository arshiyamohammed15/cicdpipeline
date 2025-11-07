import { PlaceholderUIComponentManager } from '../common/PlaceholderUIComponentManager';

export class MonitoringObservabilityGapsUIComponentManager extends PlaceholderUIComponentManager {
    constructor() {
        super('Monitoring & Observability Gaps');
    }

    public showMonitoringObservabilityGapsDashboard(): void {
        this.showDashboard();
    }

    public updateMonitoringObservabilityGapsData(payload: unknown): void {
        this.updateData(payload);
    }
}


