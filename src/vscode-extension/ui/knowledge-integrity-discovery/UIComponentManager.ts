import { PlaceholderUIComponentManager } from '../common/PlaceholderUIComponentManager';

export class KnowledgeIntegrityDiscoveryUIComponentManager extends PlaceholderUIComponentManager {
    constructor() {
        super('Knowledge Integrity & Discovery');
    }

    public showKnowledgeIntegrityDiscoveryDashboard(): void {
        this.showDashboard();
    }

    public updateKnowledgeIntegrityDiscoveryData(payload: unknown): void {
        this.updateData(payload);
    }
}


