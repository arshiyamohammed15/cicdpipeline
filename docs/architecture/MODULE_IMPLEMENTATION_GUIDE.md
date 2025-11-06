# ZeroUI 2.0 Module Implementation Guide

**Purpose**: Step-by-step guide for implementing modules across the three-tier architecture  
**Architecture**: Based on `zeroui-hla.md` and `zeroui-lla.md`  
**Status**: Actionable patterns from actual codebase

---

## 🎯 Architecture Overview for Implementation

### Three-Tier Separation (CRITICAL)

```
┌─────────────────────────────────────────────────────────┐
│ TIER 1: VS Code Extension (Presentation Layer)          │
│ - Receives receipts from Edge Agent                      │
│ - Renders UI only (NO business logic)                     │
│ - UI components: ExtensionInterface → UIComponentManager   │
└─────────────────────────────────────────────────────────┘
                         ↓ Receipts
┌─────────────────────────────────────────────────────────┐
│ TIER 2: Edge Agent (Delegation Layer)                   │
│ - Delegates tasks to Cloud Services                      │
│ - Validates results (NO business logic)                 │
│ - Modules: Implement DelegationInterface                 │
└─────────────────────────────────────────────────────────┘
                         ↓ HTTP/HTTPS
┌─────────────────────────────────────────────────────────┐
│ TIER 3: Cloud Services (Business Logic Layer)            │
│ - ALL business logic implementation                      │
│ - FastAPI microservices                                  │
│ - Service structure: main.py → routes.py → services.py   │
└─────────────────────────────────────────────────────────┘
```

**RULE**: Business logic ONLY in Tier 3. Tiers 1 and 2 are presentation/delegation only.

---

## 📋 Implementation Checklist Per Module

When implementing a new module (M01-M20), you must implement across all three tiers:

- [ ] **Tier 3 (Cloud Service)**: Business logic implementation
- [ ] **Tier 2 (Edge Agent)**: Delegation interface (if needed)
- [ ] **Tier 1 (VS Code Extension)**: UI rendering from receipts

---

## 🏗️ TIER 3: Cloud Services Implementation

### Step 1: Determine Service Category

Based on `zeroui-hla.md` Service Boundaries:

- **Client Services** (`src/cloud-services/client-services/`): Modules 1-3, 6-14, 20
- **Product Services** (`src/cloud-services/product-services/`): Modules 4-5, 15-19
- **Shared Services** (`src/cloud-services/shared-services/`): Module 20 (when implemented)

### Step 2: Create Service Directory Structure

**Pattern** (from `zeroui-lla.md` lines 386-431):

```
src/cloud-services/{category}/{module-name}/
├── __init__.py
├── main.py                 # FastAPI app
├── routes.py               # API routes
├── services.py             # Business logic (THIS IS WHERE LOGIC GOES)
├── models.py               # Pydantic models
└── middleware.py           # Optional: Custom middleware
```

### Step 3: Implement FastAPI App (main.py)

**Pattern** (from `zeroui-lla.md` lines 435-464):

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

### Step 4: Define Pydantic Models (models.py)

**Pattern** (from `zeroui-lla.md` lines 525-555):

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

### Step 5: Implement Business Logic (services.py)

**Pattern** (from `zeroui-lla.md` lines 498-523):

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

### Step 6: Create API Routes (routes.py)

**Pattern** (from `zeroui-lla.md` lines 466-496):

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

**CRITICAL**: All business logic goes in `services.py`, NOT in `routes.py`. Routes only handle HTTP concerns.

---

## 🔄 TIER 2: Edge Agent Implementation

### When Edge Agent Module is Needed

Edge Agent modules are **infrastructure modules** (security, cache, inference, etc.), NOT business logic modules.

**Existing Edge Agent Modules** (from `src/edge-agent/modules/`):
- `security-enforcer/`
- `cache-manager/`
- `hybrid-orchestrator/`
- `local-inference/`
- `model-manager/`
- `resource-optimizer/`

**RULE**: Business logic modules (M01-M20) do NOT need Edge Agent implementations. Only infrastructure modules do.

### If Implementing an Edge Agent Module

**Step 1: Implement DelegationInterface**

**Pattern** (from `src/edge-agent/modules/security-enforcer/SecurityEnforcer.ts`):

