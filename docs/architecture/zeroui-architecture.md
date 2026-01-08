# ZeroUI 2.0 Architecture

> **⚠️ SINGLE SOURCE OF TRUTH**: This document is the **ONLY** authoritative source for ZeroUI architecture. All other architecture documents reference this document.
>
> **Module Categories**: See **[ZeroUI Module Categories V 3.0](./ZeroUI%20Module%20Categories%20V%203.0.md)** for the final authoritative module categorization.

## Executive Summary

ZeroUI 2.0 implements a **three-tier hybrid architecture** with strict separation of concerns, designed for enterprise-grade AI systems with presentation-only UI, delegation-based edge processing, and comprehensive business logic services. The system follows a **local-first, receipts-first** approach where code stays local by default, and all decisions are tracked through signed receipts.

## Architectural Overview

### 🏗️ Three-Tier Architecture

#### **TIER 1: PRESENTATION LAYER**
- **VS Code Extension**: Presentation-only UI rendering
- **Architecture**: Receipt-driven, no business logic
- **Pattern**: Modular UI components with extension interfaces
- **Language**: TypeScript
- **Framework**: VS Code Extension API
- **Status**: ✅ Complete structure, minimal functionality

#### **TIER 2: EDGE PROCESSING LAYER**
- **Edge Agent**: Delegation and validation only
- **Architecture**: Local processing coordination
- **Pattern**: Task delegation with validation
- **Language**: TypeScript
- **Status**: ✅ Complete structure, minimal functionality

#### **TIER 3: BUSINESS LOGIC LAYER**
- **Cloud Services**: All business logic implementation
- **Architecture**: Service-oriented with clear boundaries
- **Implementation**: Python/FastAPI microservices
- **Pattern**: Client/Product/Shared service separation
- **Status**: ✅ Complete structure, 18 services implemented (4 product + 14 shared)

## Architectural Principles

### ✅ Separation of Concerns

#### **VS Code Extension**
- **Presentation-Only**: No business logic
- **Receipt-Driven**: All UI from Edge Agent receipts
- **Modular**: Self-contained UI components
- **VS Code Integration**: Commands, views, and webview panels

#### **Edge Agent**
- **Delegation-Only**: No business logic
- **Local Processing**: All processing local
- **Validation**: Result validation and quality assurance
- **Coordination**: Central orchestration of module interactions

#### **Cloud Services**
- **Business Logic**: All business logic resides here
- **Implementation**: Python/FastAPI microservices
- **Service Boundaries**: Clear Client/Product/Shared separation
- **Modular**: Independent service modules with FastAPI routers
- **Infrastructure**: Gateway, evidence, and policy services
- **API Design**: RESTful APIs with Pydantic models for validation

### 🔒 Core Design Principles

- **Fast**: Most checks happen on your laptop, instantly
- **Private**: Code stays local unless you say otherwise; receipts are small and safe
- **Consistent**: Same rules on laptop and in CI, so no surprises
- **Trustworthy**: Everything important is signed and audited
- **Local-First**: Sensitive data stays local via Edge Agent; no code/PII leaves the laptop
- **Receipts-First**: Log INTENT→RESULT with sequence_no and hash chain
- **Deterministic**: Every action is predefined, testable, and reversible

## Current Project Structure

### 📁 VS Code Extension (Presentation Layer)
```
src/vscode-extension/
├── extension.ts                    # Main orchestration (lean)
├── package.json                   # Extension manifest
├── tsconfig.json                  # TypeScript configuration
├── shared/
│   └── receipt-parser/            # Receipt parsing utilities
│       └── ReceiptParser.ts       # Receipt parsing logic
├── modules/                       # Module logic (manifest-based)
│   ├── m01-mmm-engine/
│   │   ├── module.manifest.json
│   │   ├── index.ts               # export registerModule()
│   │   ├── commands.ts
│   │   ├── providers/            # status pill, diagnostics
│   │   ├── views/                # DecisionCard sections
│   │   └── actions/              # Quick actions
│   ├── m05-detection-engine-core/
│   ├── m21-identity-access-management/
│   ├── m23-configuration-policy-management/
│   └── [m02-m04, m06-m20 other modules...]
└── ui/                            # UI components (presentation-only)
    ├── [Core UI Components]        # 6 core UI components
    │   ├── status-bar/
    │   ├── problems-panel/
    │   ├── decision-card/
    │   ├── evidence-drawer/
    │   ├── toast/
    │   └── receipt-viewer/
    └── [20 Module UI Components]   # Module-specific UI
        ├── mmm-engine/
        ├── compliance-security-challenges/
        └── [18 other modules...]
```

