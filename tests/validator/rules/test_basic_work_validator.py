from __future__ import annotations
import pytest

import ast

from validator.rules.basic_work import BasicWorkValidator


@pytest.mark.unit
def test_validate_information_and_privacy_rules():
    validator = BasicWorkValidator()
    content = "assume value\nexternal_api.call()\npassword = 'secret'"

    info_violations = validator.validate_information_usage(content)
    privacy_violations = validator.validate_privacy_protection(content)

    assert any("Avoid assumptions" in v.message for v in info_violations)
    assert any("Accessing external data" in v.message for v in info_violations)
    assert any("privacy violation" in v.message for v in privacy_violations)


@pytest.mark.unit
def test_validate_settings_and_logging_and_ai():
    validator = BasicWorkValidator()
    content = "host = 'localhost'\ndef predict():\n    return model.predict(x)\n"
    tree = ast.parse(content)

    settings_violations = validator.validate_settings_files(tree, content, "file.py")
    logging_violations = validator.validate_logging_records(tree, content, "file.py")
    ai_violations = validator.validate_ai_transparency(tree, content, "file.py")

    assert any("hardcoded value" in v.message.lower() for v in settings_violations)
    assert any("No logging patterns" in v.message for v in logging_violations)
    assert any("confidence" in v.message.lower() for v in ai_violations)
    assert any("explanation" in v.message.lower() for v in ai_violations)


@pytest.mark.unit
def test_validate_learning_and_fairness():
    validator = BasicWorkValidator()
    content = "def func():\n    return True\n"
    tree = ast.parse(content)

    learning = validator.validate_learning_from_mistakes(tree, content, "file.py")
    fairness = validator.validate_fairness_accessibility(tree, content, "file.py")

    assert learning
    assert fairness
