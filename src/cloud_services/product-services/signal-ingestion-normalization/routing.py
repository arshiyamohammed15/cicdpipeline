"""Routing engine stub."""
from __future__ import annotations

from typing import Callable, Dict, List

from .models import RoutingClass, RoutingRule, SignalEnvelope


class RoutingEngine:
    def __init__(self) -> None:
        self._rules: Dict[RoutingClass, List[RoutingRule]] = {rc: [] for rc in RoutingClass}
        self._consumers: Dict[str, Callable[[SignalEnvelope], bool]] = {}

    def register_rule(self, routing_class: RoutingClass, rule: RoutingRule) -> None:
        self._rules.setdefault(routing_class, []).append(rule)

    def register_consumer(self, destination: str, consumer: Callable[[SignalEnvelope], bool]) -> None:
        self._consumers[destination] = consumer

    def route(self, signal: SignalEnvelope) -> List[str]:
        delivered: List[str] = []
        for routing_class, rules in self._rules.items():
            for rule in rules:
                if rule.condition(signal):
                    dest = f"{routing_class.value}:{signal.tenant_id}"
                    consumer = self._consumers.get(dest) or self._consumers.get(rule.destination)
                    if consumer:
                        consumer(signal)
                    delivered.append(dest)
        return delivered
