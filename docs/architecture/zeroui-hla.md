# ZeroUI High-Level Architecture (HLA)

**Date**: 2026-01-03  
**Status**: Current Architecture  
**Version**: 2.0

## Executive Summary

ZeroUI 2.0 implements a **three-tier hybrid architecture** with strict separation of concerns:
- **TIER 1: Presentation Layer** - VS Code Extension (TypeScript)
- **TIER 2: Edge Processing Layer** - Edge Agent (TypeScript)
- **TIER 3: Business Logic Layer** - Cloud Services (Python/FastAPI)

## Code Organization

### Presentation Layer (VS Code Extension)
- **Location**: `src/vscode-extension/`
- **Structure**:
  - `extension.ts` - Main orchestration entry point
  - `modules/` - Module logic with manifest-based registration (m01-m23)
  - `ui/` - UI components (6 core + 20 module-specific)
  - `shared/` - Shared utilities (receipt parser, storage, validation)

### Edge Processing Layer (Edge Agent)
- **Location**: `src/edge-agent/`
- **Structure**:
  - `EdgeAgent.ts` - Main orchestrator
  - `core/` - Core orchestration components (AgentOrchestrator, DelegationManager, ValidationCoordinator)
  - `modules/` - Infrastructure modules (security-enforcer, cache-manager, hybrid-orchestrator, local-inference, model-manager, resource-optimizer)
  - `interfaces/` - Delegation and validation contracts
  - `shared/` - Shared utilities (storage, receipt generation, policy storage)

### Business Logic Layer (Cloud Services)
- **Location**: `src/cloud_services/`
- **Structure**:
  - `client-services/` - Client-owned business logic (integration-adapters)
  - `product_services/` - ZeroUI-owned product modules (detection-engine-core, mmm_engine, signal-ingestion-normalization, user_behaviour_intelligence)
  - `shared-services/` - ZeroUI-owned infrastructure modules (14 services including alerting, budgeting, configuration-policy-management, contracts-schema-registry, data-governance-privacy, deployment-infrastructure, evidence-receipt-indexing-service, health-reliability-monitoring, identity-access-management, key-management-service, ollama-ai-agent, trust-as-capability)
  - `llm_gateway/` - LLM Gateway service

## Architectural Principles

1. **Separation of Concerns**: Each tier has distinct responsibilities
2. **Local-First**: Sensitive data stays local via Edge Agent
3. **Receipts-First**: All decisions tracked through signed receipts
4. **Presentation-Only UI**: VS Code Extension renders UI from receipts, no business logic
5. **Delegation-Only Edge**: Edge Agent delegates and validates, no business logic
6. **Business Logic in Services**: All business logic in Cloud Services

## Module Count

- **VS Code Extension Modules**: 23 modules (m01-m23)
- **Cloud Services**: 18 services (4 product + 14 shared)
- **Edge Agent Modules**: 6 infrastructure modules

## References

- **Detailed Architecture**: `docs/architecture/zeroui-architecture.md`
- **Low-Level Architecture**: `docs/architecture/zeroui-lla.md`
- **Edge Agent Architecture**: `docs/architecture/edge-agent-architecture.md`
