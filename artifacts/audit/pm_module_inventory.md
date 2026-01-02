# PM Modules Inventory (PASS 1)

## PM-1 - MMM Engine
- Declared paths:
  - VS Code Extension: `src/vscode-extension/modules/m01-mmm-engine/`
  - Cloud Service: `src/cloud_services/product_services/mmm_engine/main.py`
- Entry points:
  - `src/cloud_services/product_services/mmm_engine/main.py` (exists=true)
- Tests:
  - `tests/mmm_engine`
  - `tests/cloud_services/product_services/mmm_engine`

## PM-2 - Cross-Cutting Concern Services
- Declared paths:
  - VS Code Extension: `src/vscode-extension/modules/m02-cross-cutting-concern-services/`
  - Cloud Service: `src/shared_libs/cccs/`
- Entry points:
  - `src/shared_libs/cccs/__init__.py` (exists=true)
- Tests:
  - `tests/cccs`

## PM-3 - Signal Ingestion & Normalization
- Declared paths:
  - VS Code Extension: `src/vscode-extension/modules/m04-signal-ingestion-normalization/`
  - Cloud Service: `src/cloud_services/product_services/signal-ingestion-normalization/main.py`
- Entry points:
  - `src/cloud_services/product_services/signal-ingestion-normalization/main.py` (exists=true)
- Tests:
  - `tests/sin`
  - `tests/cloud_services/product_services/signal_ingestion_normalization`

## PM-4 - Detection Engine Core
- Declared paths:
  - VS Code Extension: `src/vscode-extension/modules/m05-detection-engine-core/`
  - Cloud Service: `src/cloud_services/product_services/detection-engine-core/main.py`
- Entry points:
  - `src/cloud_services/product_services/detection-engine-core/main.py` (exists=true)
- Tests:
  - `tests/cloud_services/product_services/detection_engine_core`

## PM-5 - Integration Adapters
- Declared paths:
  - VS Code Extension: `src/vscode-extension/modules/m10-integration-adapters/`
  - Cloud Service: `src/cloud_services/client-services/integration-adapters/main.py`
- Entry points:
  - `src/cloud_services/client-services/integration-adapters/main.py` (exists=true)
- Tests:
  - `tests/cloud_services/client_services/integration_adapters`

## PM-6 - LLM Gateway & Safety Enforcement
- Declared paths:
  - VS Code Extension: (none listed)
  - Cloud Service: `src/cloud_services/llm_gateway/main.py`
- Entry points:
  - `src/cloud_services/llm_gateway/main.py` (exists=true)
- Tests:
  - `tests/llm_gateway`

## PM-7 - Evidence & Receipt Indexing Service
- Declared paths:
  - VS Code Extension: (none listed)
  - Cloud Service: `src/cloud_services/shared-services/evidence-receipt-indexing-service/main.py`
- Entry points:
  - `src/cloud_services/shared-services/evidence-receipt-indexing-service/main.py` (exists=true)
- Tests:
  - `tests/cloud_services/shared_services/evidence_receipt_indexing_service`
