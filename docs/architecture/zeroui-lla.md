# ZeroUI 2.0 Low-Level Architecture (LLA) v0.4

## Executive Summary

ZeroUI 2.0 implements a **comprehensive low-level architecture** with detailed implementation patterns, data flow specifications, and technical integration points across the three-tier system. This document provides the technical implementation details for the high-level architecture.

## Technical Architecture Overview

### 🔧 Implementation Patterns

#### **VS Code Extension Implementation**
- **Language**: TypeScript
- **Framework**: VS Code Extension API
- **Pattern**: Receipt-driven UI rendering
- **Architecture**: Presentation-only with modular components

#### **Edge Agent Implementation**
- **Language**: TypeScript
- **Pattern**: Delegation and validation
- **Architecture**: Local processing coordination
- **Integration**: Module orchestration and task delegation

#### **Cloud Services Implementation**
- **Language**: Python/FastAPI
- **Pattern**: Service-oriented architecture
- **Architecture**: Microservices with clear boundaries
- **Integration**: RESTful APIs and service communication

## VS Code Extension Technical Details

### 📁 File Structure Implementation
```
src/vscode-extension/
├── extension.ts                    # Main entry point
├── package.json                   # Extension manifest
├── tsconfig.json                  # TypeScript configuration
├── .vscodeignore                  # Build ignore patterns
├── shared/
│   └── receipt-parser/
│       └── ReceiptParser.ts       # Receipt parsing logic
├── modules/                       # Module logic (manifest-based)
│   ├── m01-mmm-engine/
│   │   ├── module.manifest.json
│   │   ├── index.ts               # export registerModule()
│   │   ├── commands.ts
│   │   ├── providers/
│   │   ├── views/
│   │   └── actions/
│   └── [m02-m20 other modules...]
└── ui/                            # UI components (presentation-only)
    ├── [Core UI Components]        # 6 core UI components
    └── [20 Module UI Components]  # Module-specific UI
```

### 🔧 Core Implementation Patterns

#### **Extension.ts (Main Entry Point)**
```typescript
export function activate(context: vscode.ExtensionContext) {
    // Initialize core UI managers
    const statusBarManager = new StatusBarManager();
    const problemsPanelManager = new ProblemsPanelManager();
    const decisionCardManager = new DecisionCardManager();
    const evidenceDrawerManager = new EvidenceDrawerManager();
    const toastManager = new ToastManager();
    const receiptViewerManager = new ReceiptViewerManager();
    const receiptParser = new ReceiptParser();

    // Initialize UI Module Extension Interfaces
    const mmmEngineInterface = new MMMEngineExtensionInterface();
    // ... 19 other module interfaces

    // Register core commands
    const showDecisionCard = vscode.commands.registerCommand('zeroui.showDecisionCard', () => {
        decisionCardManager.showDecisionCard();
    });

    // Register UI Module commands and views
    mmmEngineInterface.registerCommands(context);
    mmmEngineInterface.registerViews(context);
    // ... register all module interfaces
}
```

#### **UIComponent.ts Pattern**
```typescript
export class MMMEngineUIComponent {
    public renderDashboard(data?: MMMEngineData): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZeroUI MMM Engine Dashboard</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 20px;
        }
        // ... VS Code theme integration
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="dashboard-header">ZeroUI MMM Engine Dashboard</div>
        <div class="dashboard-content">
            ${data ? this.renderMMMEngineContent(data) : 'No MMM Engine data available'}
        </div>
    </div>
</body>
</html>`;
    }
}
```

#### **UIComponentManager.ts Pattern**
```typescript
export class MMMEngineUIComponentManager implements vscode.Disposable {
    private webviewPanel: vscode.WebviewPanel | undefined;
    private uiComponent: MMMEngineUIComponent;

    constructor() {
        this.uiComponent = new MMMEngineUIComponent();
    }

    public showMMMEngineDashboard(data?: MMMEngineData): void {
        if (this.webviewPanel) {
            this.webviewPanel.reveal(vscode.ViewColumn.One);
            return;
        }

        this.webviewPanel = vscode.window.createWebviewPanel(
            'zerouiMMMEngine',
            'ZeroUI MMM Engine Dashboard',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        this.webviewPanel.webview.html = this.uiComponent.renderDashboard(data);
    }
}
```

#### **ExtensionInterface.ts Pattern**
```typescript
export class MMMEngineExtensionInterface implements vscode.Disposable {
    private uiManager: MMMEngineUIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new MMMEngineUIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const showMMMDashboard = vscode.commands.registerCommand('zeroui.mmm.showDashboard', () => {
            this.uiManager.showMMMEngineDashboard();
        });