```typescript
import { DelegationInterface, DelegationTask, DelegationResult, ModuleStatus } from '../../interfaces/core/DelegationInterface';

export class {ModuleName} implements DelegationInterface {
    private isActive: boolean = false;
    private isHealthy: boolean = true;
    private tasksProcessed: number = 0;
    private totalLatency: number = 0;
    private errorCount: number = 0;

    public async initialize(): Promise<void> {
        console.log('{Module Name} initializing...');
        this.isActive = true;
        console.log('{Module Name} initialized');
    }

    public async shutdown(): Promise<void> {
        console.log('{Module Name} shutting down...');
        this.isActive = false;
        console.log('{Module Name} shut down');
    }

    public async delegate(task: DelegationTask): Promise<DelegationResult> {
        const startTime = Date.now();
        
        try {
            console.log(`{Module Name} processing task: ${task.id}`);
            
            // Implement delegation logic here
            const result = await this.processTask(task);
            
            const processingTime = Date.now() - startTime;
            this.tasksProcessed++;
            this.totalLatency += processingTime;

            return {
                taskId: task.id,
                success: true,
                result: result,
                processingTime,
                metadata: {
                    module: '{module-name}',
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
        } catch (error) {
            const processingTime = Date.now() - startTime;
            this.errorCount++;
            
            console.error(`{Module Name} failed task: ${task.id}`, error);
            
            return {
                taskId: task.id,
                success: false,
                error: error.message,
                processingTime,
                metadata: {
                    module: '{module-name}',
                    timestamp: new Date(),
                    securityValidated: false,
                    dataIntegrity: false,
                    performanceMetrics: {
                        latency: processingTime,
                        memoryUsage: process.memoryUsage().heapUsed,
                        cpuUsage: 0
                    }
                }
            };
        }
    }

    public canHandle(task: DelegationTask): boolean {
        // Define when this module can handle a task
        return task.type === '{module-type}' || 
               task.requirements?.{requirement} === true;
    }

    public getCapabilities(): string[] {
        return [
            '{capability-1}',
            '{capability-2}',
            // ... more capabilities
        ];
    }

    public getStatus(): ModuleStatus {
        return {
            name: '{module-name}',
            isActive: this.isActive,
            isHealthy: this.isHealthy,
            lastActivity: new Date(),
            metrics: {
                tasksProcessed: this.tasksProcessed,
                averageLatency: this.tasksProcessed > 0 ? this.totalLatency / this.tasksProcessed : 0,
                errorRate: this.tasksProcessed > 0 ? this.errorCount / this.tasksProcessed : 0
            }
        };
    }

    private async processTask(task: DelegationTask): Promise<any> {
        // Implementation-specific logic
        return { processed: true };
    }
}
```

**Step 2: Register in EdgeAgent.ts**

Add to `src/edge-agent/EdgeAgent.ts`:

```typescript
import { {ModuleName} } from './modules/{module-name}/{ModuleName}';

// In constructor:
private {moduleName}: {ModuleName};

// In initializeModules():
this.{moduleName} = new {ModuleName}();

// In setupCoordination():
this.orchestrator.registerModule('{module-name}', this.{moduleName});
```

---

## 🎨 TIER 1: VS Code Extension Implementation

### Step 1: Create UI Component Files

**File Structure** (from `src/vscode-extension/ui/mmm-engine/`):

```
src/vscode-extension/ui/{module-name}/
├── ExtensionInterface.ts
├── UIComponent.ts
├── UIComponentManager.ts
└── types.ts
```

### Step 2: Define Types (types.ts)

```typescript
export interface {ModuleName}Data {
    id: string;
    // Define your module-specific data structure
    // This should match the receipt structure from Edge Agent
}
```

### Step 3: Implement UIComponent (UIComponent.ts)

**Pattern** (from `src/vscode-extension/ui/mmm-engine/UIComponent.ts`):

```typescript
import { {ModuleName}Data } from './types';

export class {ModuleName}UIComponent {
    public renderDashboard(data?: {ModuleName}Data): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZeroUI {Module Name} Dashboard</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 20px;
        }
        .dashboard {
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            padding: 16px;
        }
        .dashboard-header {
            font-weight: bold;
            margin-bottom: 16px;
            color: var(--vscode-textLink-foreground);
        }
        /* Add your module-specific styles */
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="dashboard-header">ZeroUI {Module Name} Dashboard</div>
        <div class="dashboard-content">
            ${data ? this.render{ModuleName}Content(data) : 'No {Module Name} data available'}
        </div>
    </div>
</body>
</html>`;
    }

    private render{ModuleName}Content(data: {ModuleName}Data): string {
        // Implement your module-specific rendering logic
        return `
            <div class="content">
                <p>Module ID: ${data.id}</p>
                <!-- Add your module-specific content -->
            </div>
        `;
    }
}
```

**CRITICAL**: UIComponent only renders HTML. NO business logic. Data comes from receipts.

### Step 4: Implement UIComponentManager (UIComponentManager.ts)

```typescript
import * as vscode from 'vscode';
import { {ModuleName}UIComponent } from './UIComponent';
import { {ModuleName}Data } from './types';

