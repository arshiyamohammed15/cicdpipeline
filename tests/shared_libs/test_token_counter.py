from __future__ import annotations

import pytest

from src.shared_libs.token_counter import ConservativeTokenEstimator


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", 0),
        ("a", 1),
        ("abcd", 1),
        ("abcde", 2),
    ],
)
def test_conservative_token_estimator_text_counts_are_deterministic(
    text: str, expected: int
) -> None:
    counter = ConservativeTokenEstimator(chars_per_token=4)

    assert counter.count_input(text) == expected
    assert counter.count_input(text) == expected


def test_conservative_token_estimator_message_counts_are_deterministic() -> None:
    counter = ConservativeTokenEstimator(chars_per_token=4)
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ]
    messages_reordered = [
        {"content": "Hello", "role": "user"},
        {"content": "Hi", "role": "assistant"},
    ]

    assert counter.count_input(messages) == 13
    assert counter.count_input(messages_reordered) == 13
    assert counter.count_input(messages) == counter.count_input(messages_reordered)


def test_conservative_token_estimator_estimate_output_pass_through() -> None:
    counter = ConservativeTokenEstimator()

    assert counter.estimate_output(128) == 128
    assert counter.estimate_output(128) == counter.estimate_output(128)