        const refreshMMMData = vscode.commands.registerCommand('zeroui.mmm.refresh', () => {
            this.uiManager.updateMMMEngineData({} as any);
        });

        const exportMMMReport = vscode.commands.registerCommand('zeroui.mmm.exportReport', () => {
            this.exportMMMReport();
        });

        this.disposables.push(showMMMDashboard, refreshMMMData, exportMMMReport);
        context.subscriptions.push(...this.disposables);
    }
}
```

### 📊 Receipt Processing Implementation
```typescript
export class ReceiptParser {
    public parseDecisionReceipt(receiptJson: string): DecisionReceipt | null {
        try {
            const receipt = JSON.parse(receiptJson);
            return this.validateDecisionReceipt(receipt) ? receipt : null;
        } catch (error) {
            console.error('Failed to parse decision receipt:', error);
            return null;
        }
    }

    private validateDecisionReceipt(receipt: any): receipt is DecisionReceipt {
        return (
            typeof receipt.receipt_id === 'string' &&
            typeof receipt.gate_id === 'string' &&
            Array.isArray(receipt.policy_version_ids) &&
            typeof receipt.snapshot_hash === 'string' &&
            typeof receipt.timestamp_utc === 'string' &&
            typeof receipt.timestamp_monotonic_ms === 'number' &&
            typeof receipt.inputs === 'object' &&
            typeof receipt.decision === 'object' &&
            typeof receipt.decision.status === 'string' &&
            typeof receipt.decision.rationale === 'string' &&
            Array.isArray(receipt.decision.badges) &&
            Array.isArray(receipt.evidence_handles) &&
            typeof receipt.actor === 'object' &&
            typeof receipt.actor.repo_id === 'string' &&
            typeof receipt.degraded === 'boolean' &&
            typeof receipt.signature === 'string'
        );
    }
}
```

## Edge Agent Technical Details

### 📁 File Structure Implementation
```
src/edge-agent/
├── EdgeAgent.ts                    # Main orchestrator
├── core/
│   ├── AgentOrchestrator.ts        # Module coordination
│   ├── DelegationManager.ts        # Task delegation
│   └── ValidationCoordinator.ts    # Result validation
├── interfaces/
│   └── core/
│       ├── DelegationInterface.ts # Delegation contracts
│       └── ValidationInterface.ts # Validation contracts
└── modules/
    ├── security-enforcer/          # Security delegation
    ├── cache-manager/              # Cache operations
    ├── hybrid-orchestrator/        # Hybrid processing
    ├── local-inference/            # Local inference
    ├── model-manager/              # Model management
    └── resource-optimizer/         # Resource optimization
```

### 🔧 Core Implementation Patterns

#### **EdgeAgent.ts (Main Orchestrator)**
```typescript
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

    public async start(): Promise<void> {
        console.log('Edge Agent starting - Delegation and validation mode');

        // Initialize all modules
        await this.orchestrator.initialize();
        await this.delegationManager.initialize();
        await this.validationCoordinator.initialize();

        console.log('Edge Agent initialized - Ready for delegation and validation');
    }
}
```

#### **DelegationInterface.ts (Contract)**
```typescript
export interface DelegationInterface {
    delegate(task: any): Promise<any>;
    canHandle(task: any): boolean;
    getCapabilities(): string[];
    getStatus(): ModuleStatus;
}

export interface DelegationTask {
    id: string;
    type: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
    data: any;
    requirements: {
        security?: boolean;
        performance?: boolean;
        compliance?: boolean;
    };
    timeout?: number;
    retryCount?: number;
}

export interface DelegationResult {
    taskId: string;
    success: boolean;
    result?: any;
    error?: string;
    processingTime: number;
    metadata: {
        module: string;
        timestamp: Date;
        securityValidated: boolean;
        dataIntegrity: boolean;
        performanceMetrics: {
            latency: number;
            memoryUsage: number;
            cpuUsage: number;
        };
    };
}
```

#### **Module Implementation Pattern**
```typescript
export class SecurityEnforcer implements DelegationInterface {
    private isActive: boolean = false;
    private isHealthy: boolean = true;
    private tasksProcessed: number = 0;
    private totalLatency: number = 0;
    private errorCount: number = 0;

