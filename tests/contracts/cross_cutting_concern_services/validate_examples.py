# Minimal example loader for cross_cutting_concern_services
import json, pathlib

base = pathlib.Path(__file__).resolve().parents[3] / "contracts" / "cross_cutting_concern_services" / "examples"
names = ["decision_response_ok.json","decision_response_error.json","evidence_link_valid.json","feedback_receipt_valid.json","receipt_valid.json"]

for n in names:
    p = base / n
    data = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data, (dict, list)), f"Example {n} is not JSON object/list"
print("OK: loaded 5 examples for cross_cutting_concern_services")