### 📁 Edge Agent (Processing Layer)
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

### 📁 Cloud Services (Business Logic Layer)
```
src/cloud_services/
├── client-services/                # Client-owned business logic modules
│   └── integration-adapters/
├── product_services/              # ZeroUI-owned product modules
│   ├── detection-engine-core/
│   ├── mmm_engine/
│   ├── signal-ingestion-normalization/
│   └── user_behaviour_intelligence/
├── shared-services/                # ZeroUI-owned infrastructure modules
│   ├── alerting-notification-service/
│   ├── api-gateway-webhooks/
│   ├── budgeting-rate-limiting-cost-observability/
│   ├── configuration-policy-management/
│   ├── contracts-schema-registry/
│   ├── data-governance-privacy/
│   ├── deployment-infrastructure/
│   ├── evidence-receipt-indexing-service/
│   ├── health-reliability-monitoring/
│   ├── identity-access-management/
│   ├── key-management-service/
│   ├── ollama-ai-agent/
│   └── trust-as-capability/
└── llm_gateway/                    # LLM Gateway service
```

## VS Code Extension Technical Details

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

### 🔧 Service Implementation Patterns

#### **FastAPI App Pattern (main.py)**
```python
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from .models import HealthResponse

app = FastAPI(
    title="ZeroUI {Module Name} Service",
    version="2.0.0",
    description="{Module Name} business logic service"
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
app.include_router(router, prefix="/api/v1", tags=["{module-name}"])

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
from .services import {ModuleName}Service

router = APIRouter()

def get_service() -> {ModuleName}Service:
    return {ModuleName}Service()

@router.post("/process", response_model=ProcessDataResponse)
async def process_data(
    request: ProcessDataRequest,
    service: {ModuleName}Service = Depends(get_service)
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
# from .repositories import DataRepository  # Add if needed
# from .validators import ValidationService  # Add if needed

class {ModuleName}Service:
    def __init__(
        self,
        # data_repository: Optional[DataRepository] = None,
        # validation_service: Optional[ValidationService] = None
    ):
        # self.data_repository = data_repository or DataRepository()
        # self.validation_service = validation_service or ValidationService()
        pass

    async def process_data(self, request: ProcessDataRequest) -> dict:
        """
        IMPLEMENT YOUR BUSINESS LOGIC HERE
        This is the ONLY place where business logic should exist.
        """
        # Validate input data (if validation service exists)
        # await self.validation_service.validate(request)

        # Process data (your business logic)
        result = {
            "processed": True,
            "module": "{module-name}",
            "data": request.data
        }

        # Return processed result
        return result
```

#### **Pydantic Model Pattern (models.py)**
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class {ModuleName}Metrics(BaseModel):
    collected: int = Field(ge=0, description="Number of metrics collected")
    processed: int = Field(ge=0, description="Number of metrics processed")
    errors: int = Field(ge=0, description="Number of errors encountered")

class {ModuleName}Data(BaseModel):
    id: str = Field(..., description="Unique identifier")
    metrics: {ModuleName}Metrics = Field(..., description="Module metrics")
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
    'resources'       // Resource optimization
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
- **Protocol**: Local IPC/HTTP

### 🔗 Edge Agent ↔ Cloud Services
- **Delegation**: Edge Agent delegates tasks to Cloud Services
- **Validation**: Edge Agent validates results from Cloud Services
- **Communication**: RESTful APIs (FastAPI) and message queues
- **Protocol**: HTTP/HTTPS with JSON payloads

