/**
 * Minimal no-op implementation for UI component managers that have not yet
 * been fully built. The extension relies on these classes existing so command
 * wiring and view registration compile cleanly, even though the actual UI is
 * still to be implemented.
 */
export class PlaceholderUIComponentManager {
    private lastPayload: unknown = undefined;

    protected constructor(private readonly moduleDisplayName: string) {}

    protected showDashboard(): void {
        console.log(`[${this.moduleDisplayName}] showDashboard`);
    }

    protected updateData(payload: unknown): void {
        this.lastPayload = payload;
        console.log(`[${this.moduleDisplayName}] updateData`, payload);
    }

    public dispose(): void {
        this.lastPayload = undefined;
    }
}


