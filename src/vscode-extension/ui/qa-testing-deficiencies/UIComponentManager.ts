export class QATestingDeficienciesUIComponentManager {
    private lastSnapshot: unknown;

    constructor() {
        this.lastSnapshot = undefined;
    }

    public showQATestingDeficienciesDashboard(): void {
        console.log('[QA Testing Deficiencies] showDashboard');
    }

    public updateQATestingDeficienciesData(payload: unknown): void {
        this.lastSnapshot = payload;
        console.log('[QA Testing Deficiencies] updateData', payload);
    }

    public dispose(): void {
        this.lastSnapshot = undefined;
    }
}
