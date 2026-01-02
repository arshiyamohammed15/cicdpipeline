# PM Modules Contract Tests (PASS 3)

Result: PASS

Commands:
- `python -m pytest --import-mode=importlib tests/contracts/mmm_engine/validate_examples.py tests/contracts/cross_cutting_concern_services/validate_examples.py tests/contracts/signal_ingestion_and_normalization/validate_examples.py tests/contracts/detection_engine_core/validate_examples.py tests/contracts/integration_adaptors/validate_examples.py tests/contracts/llm_gateway/validate_examples.py tests/contracts/evidence_receipt_indexing_service/validate_examples.py -q`
- `python scripts/ci/validate_llm_gateway_schemas.py`

Logs:
- `artifacts/audit/logs/pass3_contracts.log`
- `artifacts/audit/logs/pass3_llm_gateway_schema_validation.log`

Evidence summary:
- PM-1..PM-5: contract example fixtures loaded from `contracts/*/examples` via `tests/contracts/*/validate_examples.py`.
- PM-6: `contracts/llm_gateway/examples/*` validated against `contracts/schemas/llm_*_v1.json`.
- PM-7: `contracts/evidence_receipt_indexing_service/examples/*` validated via ERIS Pydantic models.
