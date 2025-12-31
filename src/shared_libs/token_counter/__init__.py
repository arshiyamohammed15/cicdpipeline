"""
Token counting abstractions for request budgeting.

Counts are estimates and do not attempt vendor tokenizer parity.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence, Union

Message = Mapping[str, str]
TextOrMessages = Union[str, Sequence[Message]]


class TokenCounter(Protocol):
    """Interface for token counting in budget checks."""

    def count_input(self, text_or_messages: TextOrMessages) -> int:
        """Return the estimated token count for input text or messages."""

    def estimate_output(self, max_output_tokens_requested: int) -> int:
        """Return the estimated output tokens for a requested max."""


def _messages_to_text(messages: Sequence[Message]) -> str:
    parts: list[str] = []
    for message in messages:
        for key in sorted(message.keys()):
            value = message.get(key)
            if value is None:
                continue
            parts.append(f"{key}:{value}")
    return "\n".join(parts)


@dataclass(frozen=True)
class ConservativeTokenEstimator:
    """
    Deterministic token estimator based on character length.

    This is an estimate only; it does not attempt to match any tokenizer.
    """

    chars_per_token: int = 4

    def count_input(self, text_or_messages: TextOrMessages) -> int:
        if isinstance(text_or_messages, str):
            text = text_or_messages
        else:
            text = _messages_to_text(text_or_messages)

        if not text:
            return 0
        return math.ceil(len(text) / self.chars_per_token)

    def estimate_output(self, max_output_tokens_requested: int) -> int:
        return max_output_tokens_requested


__all__ = [
    "ConservativeTokenEstimator",
    "Message",
    "TextOrMessages",
    "TokenCounter",
]