    public async delegate(task: DelegationTask): Promise<DelegationResult> {
        const startTime = Date.now();

        try {
            console.log(`Security Enforcer processing task: ${task.id}`);

            // Enforce security policies
            const securityResult = await this.enforceSecurityPolicies(task);

            const processingTime = Date.now() - startTime;
            this.tasksProcessed++;
            this.totalLatency += processingTime;

            const result: DelegationResult = {
                taskId: task.id,
                success: true,
                result: securityResult,
                processingTime,
                metadata: {
                    module: 'security-enforcer',
                    timestamp: new Date(),
                    securityValidated: true,
                    dataIntegrity: true,
                    performanceMetrics: {
                        latency: processingTime,
                        memoryUsage: process.memoryUsage().heapUsed,
                        cpuUsage: 0
                    }
                }
            };

            return result;
        } catch (error) {
            // Error handling implementation
        }
    }

    public canHandle(task: DelegationTask): boolean {
        return task.type === 'security' ||
               task.requirements?.security === true ||
               task.priority === 'critical';
    }

    public getCapabilities(): string[] {
        return [
            'security-policy-enforcement',
            'data-encryption',
            'access-control',
            'audit-logging',
            'threat-detection'
        ];
    }
}
```

## Cloud Services Technical Details

### 📁 Service Structure Implementation
```
src/cloud-services/
├── client-services/                # 13 business logic modules
│   ├── mmm-engine/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app
│   │   ├── routes.py               # API routes
│   │   ├── services.py             # Business logic
│   │   ├── models.py               # Pydantic models
│   │   └── middleware.py           # Custom middleware
│   ├── cross-cutting-concerns/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app
│   │   ├── routes.py               # API routes
│   │   ├── services.py             # Business logic
│   │   └── models.py               # Pydantic models
│   └── [11 other modules...]
├── product-services/               # 7 business logic modules
│   ├── detection-engine-core/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app
│   │   ├── routes.py               # API routes
│   │   ├── services.py             # Business logic
│   │   └── models.py               # Pydantic models
│   └── [6 other modules...]
├── shared-services/                # 1 business logic module
│   └── qa-testing-deficiencies/
│       ├── __init__.py
│       ├── main.py
│       ├── routes.py
│       ├── services.py
│       └── models.py
├── adapter-gateway/                # Infrastructure service
│   ├── __init__.py
│   ├── main.py
│   └── routes.py
├── evidence-service/               # Infrastructure service
│   ├── __init__.py
│   ├── main.py
│   └── routes.py
└── policy-service/                 # Infrastructure service
    ├── __init__.py
    ├── main.py
    └── routes.py
```

### 🔧 Service Implementation Patterns

#### **FastAPI App Pattern (main.py)**
```python
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from .models import HealthResponse

