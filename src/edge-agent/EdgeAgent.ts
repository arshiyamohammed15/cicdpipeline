import { AgentOrchestrator } from './core/AgentOrchestrator';
import { DelegationManager } from './core/DelegationManager';
import { ValidationCoordinator } from './core/ValidationCoordinator';
import { SecurityEnforcer } from './modules/security-enforcer/SecurityEnforcer';
import { CacheManager } from './modules/cache-manager/CacheManager';
import { HybridOrchestrator } from './modules/hybrid-orchestrator/HybridOrchestrator';
import { LocalInference } from './modules/local-inference/LocalInference';
import { ModelManager } from './modules/model-manager/ModelManager';
import { ResourceOptimizer } from './modules/resource-optimizer/ResourceOptimizer';
import { ReceiptStorageService } from './shared/storage/ReceiptStorageService';
import { ReceiptGenerator } from './shared/storage/ReceiptGenerator';
import { PolicyStorageService } from './shared/storage/PolicyStorageService';

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
    private receiptStorage: ReceiptStorageService;
    private receiptGenerator: ReceiptGenerator;
    private policyStorage: PolicyStorageService;

    constructor(zuRoot?: string) {
        // Initialize storage services
        this.receiptStorage = new ReceiptStorageService(zuRoot);
        this.receiptGenerator = new ReceiptGenerator();
        this.policyStorage = new PolicyStorageService(zuRoot);

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

    /**
     * Process task and generate receipt
     * 
     * @param task Task to process
     * @param repoId Repository identifier
     * @returns Promise<{result: any, receiptPath: string}> Processing result and receipt storage path
     */
    public async processTaskWithReceipt(task: any, repoId: string): Promise<{result: any, receiptPath: string}> {
        // Process task through delegation
        const result = await this.delegateTask(task);

        // Validate result
        const isValid = await this.validateResult(result);

        // Generate receipt
        const receipt = this.receiptGenerator.generateDecisionReceipt(
            'edge-agent',
            [], // TODO: Get policy version IDs from policy storage
            '', // TODO: Get snapshot hash
            task.data || {},
            {
                status: isValid ? 'pass' : 'warn',
                rationale: isValid ? 'Task processed successfully' : 'Validation warnings detected',
                badges: isValid ? ['processed', 'validated'] : ['processed']
            },
            [], // Evidence handles
            {
                repo_id: repoId
            },
            !isValid
        );

        // Store receipt
        const receiptPath = await this.receiptStorage.storeDecisionReceipt(receipt, repoId);

        return {
            result: result,
            receiptPath: receiptPath
        };
    }

    // Security and resource management
    public async enforceSecurity(policy: any): Promise<boolean> {
        return await this.securityEnforcer.enforce(policy);
    }

    public async optimizeResources(): Promise<void> {
        // ResourceOptimizer uses delegate() method, not optimize()
        // This method is kept for API compatibility but delegates to the resource optimizer
        await this.resourceOptimizer.delegate({
            id: 'resource-optimization',
            type: 'resource-optimizer',
            priority: 'medium',
            data: {},
            requirements: {}
        });
    }

    /**
     * Get receipt storage service (for external access)
     */
    public getReceiptStorage(): ReceiptStorageService {
        return this.receiptStorage;
    }

    /**
     * Get receipt generator (for external access)
     */
    public getReceiptGenerator(): ReceiptGenerator {
        return this.receiptGenerator;
    }

    /**
     * Get policy storage service (for external access)
     */
    public getPolicyStorage(): PolicyStorageService {
        return this.policyStorage;
    }
}
