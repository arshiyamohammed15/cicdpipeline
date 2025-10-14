import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
rule = next(r for r in factory.get_all_rules() if r["id"] == "L031")

@pytest.mark.parametrize("test_case", factory.create_test_cases(lambda x: x.get("id") == "L031"), ids=lambda tc: tc.test_method_name)
def test_l031_design_for_quick_adoption(test_case):
    assert test_case.rule_id == "L031"
    assert test_case.category == "system_design"
    assert test_case.constitution == "Product (Initial)"
    assert test_case.severity in ("error", "warning", "info")

    # Ensure rule metadata consistency
    assert rule["id"] == test_case.rule_id
