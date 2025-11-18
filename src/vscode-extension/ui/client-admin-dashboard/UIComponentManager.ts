import { PlaceholderUIComponentManager } from '../common/PlaceholderUIComponentManager';

export class ClientAdminDashboardUIComponentManager extends PlaceholderUIComponentManager {
    constructor() {
        super('Client Admin Dashboard');
    }

    public showClientAdminDashboardDashboard(): void {
        this.showDashboard();
    }

    public updateClientAdminDashboardData(payload: unknown): void {
        this.updateData(payload);
    }
}
