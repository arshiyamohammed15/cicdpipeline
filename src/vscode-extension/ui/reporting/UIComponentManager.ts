import { PlaceholderUIComponentManager } from '../common/PlaceholderUIComponentManager';

export class ReportingUIComponentManager extends PlaceholderUIComponentManager {
    constructor() {
        super('Reporting');
    }

    public showReportingDashboard(): void {
        this.showDashboard();
    }

    public updateReportingData(payload: unknown): void {
        this.updateData(payload);
    }
}


