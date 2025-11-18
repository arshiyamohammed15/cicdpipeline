import { PlaceholderUIComponentManager } from '../common/PlaceholderUIComponentManager';

export class TechnicalDebtAccumulationUIComponentManager extends PlaceholderUIComponentManager {
    constructor() {
        super('Technical Debt Accumulation');
    }

    public showTechnicalDebtAccumulationDashboard(): void {
        this.showDashboard();
    }

    public updateTechnicalDebtAccumulationData(payload: unknown): void {
        this.updateData(payload);
    }
}