### 🔗 Cloud Services ↔ External Systems
- **APIs**: RESTful APIs for external integration
- **Authentication**: OAuth2 and JWT tokens
- **Rate Limiting**: API rate limiting and throttling

## System Context & Planes

### Four-Plane Architecture (Conceptual View)

The system can be understood as four planes:

1. **IDE / Edge Agent Plane** (Your Laptop)
   - VS Code Extension (presentation)
   - Edge Agent (delegation): local policy evaluator (dry-run), receipt writer (append-only JSONL), policy cache, config loader, adapters (Git/PR/CI)
   - In-flow coaching: Mirror / Mentor / Multiplier messages, status pill, diagnostics, quick fix
   - Laptop trust: public-key trust store (KID-based), optional signing, local logs/receipts

2. **Client / Tenant Cloud Plane** (Your Company)
   - Policy enforcement proxies for PR/CI (pass / warn / soft_block / hard_block)
   - Evidence/WORM stores (append-only mirror, retention, legal-hold)
   - Data minimisation/redaction (before anything leaves tenant)
   - Enterprise adapters (Git/CI, Confluence/Jira, Slack/Teams), SSO/SCIM, compliance hooks
   - Tenant privacy-split APIs/queues to talk to product cloud

3. **ZeroUI Product Cloud Plane** (The Product's Brain)
   - Detection & decision services, risk/nudge engines, release risk gate, knowledge integrity
   - Learning loop (uses receipts/metadata, not raw code) → improves tips and rules
   - Feature store, bounded model helpers for explanations
   - Policy compiler → signed policy snapshot (hash, KID, version IDs)

4. **Shared Services Plane** (Building Security & Logs)
   - Identity & trust, Policy Registry (signed snapshots), Audit Ledger (append-only)
   - Observability mesh (metrics/logs/traces, SLO/error-budget), key management, artifact/model registry, notification bus

### Connectors Between Planes

- **Shared ⇄ Product**: contracts (OpenAPI) / events
- **Product ⇄ Client**: privacy-split APIs / queues
- **Client ⇄ IDE**: local-first, signed receipts

## End-to-End Flow (T0 / T1 / T2)

1. **T0: Evaluate** - Compile & Sign Policy Snapshot (Product) → Publish to Policy Registry (Shared) → Fetch & Cache Snapshot (Client) → Pull Snapshot (Local Cache) (IDE) → Local Policy Evaluation (dry-run) (IDE) → Show pill, diagnostics, quick fix

2. **T1: Act** - User selects fix → Decision Card shows "What will happen" → Extension calls Edge Agent → Agent verifies signature/KID → Agent performs dry-run → Extension shows diff for confirm → On confirm, agent applies action → Write Signed Receipt (IDE → append-only JSONL) → User choices recorded

3. **T2: Outcome** - PR/CI Gate Enforcement (Client) → Append to Audit Ledger (Shared) → Evidence logged → Learning Loop & Nudge Updates (Product) → next signed snapshot

## Data & Privacy

- **Code stays local by default**
- **Receipts/evidence are metadata** (what happened, why, outcome)
- **Redaction/minimisation happens** in the Client plane before any cross-plane sharing
- **Stores**: laptop receipts → tenant WORM mirror → shared audit ledger (append-only)

## Policy Lifecycle

**States**: Draft → Review → Approve → Sign → Distribute → Revoke

- Each snapshot has hash + KID + version IDs
- Distribution via Policy Registry; clients and laptops verify before using
- Revocation uses registry + tenant caches

## Gate Decision (Deterministic)

**Flow**: Inputs → rubric → outcome (pass / warn / soft_block / hard_block) + reason codes

- Receipt always written (includes decision, reason, policy_version_ids)
- Same rules on laptop and in CI (no surprises)

## Trust & Keys

- Product cloud signs snapshots
- Laptops/clients verify with trusted public keys (KID-based)
- Rotation & revocation (CRL) supported via the registry
- Audit ledger ensures append-only evidence

## Observability & SLOs

- OpenTelemetry metrics/logs/traces flow into the observability mesh
- SLO/error-budget checks run; alerts go to IDE and chat channels via notification bus
- Examples: availability, latency, receipt fsync budget

## Storage & Retention

- **Laptop**: receipts (JSONL), logs, snapshot cache
- **Client**: WORM evidence mirror, legal-hold/retention, DLQ for ingestion
- **Shared**: audit ledger (append-only), policy registry, artifact/model registry

## Deployment & Environment Ladder

**Environments**: Development → Integration → Staging → UAT → Production

- Each environment shows ingress, egress, secrets/trust stores, and rollback path
- Canary/blue-green supported
- Clear rollback path (policy/snapshot and gate configs are versioned)

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

## Service Boundaries

### 🏢 Client Services (Company-Owned, Private Data)
- **Location**: `src/cloud_services/client-services/`
- **Modules**: Company-specific business logic
- **Data**: Private company data and processes
- **Ownership**: Company-owned services

### 🏭 Product Services (ZeroUI-Owned, Cross-Tenant)
- **Location**: `src/cloud_services/product_services/`
- **Modules**: ZeroUI product functionality
- **Data**: Cross-tenant product data
- **Ownership**: ZeroUI-owned services

### 🔧 Shared Services (ZeroUI-Owned, Infrastructure)
- **Location**: `src/cloud_services/shared-services/`
- **Modules**: ZeroUI-owned infrastructure
- **Ownership**: ZeroUI-owned infrastructure

## Implementation Status

### ✅ Completed
- **Architecture**: Complete three-tier structure
- **VS Code Extension**: 20 UI modules + 6 core components
- **Edge Agent**: 6 delegation modules + orchestration
- **Cloud Services**: 16 modules have `main.py` files implemented

### ❌ Minimal Functionality
- **Edge Agent**: Architecture only, no real implementation
- **VS Code Extension**: Architecture only, no real UI functionality
- **Cloud Services**: Some modules have structure only, no business logic implementation

### ✅ Working Components
- **Receipt Parser**: Complete parsing and validation logic
- **VS Code Integration**: Extension can be loaded
- **Architecture**: Proper separation of concerns

## Key Architectural Benefits

### 🎯 Clean Separation
- **Clear Boundaries**: Each tier has distinct responsibilities
- **No Cross-Tier Logic**: Business logic only in Cloud Services
- **Modular Design**: Independent, maintainable components

### 🚀 Scalability
- **Independent Scaling**: Each tier can scale independently
- **Service-Oriented**: Cloud Services can be distributed
- **Edge Processing**: Local processing reduces cloud dependency

### 🔒 Security
- **Data Isolation**: Clear data ownership boundaries
- **Local Processing**: Sensitive data stays local
- **Validation**: Multi-layer validation and quality assurance

## Next Steps

### 🎯 Implementation Priorities
1. **Edge Agent Implementation**: Real delegation and validation logic
2. **VS Code Extension Implementation**: Functional UI components
3. **Cloud Services Implementation**: Business logic modules

### 📋 Architectural Compliance
- **✅ Structure**: Complete three-tier architecture
- **✅ Separation**: Clear separation of concerns
- **✅ Modularity**: Independent, maintainable components
- **❌ Functionality**: Minimal working implementation

## Glossary

- **Policy (Rulebook)**: Clear "yes/no/warn" rules written as code
- **Receipt**: A small, signed note: what ran, what it decided, and why
- **Nudge**: Friendly hint in the IDE to fix or improve a change
- **Snapshot**: A sealed version of the rulebook everyone agrees on

## References

- **Module Categories**: [ZeroUI Module Categories V 3.0](./ZeroUI%20Module%20Categories%20V%203.0.md)
- **Edge Agent Architecture**: [edge-agent-architecture.md](./edge-agent-architecture.md)
- **Module Mappings**: [modules-mapping-and-gsmd-guide.md](./modules-mapping-and-gsmd-guide.md)

---

**Document Version**: v2.0  
**Last Updated**: 2026-01-03  
**Status**: Single Source of Truth - Architecture Complete, Implementation Pending

