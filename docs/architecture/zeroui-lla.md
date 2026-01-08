# ZeroUI Low-Level Architecture (LLA)

**Date**: 2026-01-03  
**Status**: Current Architecture  
**Version**: 2.0

## Overview

This document outlines low-level structural conventions, implementation patterns, and technical details used across the ZeroUI codebase.

## VS Code Extension Layout

### Module Structure
- **Location**: `src/vscode-extension/modules/`
- **Pattern**: Each module follows `m{NN}-{module-name}/` naming
- **Structure per Module**:
  ```
  m{NN}-{module-name}/
  ├── module.manifest.json    # Module manifest (commands, menus, views, configuration)
  ├── index.ts                # Module registration (export registerModule())
  ├── commands.ts             # Command implementations
  ├── providers/              # Status pill and diagnostics providers
  │   ├── status-pill.ts
  │   └── diagnostics.ts
  ├── views/                  # DecisionCard section providers
  │   └── DecisionCardSectionProvider.ts
  └── actions/                # Quick action implementations
      └── QuickActions.ts
  ```

### UI Component Structure
- **Location**: `src/vscode-extension/ui/`
- **Core Components** (6):
  - `status-bar/` - StatusBarManager
  - `problems-panel/` - ProblemsPanelManager
  - `decision-card/` - DecisionCardManager
  - `evidence-drawer/` - EvidenceDrawerManager
  - `toast/` - ToastManager
  - `receipt-viewer/` - ReceiptViewerManager

- **Module UI Components** (20):
  - Each module has corresponding UI component in `ui/{module-name}/`
  - Pattern: `ExtensionInterface.ts`, `UIComponent.ts`, `UIComponentManager.ts`, `types.ts`

### Shared Utilities
- **Location**: `src/vscode-extension/shared/`
- **Components**:
  - `receipt-parser/` - ReceiptParser for parsing DecisionReceipt objects
  - `storage/` - PSCLArtifactWriter, PreCommitDecisionService, ReceiptStorageReader
  - `validation/` - PreCommitValidationPipeline

## Edge Agent Layout

### Core Components
- **Location**: `src/edge-agent/core/`
- **Files**:
  - `AgentOrchestrator.ts` - Module coordination and orchestration
  - `DelegationManager.ts` - Task delegation and routing
  - `ValidationCoordinator.ts` - Result validation with multi-rule system

### Module Pattern
- **Location**: `src/edge-agent/modules/`
- **Structure per Module**:
  ```
  {module-name}/
  ├── {ModuleName}.ts         # Main module class implementing DelegationInterface
  └── [supporting files]
  ```

### Interfaces
- **Location**: `src/edge-agent/interfaces/core/`
- **Files**:
  - `DelegationInterface.ts` - DelegationTask, DelegationResult contracts
  - `ValidationInterface.ts` - ValidationRule contracts

### Shared Components
- **Location**: `src/edge-agent/shared/`
- **Components**:
  - `storage/` - ReceiptStorageService, ReceiptGenerator, PolicyStorageService
  - `health/` - HeartbeatEmitter
  - `ai-detection/` - AIAssistanceDetector
  - `storage/` - DataCategoryClassifier

## Cloud Services Layout

### Service Structure Pattern
- **Location**: `src/cloud_services/{category}-services/{service-name}/`
- **Standard Structure**:
  ```
  {service-name}/
  ├── main.py                 # FastAPI app entry point
  ├── routes.py               # API route definitions
  ├── services.py             # Business logic services
  ├── models.py               # Pydantic models
  ├── dependencies.py         # Dependency injection
  ├── database/               # Database layer
  │   ├── connection.py      # DB connection management
  │   ├── models.py          # SQLAlchemy models
  │   ├── repositories.py    # Data access layer
  │   └── migrations/        # Alembic migrations
  ├── observability/          # Metrics, tracing, audit
  ├── middleware.py          # Custom middleware
  ├── config.py              # Configuration
  └── requirements.txt        # Python dependencies
  ```

### Service Categories
- **Client Services**: `src/cloud_services/client-services/`
- **Product Services**: `src/cloud_services/product_services/`
- **Shared Services**: `src/cloud_services/shared-services/`
- **LLM Gateway**: `src/cloud_services/llm_gateway/`

## Platform Layer

### Location
- **Location**: `src/platform/`
- **Structure**:
  - `router/` - WorkloadRouter
  - `adapters/` - Local adapters (LocalDRPlan, LocalGpuPool, LocalDLQ, LocalIngress)
  - `ports/` - Port interfaces
  - `config/` - Configuration
  - `cost/` - CostTracker

## Implementation Patterns

### TypeScript Patterns
- **Module Registration**: Manifest-based with `registerModule()` export
- **UI Components**: Manager pattern with webview panels
- **Receipt Processing**: Parser pattern with validation
- **Delegation**: Interface-based with `DelegationInterface`

### Python Patterns
- **FastAPI Services**: Router-based with dependency injection
- **Database Layer**: Repository pattern with SQLAlchemy
- **Observability**: Decorator-based metrics and tracing
- **Configuration**: Environment variable-based with Pydantic models

## File Naming Conventions

- **TypeScript**: PascalCase for classes, camelCase for functions, kebab-case for files
- **Python**: snake_case for files and functions, PascalCase for classes
- **Modules**: `m{NN}-{kebab-case-name}/` pattern
- **Services**: `{kebab-case-name}/` pattern

## References

- **High-Level Architecture**: `docs/architecture/zeroui-hla.md`
- **Detailed Architecture**: `docs/architecture/zeroui-architecture.md`
- **Edge Agent Architecture**: `docs/architecture/edge-agent-architecture.md`
