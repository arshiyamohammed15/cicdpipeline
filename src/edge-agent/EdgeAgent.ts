import { AgentOrchestrator } from './core/AgentOrchestrator';
import { DelegationManager } from './core/DelegationManager';
import { ValidationCoordinator } from './core/ValidationCoordinator';
import { SecurityEnforcer } from './modules/security-enforcer/SecurityEnforcer';
import { CacheManager } from './modules/cache-manager/CacheManager';
import { HybridOrchestrator } from './modules/hybrid-orchestrator/HybridOrchestrator';
import { LocalInference } from './modules/local-inference/LocalInference';
import { ModelManager } from './modules/model-manager/ModelManager';
import { ResourceOptimizer } from './modules/resource-optimizer/ResourceOptimizer';

export class EdgeAgent {
    private orchestrator: AgentOrchestrator;
    private delegationManager: DelegationManager;
    private validationCoordinator: ValidationCoordinator;
    private securityEnforcer: SecurityEnforcer;
    private cacheManager: CacheManager;
    private hybridOrchestrator: HybridOrchestrator;
    private localInference: LocalInference;
    private modelManager: ModelManager;
    private resourceOptimizer: ResourceOptimizer;

    constructor() {
        this.initializeModules();
        this.setupCoordination();
    }

    private initializeModules(): void {
        // Initialize core components
        this.orchestrator = new AgentOrchestrator();
        this.delegationManager = new DelegationManager();
        this.validationCoordinator = new ValidationCoordinator();

        // Initialize infrastructure modules
        this.securityEnforcer = new SecurityEnforcer();
        this.cacheManager = new CacheManager();
        this.hybridOrchestrator = new HybridOrchestrator();
        this.localInference = new LocalInference();
        this.modelManager = new ModelManager();
        this.resourceOptimizer = new ResourceOptimizer();
    }

    private setupCoordination(): void {
        // Register modules with orchestrator
        this.orchestrator.registerModule('security', this.securityEnforcer);
        this.orchestrator.registerModule('cache', this.cacheManager);
        this.orchestrator.registerModule('hybrid', this.hybridOrchestrator);
        this.orchestrator.registerModule('inference', this.localInference);
        this.orchestrator.registerModule('models', this.modelManager);
        this.orchestrator.registerModule('resources', this.resourceOptimizer);

        // Setup delegation coordination
        this.delegationManager.setOrchestrator(this.orchestrator);
        this.validationCoordinator.setDelegationManager(this.delegationManager);
    }

    public async start(): Promise<void> {
        console.log('Edge Agent starting - Delegation and validation mode');
        
        // Initialize all modules
        await this.orchestrator.initialize();
        await this.delegationManager.initialize();
        await this.validationCoordinator.initialize();

        console.log('Edge Agent initialized - Ready for delegation and validation');
    }

    public async stop(): Promise<void> {
        console.log('Edge Agent stopping...');
        
        await this.orchestrator.shutdown();
        await this.delegationManager.shutdown();
        await this.validationCoordinator.shutdown();

        console.log('Edge Agent stopped');
    }

    // Delegation methods
    public async delegateTask(task: any): Promise<any> {
        return await this.delegationManager.delegate(task);
    }

    public async validateResult(result: any): Promise<boolean> {
        return await this.validationCoordinator.validate(result);
    }

    public async processLocally(data: any): Promise<any> {
        return await this.orchestrator.processLocally(data);
    }

    // Security and resource management
    public async enforceSecurity(policy: any): Promise<boolean> {
        return await this.securityEnforcer.enforce(policy);
    }

    public async optimizeResources(): Promise<void> {
        await this.resourceOptimizer.optimize();
    }
}
