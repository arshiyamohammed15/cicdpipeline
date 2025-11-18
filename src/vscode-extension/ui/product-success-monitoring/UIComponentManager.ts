import { PlaceholderUIComponentManager } from '../common/PlaceholderUIComponentManager';

export class ProductSuccessMonitoringUIComponentManager extends PlaceholderUIComponentManager {
    constructor() {
        super('Product Success Monitoring');
    }

    public showProductSuccessMonitoringDashboard(): void {
        this.showDashboard();
    }

    public updateProductSuccessMonitoringData(payload: unknown): void {
        this.updateData(payload);
    }
}
