import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
rule = next(r for r in factory.get_all_rules() if r["id"] == "L051")

@pytest.mark.parametrize("test_case", factory.create_test_cases(lambda x: x.get("id") == "L051"), ids=lambda tc: tc.test_method_name)
def test_l051_scale_from_small_to_huge(test_case):
    assert test_case.rule_id == "L051"
    assert test_case.category == "platform"
    assert test_case.constitution == "Product (Initial)"
    assert test_case.severity in ("error", "warning", "info")

    # Ensure rule metadata consistency
    assert rule["id"] == test_case.rule_id
