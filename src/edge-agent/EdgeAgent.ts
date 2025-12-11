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
import { ReceiptGenerator, ReceiptGeneratorOptions } from './shared/storage/ReceiptGenerator';
import { PolicyStorageService } from './shared/storage/PolicyStorageService';
import { HeartbeatEmitter } from './shared/health/HeartbeatEmitter';
import { DelegationTask, DelegationResult } from './interfaces/core/DelegationInterface';
import { AIAssistanceDetector, AIDetectionSignals, ActorType } from './shared/ai-detection/AIAssistanceDetector';
import { DataCategory, DataCategoryClassifier, DataClassificationSignals } from './shared/storage/DataCategoryClassifier';

const resolvePlane = (value?: string): 'Laptop' | 'Tenant' | 'Product' | 'Shared' => {
    const allowed = new Set(['Laptop', 'Tenant', 'Product', 'Shared']);
    if (value && allowed.has(value)) {
        return value as 'Laptop' | 'Tenant' | 'Product' | 'Shared';
    }
    return 'Laptop';
};

const resolveEnvironment = (value?: string): 'dev' | 'test' | 'stage' | 'prod' => {
    const allowed = new Set(['dev', 'test', 'stage', 'prod']);
    if (value && allowed.has(value)) {
        return value as 'dev' | 'test' | 'stage' | 'prod';
    }
    return 'dev';
};

export interface EdgeAgentOptions {
    signingKey?: string | Buffer;
    signingKeyPath?: string;
    signingKeyId?: string;
}

export class EdgeAgent {
    private orchestrator!: AgentOrchestrator;
    private delegationManager!: DelegationManager;
    private validationCoordinator!: ValidationCoordinator;
    private securityEnforcer!: SecurityEnforcer;
    private cacheManager!: CacheManager;
    private hybridOrchestrator!: HybridOrchestrator;
    private localInference!: LocalInference;
    private modelManager!: ModelManager;
    private resourceOptimizer!: ResourceOptimizer;
    private receiptStorage: ReceiptStorageService;
    private receiptGenerator: ReceiptGenerator;
    private policyStorage: PolicyStorageService;
    private heartbeatEmitter: HeartbeatEmitter;
    private aiDetector: AIAssistanceDetector;
    private dataClassifier: DataCategoryClassifier;

    constructor(zuRoot?: string, options: EdgeAgentOptions = {}) {
        // Initialize storage services
        this.receiptStorage = new ReceiptStorageService(zuRoot);
        const generatorOptions: ReceiptGeneratorOptions = {};
        if (options.signingKey !== undefined) {
            generatorOptions.privateKey = options.signingKey;
        }
        if (options.signingKeyPath) {
            generatorOptions.privateKeyPath = options.signingKeyPath;
        }
        if (options.signingKeyId) {
            generatorOptions.keyId = options.signingKeyId;
        }
        this.receiptGenerator = new ReceiptGenerator(generatorOptions);
        this.policyStorage = new PolicyStorageService(zuRoot);
        this.aiDetector = new AIAssistanceDetector();
        this.dataClassifier = new DataCategoryClassifier();

        this.heartbeatEmitter = new HeartbeatEmitter({
            componentId: process.env.HEALTH_RELIABILITY_MONITORING_COMPONENT_ID ?? 'edge-agent',
            plane: resolvePlane(process.env.HEALTH_RELIABILITY_MONITORING_PLANE),
            environment: resolveEnvironment(process.env.HEALTH_RELIABILITY_MONITORING_ENVIRONMENT),
            tenantId: process.env.HEALTH_RELIABILITY_MONITORING_TENANT_ID,
            endpoint: process.env.HEALTH_RELIABILITY_MONITORING_HEARTBEAT_ENDPOINT,
            intervalMs: process.env.HEALTH_RELIABILITY_MONITORING_HEARTBEAT_INTERVAL_MS
                ? Number(process.env.HEALTH_RELIABILITY_MONITORING_HEARTBEAT_INTERVAL_MS)
                : undefined
        });

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
        this.heartbeatEmitter.start();
    }

    public async stop(): Promise<void> {
        console.log('Edge Agent stopping...');

        await this.orchestrator.shutdown();
        await this.delegationManager.shutdown();
        await this.validationCoordinator.shutdown();
        this.heartbeatEmitter.stop();

        console.log('Edge Agent stopped');
    }

    // Delegation methods
    public async delegateTask(task: DelegationTask): Promise<DelegationResult> {
        return await this.delegationManager.delegate(task);
    }

