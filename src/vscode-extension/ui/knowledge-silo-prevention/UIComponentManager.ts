import { PlaceholderUIComponentManager } from '../common/PlaceholderUIComponentManager';

export class KnowledgeSiloPreventionUIComponentManager extends PlaceholderUIComponentManager {
    constructor() {
        super('Knowledge Silo Prevention');
    }

    public showKnowledgeSiloPreventionDashboard(): void {
        this.showDashboard();
    }

    public updateKnowledgeSiloPreventionData(payload: unknown): void {
        this.updateData(payload);
    }
}
