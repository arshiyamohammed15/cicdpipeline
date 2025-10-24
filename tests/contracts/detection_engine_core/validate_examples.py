# Minimal example loader for detection_engine_core
import json, pathlib

base = pathlib.Path(__file__).resolve().parents[3] / "contracts" / "detection_engine_core" / "examples"
names = ["decision_response_ok.json","decision_response_error.json","evidence_link_valid.json","feedback_receipt_valid.json","receipt_valid.json"]

for n in names:
    p = base / n
    data = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data, (dict, list)), f"Example {n} is not JSON object/list"
print("OK: loaded 5 examples for detection_engine_core")
