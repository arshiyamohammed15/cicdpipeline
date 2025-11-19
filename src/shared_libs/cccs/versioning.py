"""
API version helpers for CCCS runtime.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class APIVersion:
    """Semantic version representation."""

    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> "APIVersion":
        parts = value.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid semantic version: {value}")
        return cls(*(int(p) for p in parts))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_compatible_with(self, other: "APIVersion") -> bool:
        """Compatibility per PRD: major must match and self >= other."""
        return (
            self.major == other.major
            and (self.minor, self.patch) >= (other.minor, other.patch)
        )