    public async validateResult(result: DelegationResult): Promise<boolean> {
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
     * @returns Promise<{result: DelegationResult, receiptPath: string}> Processing result and receipt storage path
     */
    public async processTaskWithReceipt(
        task: DelegationTask,
        repoId: string,
        options?: {
            context?: {
                surface?: 'ide' | 'pr' | 'ci';
                branch?: string;
                commit?: string;
                pr_id?: string;
            };
            override?: {
                reason: string;
                approver: string;
                timestamp: string;
                override_id?: string;
            };
            dataCategory?: DataCategory;
            classificationSignals?: DataClassificationSignals;
            actorType?: ActorType;
            aiSignals?: AIDetectionSignals;
            evaluationPoint?: 'pre-commit' | 'pre-merge' | 'pre-deploy' | 'post-deploy';
        }
    ): Promise<{result: DelegationResult, receiptPath: string}> {
        // Process task through delegation
        const result = await this.delegateTask(task);

        // Validate result
        const isValid = await this.validateResult(result);

        // Get active policy information from policy storage
        const policyInfo = await this.policyStorage.getActivePolicyInfo(['default']);

        // Generate receipt with policy information
        const evaluationPoint = options?.evaluationPoint ?? this.normalizeEvaluationPoint((task as any)?.data?.context);
        const context = options?.context ?? this.extractContext(task);
        const actorType = this.resolveActorType(task, options);
        const dataCategory = this.resolveDataCategory(task, options);

        const receipt = this.receiptGenerator.generateDecisionReceipt(
            'edge-agent',
            policyInfo.policy_version_ids,
            policyInfo.snapshot_hash,
            task.data || {},
            {
                status: isValid ? 'pass' : 'warn',
                rationale: isValid ? 'Task processed successfully' : 'Validation warnings detected',
                badges: isValid ? ['processed', 'validated'] : ['processed']
            },
            [], // Evidence handles
            {
                repo_id: repoId,
                ...(actorType ? { type: actorType } : {})
            },
            !isValid,
            evaluationPoint,
            context,
            options?.override,
            dataCategory
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

    private normalizeEvaluationPoint(value: unknown): 'pre-commit' | 'pre-merge' | 'pre-deploy' | 'post-deploy' {
        const allowed = new Set(['pre-commit', 'pre-merge', 'pre-deploy', 'post-deploy']);
        if (typeof value === 'string' && allowed.has(value)) {
            return value as any;
        }
        return 'pre-commit';
    }

    private extractContext(task: DelegationTask): {
        surface?: 'ide' | 'pr' | 'ci';
        branch?: string;
        commit?: string;
        pr_id?: string;
    } | undefined {
        const data = (task as any)?.data ?? {};
        const surface = typeof data.surface === 'string' ? data.surface : undefined;
        const branch = typeof data.branch === 'string' ? data.branch : undefined;
        const commit = typeof data.commit === 'string' ? data.commit : undefined;
        const pr_id = typeof data.pr_id === 'string' ? data.pr_id : undefined;

        if (!surface && !branch && !commit && !pr_id) {
            return undefined;
        }

        return { surface, branch, commit, pr_id };
    }

    private resolveActorType(
        task: DelegationTask,
        options?: {
            actorType?: ActorType;
            aiSignals?: AIDetectionSignals;
        }
    ): ActorType | undefined {
        const data = (task as any)?.data ?? {};
        const hint = options?.actorType ?? (typeof data.actor_type === 'string' ? data.actor_type : undefined);

        return this.aiDetector.detect({
            actorTypeHint: hint as ActorType | undefined,
            ...(options?.aiSignals ?? {})
        });
    }

    private resolveDataCategory(
        task: DelegationTask,
        options?: {
            dataCategory?: DataCategory;
            classificationSignals?: DataClassificationSignals;
        }
    ): DataCategory | undefined {
        const data = (task as any)?.data ?? {};
        const explicitCategory = options?.dataCategory ?? (typeof data.data_category === 'string' ? data.data_category : undefined);
        const containsSensitiveData = Boolean(data.contains_sensitive_data);
        const containsSecrets = Boolean(data.contains_secrets);
        const piiDetected = Boolean(data.pii_detected);

        return this.dataClassifier.classify({
            explicitCategory,
            containsSensitiveData,
            containsSecrets,
            piiDetected,
            ...(options?.classificationSignals ?? {})
        });
    }
}