export class {ModuleName}UIComponentManager implements vscode.Disposable {
    private webviewPanel: vscode.WebviewPanel | undefined;
    private uiComponent: {ModuleName}UIComponent;

    constructor() {
        this.uiComponent = new {ModuleName}UIComponent();
    }

    public show{ModuleName}Dashboard(data?: {ModuleName}Data): void {
        if (this.webviewPanel) {
            this.webviewPanel.reveal(vscode.ViewColumn.One);
            return;
        }

        this.webviewPanel = vscode.window.createWebviewPanel(
            'zeroui{ModuleName}',
            'ZeroUI {Module Name} Dashboard',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        this.webviewPanel.webview.html = this.uiComponent.renderDashboard(data);
        
        this.webviewPanel.onDidDispose(() => {
            this.webviewPanel = undefined;
        });
    }

    public update{ModuleName}Data(data: {ModuleName}Data): void {
        if (this.webviewPanel) {
            this.webviewPanel.webview.html = this.uiComponent.renderDashboard(data);
        }
    }

    public dispose(): void {
        this.webviewPanel?.dispose();
    }
}
```

### Step 5: Implement ExtensionInterface (ExtensionInterface.ts)

**Pattern** (from `src/vscode-extension/ui/mmm-engine/ExtensionInterface.ts`):

```typescript
import * as vscode from 'vscode';
import { {ModuleName}UIComponentManager } from './UIComponentManager';

export class {ModuleName}ExtensionInterface implements vscode.Disposable {
    private uiManager: {ModuleName}UIComponentManager;
    private disposables: vscode.Disposable[] = [];

    constructor() {
        this.uiManager = new {ModuleName}UIComponentManager();
    }

    public registerCommands(context: vscode.ExtensionContext): void {
        const show{Dashboard} = vscode.commands.registerCommand('zeroui.{module-name}.showDashboard', () => {
            this.uiManager.show{ModuleName}Dashboard();
        });

        const refresh{Data} = vscode.commands.registerCommand('zeroui.{module-name}.refresh', () => {
            this.uiManager.update{ModuleName}Data({} as any); // Will be replaced with actual receipt data
        });

        const export{Report} = vscode.commands.registerCommand('zeroui.{module-name}.exportReport', () => {
            this.export{ModuleName}Report();
        });

        this.disposables.push(show{Dashboard}, refresh{Data}, export{Report});
        context.subscriptions.push(...this.disposables);
    }

    public registerViews(context: vscode.ExtensionContext): void {
        const {moduleName}TreeProvider = new {ModuleName}TreeDataProvider();
        const {moduleName}TreeView = vscode.window.createTreeView('zeroui{ModuleName}', {
            treeDataProvider: {moduleName}TreeProvider,
            showCollapseAll: true
        });

        this.disposables.push({moduleName}TreeView);
        context.subscriptions.push(...this.disposables);
    }

    private export{ModuleName}Report(): void {
        vscode.window.showInformationMessage('{Module Name} report export functionality');
    }

    public dispose(): void {
        this.disposables.forEach(d => d.dispose());
        this.uiManager.dispose();
    }
}

class {ModuleName}TreeDataProvider implements vscode.TreeDataProvider<any> {
    private _onDidChangeTreeData: vscode.EventEmitter<any | undefined | null | void> = new vscode.EventEmitter<any | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<any | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: any): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
        treeItem.command = {
            command: 'zeroui.{module-name}.showDashboard',
            title: 'Show {Module Name} Dashboard'
        };
        return treeItem;
    }

    getChildren(element?: any): any[] {
        return [
            { label: '{View Item 1}' },
            { label: '{View Item 2}' },
            // Add your module-specific tree items
        ];
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }
}
```

### Step 6: Register in extension.ts

**Pattern** (from `src/vscode-extension/extension.ts` lines 97-116, 134-145, 241-271):

```typescript
// Import
import { {ModuleName}ExtensionInterface } from './ui/{module-name}/ExtensionInterface';

// In activate() function:
const {moduleName}Interface = new {ModuleName}ExtensionInterface();

// Register commands and views
{moduleName}Interface.registerCommands(context);
{moduleName}Interface.registerViews(context);

