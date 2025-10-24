# Minimal example loader for compliance_and_security_challenges
import json, pathlib

base = pathlib.Path(__file__).resolve().parents[3] / "contracts" / "compliance_and_security_challenges" / "examples"
names = ["decision_response_ok.json","decision_response_error.json","evidence_link_valid.json","feedback_receipt_valid.json","receipt_valid.json"]

for n in names:
    p = base / n
    data = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data, (dict, list)), f"Example {n} is not JSON object/list"
print("OK: loaded 5 examples for compliance_and_security_challenges")
