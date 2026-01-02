import json
from pathlib import Path

from evidence_receipt_indexing_service import models as eris_models

ROOT = Path(__file__).resolve().parents[3]
EXAMPLES_DIR = ROOT / "contracts" / "evidence_receipt_indexing_service" / "examples"

CASES = [
    ("health_response.json", eris_models.HealthResponse),
    ("receipt_ingestion_request.json", eris_models.ReceiptIngestionRequest),
    ("receipt_ingestion_response.json", eris_models.ReceiptIngestionResponse),
]

for example_name, model in CASES:
    example_path = EXAMPLES_DIR / example_name
    data = json.loads(example_path.read_text(encoding="utf-8"))
    model.model_validate(data)

print("OK: validated 3 examples for evidence_receipt_indexing_service")
