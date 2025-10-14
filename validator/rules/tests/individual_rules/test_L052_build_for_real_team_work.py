import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
rule = next(r for r in factory.get_all_rules() if r["id"] == "L052")

@pytest.mark.parametrize("test_case", factory.create_test_cases(lambda x: x.get("id") == "L052"), ids=lambda tc: tc.test_method_name)
def test_l052_build_for_real_team_work(test_case):
    assert test_case.rule_id == "L052"
    assert test_case.category == "teamwork"
    assert test_case.constitution == "Product (Initial)"
    assert test_case.severity in ("error", "warning", "info")

    # Ensure rule metadata consistency
    assert rule["id"] == test_case.rule_id
