from __future__ import annotations

import pytest

from validator.utils import rule_validator


class _DummyCountLoader:
    def __init__(self, total: int) -> None:
        self._total = total

    def get_total_rules(self) -> int:
        return self._total


class _DummyRules:
    def __init__(self, rules: list[dict]) -> None:
        self._rules = rules

    def get_all_rules(self) -> list[dict]:
        return list(self._rules)

    def get_rule_by_number(self, number: int) -> dict | None:
        for rule in self._rules:
            if rule.get("rule_number") == number:
                return rule
        return None


def _make_validator(monkeypatch: pytest.MonkeyPatch, rules: list[dict], total: int | None = None) -> rule_validator.RuleNumberValidator:
    monkeypatch.setattr(rule_validator, "get_rule_count_loader", lambda: _DummyCountLoader(total or len(rules)))
    monkeypatch.setattr(rule_validator, "ConstitutionRulesJSON", lambda: _DummyRules(rules))
    return rule_validator.RuleNumberValidator()


def test_validate_and_lookup_rule_number(monkeypatch: pytest.MonkeyPatch) -> None:
    rules = [
        {"rule_number": 1, "title": "Rule One"},
        {"rule_number": 2, "title": "Rule Two"},
        {"rule_number": 3, "title": "Rule Three"},
    ]
    validator = _make_validator(monkeypatch, rules)

    assert validator.validate_rule_number(2) is True
    assert validator.get_rule_by_number(1)["title"] == "Rule One"
    assert validator.get_rule_number_by_title("Two") == 2


def test_out_of_range_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    rules = [{"rule_number": 1, "title": "Rule One"}]
    validator = _make_validator(monkeypatch, rules, total=1)

    with pytest.raises(ValueError) as exc:
        validator.validate_rule_number(5)

    assert "out of valid range" in str(exc.value)


def test_rule_number_mismatch_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    class _MismatchRules:
        def get_all_rules(self) -> list[dict]:
            return [{"rule_number": 99, "title": "Mismatch"}]

        def get_rule_by_number(self, number: int) -> dict:
            return {"rule_number": 99, "title": "Mismatch"}

    monkeypatch.setattr(rule_validator, "get_rule_count_loader", lambda: _DummyCountLoader(100))
    monkeypatch.setattr(rule_validator, "ConstitutionRulesJSON", _MismatchRules)

    validator = rule_validator.RuleNumberValidator()

    with pytest.raises(ValueError) as exc:
        validator.validate_rule_number(2)

    assert "Rule number mismatch" in str(exc.value)