// Add to subscriptions
context.subscriptions.push({moduleName}Interface);
```

### Step 7: Add Commands to package.json

**Pattern** (from `src/vscode-extension/package.json` lines 39-73):

```json
{
  "contributes": {
    "commands": [
      {
        "command": "zeroui.{module-name}.showDashboard",
        "title": "{Module Name} Dashboard",
        "category": "ZeroUI"
      },
      {
        "command": "zeroui.{module-name}.refresh",
        "title": "{Module Name} Refresh",
        "category": "ZeroUI"
      },
      {
        "command": "zeroui.{module-name}.exportReport",
        "title": "{Module Name} Export Report",
        "category": "ZeroUI"
      }
    ]
  }
}
```

---

## 🔄 Data Flow Implementation

### Receipt Flow (Edge Agent → VS Code Extension)

**Step 1: Edge Agent Generates Receipt**

Edge Agent processes task, calls Cloud Service, receives result, generates receipt:

```typescript
// In Edge Agent (pseudo-code)
const cloudResult = await this.delegationManager.delegateToCloudService(task);
const receipt = {
    receipt_id: generateId(),
    gate_id: 'edge-agent',
    decision: {
        status: 'approved',
        rationale: 'Task processed successfully',
        badges: ['processed']
    },
    inputs: task.data,
    result: cloudResult,
    timestamp_utc: new Date().toISOString(),
    signature: signReceipt(receipt)
};
```

**Step 2: VS Code Extension Receives Receipt**

```typescript
// In ExtensionInterface or UIComponentManager
const receipt = await receiveReceiptFromEdgeAgent();
const parsedReceipt = receiptParser.parseDecisionReceipt(receipt);
if (parsedReceipt) {
    const moduleData = extractModuleData(parsedReceipt);
    this.uiManager.update{ModuleName}Data(moduleData);
}
```

**Step 3: UI Renders from Receipt Data**

```typescript
// UIComponent uses receipt data to render
public renderDashboard(data?: {ModuleName}Data): string {
    // Render HTML using data from receipt
    // NO business logic, only presentation
}
```

---

## ✅ Implementation Validation Checklist

### Tier 3 (Cloud Services)
- [ ] Service directory created in correct category (client/product/shared)
- [ ] `main.py` implements FastAPI app with health endpoint
- [ ] `routes.py` defines API routes (no business logic)
- [ ] `services.py` contains ALL business logic
- [ ] `models.py` defines Pydantic models for validation
- [ ] Service can be started independently
- [ ] Health endpoint returns 200 OK

### Tier 2 (Edge Agent)
- [ ] Module implements `DelegationInterface` (if infrastructure module)
- [ ] Module registered in `EdgeAgent.ts`
- [ ] Module can handle appropriate task types
- [ ] Module returns `DelegationResult` with proper metadata

### Tier 1 (VS Code Extension)
- [ ] `ExtensionInterface.ts` implements `vscode.Disposable`
- [ ] `UIComponent.ts` renders HTML only (no business logic)
- [ ] `UIComponentManager.ts` manages webview panels
- [ ] Commands registered in `extension.ts`
- [ ] Commands added to `package.json`
- [ ] Types defined in `types.ts`
- [ ] UI renders from receipt data

### Cross-Tier Integration
- [ ] Cloud Service returns data in expected format
- [ ] Edge Agent can call Cloud Service API
- [ ] Edge Agent generates receipts with module data
- [ ] VS Code Extension can parse receipts
- [ ] UI displays data from receipts correctly

---

## 🚨 Critical Rules

### DO NOT Violate Separation of Concerns

❌ **NEVER** put business logic in:
- VS Code Extension (Tier 1)
- Edge Agent modules (Tier 2)

✅ **ALWAYS** put business logic in:
- Cloud Services (Tier 3)

### DO NOT Create Circular Dependencies

❌ Tier 1 → Tier 2 → Tier 3 → Tier 1 (circular)

✅ Tier 1 ← Tier 2 ← Tier 3 (one-way flow)

### DO Follow Receipt-Driven Pattern

- Edge Agent generates receipts
- VS Code Extension consumes receipts
- UI renders from receipt data only

### DO Use Established Patterns

- Follow file structure patterns exactly
- Use naming conventions (ExtensionInterface, UIComponent, etc.)
- Implement interfaces as documented

---

## 📚 Reference Files

### Architecture Documents
- `docs/architecture/zeroui-hla.md` - High-level architecture
- `docs/architecture/zeroui-lla.md` - Low-level implementation patterns
- `docs/architecture/modules-mapping-and-gsmd-guide.md` - Module mappings

### Implementation Examples
- VS Code Extension: `src/vscode-extension/ui/mmm-engine/`
- Edge Agent: `src/edge-agent/modules/security-enforcer/`
- Cloud Services: Use patterns from `zeroui-lla.md` (services not yet implemented)

### Validation
- `docs/architecture/ARCHITECTURE_VALIDATION_REPORT.md` - Current implementation status

---

**Document Version**: 1.0  
**Last Updated**: Current  
**Status**: Implementation Guide - Ready for Use

