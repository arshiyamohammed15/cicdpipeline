"""
Async performance runner that enforces PRD latency budgets.
"""

from __future__ import annotations

import asyncio
import statistics
from dataclasses import dataclass, field
from time import perf_counter
from typing import Awaitable, Callable, Dict, Iterable, List, Sequence


@dataclass
class PerfScenario:
    name: str
    iterations: int
    concurrency: int
    coroutine_factory: Callable[[], Awaitable[None]]
    latency_budget_ms: float


@dataclass
class PerfResult:
    name: str
    latencies_ms: List[float] = field(default_factory=list)

    @property
    def p50(self) -> float:
        return percentile(self.latencies_ms, 50.0)

    @property
    def p95(self) -> float:
        return percentile(self.latencies_ms, 95.0)

    @property
    def p99(self) -> float:
        return percentile(self.latencies_ms, 99.0)

    def to_dict(self) -> Dict[str, float]:
        return {"p50": self.p50, "p95": self.p95, "p99": self.p99}


class PerfRunner:
    """Runs async callables under configurable concurrency and captures latency stats."""

    def __init__(self, *, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self._loop = loop or asyncio.get_event_loop()

    async def run(self, scenarios: Sequence[PerfScenario]) -> List[PerfResult]:
        results: List[PerfResult] = []
        for scenario in scenarios:
            latencies: List[float] = []
            semaphore = asyncio.Semaphore(scenario.concurrency)

            async def worker() -> None:
                async with semaphore:
                    start = perf_counter()
                    await scenario.coroutine_factory()
                    elapsed_ms = (perf_counter() - start) * 1000
                    latencies.append(elapsed_ms)

            await asyncio.gather(*(worker() for _ in range(scenario.iterations)))
            result = PerfResult(name=scenario.name, latencies_ms=latencies)
            if result.p95 > scenario.latency_budget_ms:
                raise AssertionError(
                    f"Scenario {scenario.name} breached latency budget "
                    f"(p95={result.p95:.2f}ms > {scenario.latency_budget_ms}ms)"
                )
            results.append(result)
        return results


def percentile(values: Iterable[float], percentile_value: float) -> float:
    data = sorted(values)
    if not data:
        return 0.0
    k = (len(data) - 1) * (percentile_value / 100)
    f = int(k)
    c = min(f + 1, len(data) - 1)
    if f == c:
        return data[int(k)]
    d0 = data[f] * (c - k)
    d1 = data[c] * (k - f)
    return d0 + d1

