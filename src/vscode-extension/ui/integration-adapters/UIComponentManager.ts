import { PlaceholderUIComponentManager } from '../common/PlaceholderUIComponentManager';

export class IntegrationAdaptersUIComponentManager extends PlaceholderUIComponentManager {
    constructor() {
        super('Integration Adapters');
    }

    public showIntegrationAdaptersDashboard(): void {
        this.showDashboard();
    }

    public updateIntegrationAdaptersData(payload: unknown): void {
        this.updateData(payload);
    }
}


