import json
from pathlib import Path

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[3]
EXAMPLES_DIR = ROOT / "contracts" / "llm_gateway" / "examples"
SCHEMAS_DIR = ROOT / "contracts" / "schemas"

PAIRS = [
    ("llm_request_v1_example.json", "llm_request_v1.json"),
    ("llm_response_v1_example.json", "llm_response_v1.json"),
]

for example_name, schema_name in PAIRS:
    example_path = EXAMPLES_DIR / example_name
    schema_path = SCHEMAS_DIR / schema_name
    example = json.loads(example_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft7Validator(schema).validate(example)

print("OK: validated 2 examples for llm_gateway")
