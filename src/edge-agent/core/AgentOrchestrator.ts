import { DelegationInterface } from '../interfaces/core/DelegationInterface';
import { ValidationInterface } from '../interfaces/core/ValidationInterface';

export class AgentOrchestrator {
    private modules: Map<string, any> = new Map();
    private isInitialized: boolean = false;

    public registerModule(name: string, module: any): void {
        this.modules.set(name, module);
        console.log(`Registered module: ${name}`);
    }

    public async initialize(): Promise<void> {
        if (this.isInitialized) {
            return;
        }

        console.log('Initializing Edge Agent modules...');

        // Initialize all registered modules
        for (const [name, module] of this.modules) {
            if (module.initialize && typeof module.initialize === 'function') {
                await module.initialize();
                console.log(`Module ${name} initialized`);
            }
        }

        this.isInitialized = true;
        console.log('All Edge Agent modules initialized');
    }

    public async shutdown(): Promise<void> {
        console.log('Shutting down Edge Agent modules...');

        for (const [name, module] of this.modules) {
            if (module.shutdown && typeof module.shutdown === 'function') {
                await module.shutdown();
                console.log(`Module ${name} shut down`);
            }
        }

        this.isInitialized = false;
        console.log('All Edge Agent modules shut down');
    }

    public async processLocally(data: any): Promise<any> {
        if (!this.isInitialized) {
            throw new Error('Agent not initialized');
        }

        console.log('Processing data locally in Edge Agent');

        // Delegate to appropriate modules based on data type
        const result = await this.delegateProcessing(data);

        return result;
    }

    private async delegateProcessing(data: any): Promise<any> {
        // Determine which modules to use based on data characteristics
        const processingPipeline = this.determineProcessingPipeline(data);

        let result = data;
        for (const moduleName of processingPipeline) {
            const module = this.modules.get(moduleName);
            if (module && module.process) {
                result = await module.process(result);
                console.log(`Processed through module: ${moduleName}`);
            }
        }

        return result;
    }

    private determineProcessingPipeline(data: any): string[] {
        // Determine processing pipeline based on data characteristics
        const pipeline: string[] = [];

        // Security enforcement first
        pipeline.push('security');

        // Cache check
        pipeline.push('cache');

        // Local inference if needed
        if (this.requiresInference(data)) {
            pipeline.push('inference');
        }

        // Model management if needed
        if (this.requiresModelManagement(data)) {
            pipeline.push('models');
        }

        // Resource optimization
        pipeline.push('resources');

        return pipeline;
    }

    private requiresInference(data: any): boolean {
        // Determine if data requires local inference
        return data.type === 'inference' || data.requiresInference === true;
    }

    private requiresModelManagement(data: any): boolean {
        // Determine if data requires model management
        return data.type === 'model' || data.requiresModelManagement === true;
    }

    public getModule(name: string): any {
        return this.modules.get(name);
    }

    public getAvailableModules(): string[] {
        return Array.from(this.modules.keys());
    }
}