app = FastAPI(
    title="ZeroUI MMM Engine Service",
    version="2.0.0",
    description="MMM Engine business logic service"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1", tags=["mmm-engine"])

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", timestamp=datetime.utcnow())
```

#### **Router Pattern (routes.py)**
```python
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from .models import ProcessDataRequest, ProcessDataResponse
from .services import MMMEngineService

router = APIRouter()

def get_service() -> MMMEngineService:
    return MMMEngineService()

@router.post("/process", response_model=ProcessDataResponse)
async def process_data(
    request: ProcessDataRequest,
    service: MMMEngineService = Depends(get_service)
) -> ProcessDataResponse:
    try:
        result = await service.process_data(request)
        return ProcessDataResponse(
            success=True,
            data=result,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
```

#### **Service Pattern (services.py)**
```python
from typing import Optional
from .models import ProcessDataRequest, ProcessDataResponse
from .repositories import DataRepository
from .validators import ValidationService

class MMMEngineService:
    def __init__(
        self,
        data_repository: Optional[DataRepository] = None,
        validation_service: Optional[ValidationService] = None
    ):
        self.data_repository = data_repository or DataRepository()
        self.validation_service = validation_service or ValidationService()

    async def process_data(self, request: ProcessDataRequest) -> dict:
        # Validate input data
        await self.validation_service.validate(request)

        # Process data
        result = await self.data_repository.process(request)

        # Return processed result
        return result
```

#### **Pydantic Model Pattern (models.py)**
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class MMMEngineMetrics(BaseModel):
    collected: int = Field(ge=0, description="Number of metrics collected")
    processed: int = Field(ge=0, description="Number of metrics processed")
    errors: int = Field(ge=0, description="Number of errors encountered")

class MMMEngineData(BaseModel):
    id: str = Field(..., description="Unique identifier")
    metrics: MMMEngineMetrics = Field(..., description="Engine metrics")
    status: str = Field(..., pattern="^(active|inactive|error)$", description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")

class ProcessDataRequest(BaseModel):
    data: Dict[str, Any] = Field(..., description="Input data to process")
    options: Optional[Dict[str, Any]] = Field(None, description="Processing options")

class ProcessDataResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Processed data")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: str = Field(..., description="Response timestamp")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
```

## Data Flow Implementation

### 🔄 Receipt Flow
1. **Edge Agent** processes data locally
2. **Receipt Generation** creates signed receipts
3. **VS Code Extension** receives receipts
4. **Receipt Parser** validates and parses receipts
5. **UI Components** render dashboards from receipt data

### 📊 Processing Pipeline
```typescript
// Edge Agent Processing Pipeline
const pipeline = [
    'security',      // Security enforcement first
    'cache',         // Cache operations
    'inference',     // Local inference if needed
    'models',        // Model management if needed
    'resources'      // Resource optimization
];

// Process through pipeline
for (const moduleName of pipeline) {
    const module = this.modules.get(moduleName);
    if (module && module.process) {
        result = await module.process(result);
    }
}
```

### 🔒 Security Implementation
```typescript
// Security enforcement
export class SecurityEnforcer {
    async enforceSecurityPolicies(task: DelegationTask): Promise<SecurityResult> {
        return {
            securityValidated: true,
            policiesApplied: [
                'data-encryption',
                'access-control',
                'audit-logging'
            ],
            threatLevel: 'low',
            complianceStatus: 'compliant'
        };
    }
}
```

## Integration Points

### 🔗 VS Code Extension ↔ Edge Agent
- **Receipts**: Edge Agent generates receipts for VS Code Extension
- **Data Flow**: One-way data flow from Edge Agent to Extension
- **Format**: JSON receipts with signatures

### 🔗 Edge Agent ↔ Cloud Services
- **Delegation**: Edge Agent delegates tasks to Cloud Services
- **Validation**: Edge Agent validates results from Cloud Services
- **Communication**: RESTful APIs (FastAPI) and message queues
- **Protocol**: HTTP/HTTPS with JSON payloads

### 🔗 Cloud Services ↔ External Systems
- **APIs**: RESTful APIs for external integration
- **Authentication**: OAuth2 and JWT tokens
- **Rate Limiting**: API rate limiting and throttling

## Performance Considerations

### ⚡ VS Code Extension Performance
- **Lazy Loading**: UI components loaded on demand
- **Caching**: Receipt data cached for performance
- **Webview Optimization**: Efficient webview panel management

### ⚡ Edge Agent Performance
- **Local Processing**: All processing happens locally
- **Caching**: Local cache for frequently accessed data
- **Resource Optimization**: Dynamic resource allocation

### ⚡ Cloud Services Performance
- **Microservices**: Independent scaling of FastAPI services
- **Async Processing**: FastAPI async/await for concurrent requests
- **Database Optimization**: Efficient database queries with async ORM
- **API Optimization**: FastAPI performance tuning and response caching

## Security Implementation

### 🔒 Data Security
- **Encryption**: Data encrypted at rest and in transit
- **Access Control**: Role-based access control
- **Audit Logging**: Comprehensive audit trails

### 🔒 API Security
- **Authentication**: OAuth2 and JWT tokens (FastAPI Security)
- **Authorization**: Role-based authorization (dependency injection)
- **Rate Limiting**: API rate limiting and throttling (FastAPI middleware)
- **Input Validation**: Pydantic models for request/response validation

### 🔒 Local Security
- **Local Processing**: Sensitive data stays local
- **Security Policies**: Enforced security policies
- **Threat Detection**: Real-time threat detection

## Conclusion

ZeroUI 2.0 has achieved a **comprehensive low-level architecture** with detailed implementation patterns, technical specifications, and integration points. The architecture provides a solid foundation for implementing the actual functionality within the well-designed structural framework.

---

**Document Version**: v0.4
**Last Updated**: Current
**Status**: Architecture Complete, Implementation Pending
