"""
Routing engine for Signal Ingestion & Normalization (SIN) Module.

What: Routing & Fan-Out engine per PRD F6
Why: Deliver the right signals to the right consumers in a decoupled, scalable way
Reads/Writes: Signal routing decisions (no file I/O)
Contracts: PRD §4.6 (F6)
Risks: Routing rules must be tenant-aware and policy-driven
"""

import logging
from typing import Dict, Any, List, Optional, Callable

from .models import SignalEnvelope, RoutingClass

logger = logging.getLogger(__name__)


class RoutingError(Exception):
    """Exception raised by routing engine."""
    pass


class RoutingRule:
    """Routing rule definition."""

    def __init__(self, routing_class: RoutingClass, condition: Callable[[SignalEnvelope], bool],
                 destination: str, tenant_aware: bool = True):
        """
        Initialize routing rule.

        Args:
            routing_class: Routing class (realtime_detection, evidence_store, etc.)
            condition: Condition function that takes SignalEnvelope and returns bool
            destination: Destination identifier (queue/topic name)
            tenant_aware: Whether rule is tenant-aware (default: True)
        """
        self.routing_class = routing_class
        self.condition = condition
        self.destination = destination
        self.tenant_aware = tenant_aware


class RoutingEngine:
    """
    Routing and fan-out engine per F6.

    Per PRD F6:
    - Classify signals into routing classes
    - Policy-driven routing rules
    - Tenant-aware routing (no cross-tenant leakage)
    - Forward signals to queues/streams/adapters
    """

    def __init__(self):
        """Initialize routing engine."""
        # Routing rules: routing_class -> List[RoutingRule]
        self.routing_rules: Dict[RoutingClass, List[RoutingRule]] = {
            RoutingClass.REALTIME_DETECTION: [],
            RoutingClass.EVIDENCE_STORE: [],
            RoutingClass.ANALYTICS_STORE: [],
            RoutingClass.COST_OBSERVABILITY: []
        }
        # Downstream consumers: destination -> handler function
        self.consumers: Dict[str, Callable[[SignalEnvelope], bool]] = {}

    def register_rule(self, routing_class: RoutingClass, rule: RoutingRule) -> None:
        """
        Register routing rule.

        Args:
            routing_class: Routing class
            rule: Routing rule
        """
        if routing_class not in self.routing_rules:
            raise RoutingError(f"Unknown routing class: {routing_class}")

        self.routing_rules[routing_class].append(rule)
        logger.debug(f"Routing rule registered: {routing_class} -> {rule.destination}")

    def register_consumer(self, destination: str, handler: Callable[[SignalEnvelope], bool]) -> None:
        """
        Register downstream consumer handler.

        Args:
            destination: Destination identifier
            handler: Handler function that takes SignalEnvelope and returns success bool
        """
        self.consumers[destination] = handler
        logger.debug(f"Consumer registered: {destination}")

    def classify_signal(self, signal: SignalEnvelope) -> List[RoutingClass]:
        """
        Classify signal into routing classes per F6.

        Args:
            signal: SignalEnvelope to classify

        Returns:
            List of routing classes
        """
        routing_classes = []

        # Default classification based on signal type
        if signal.signal_type in ['pr_opened', 'test_failed', 'gate_evaluated']:
            routing_classes.append(RoutingClass.REALTIME_DETECTION)
            routing_classes.append(RoutingClass.EVIDENCE_STORE)

        if signal.signal_type in ['build_metric', 'error_rate', 'latency']:
            routing_classes.append(RoutingClass.ANALYTICS_STORE)
            routing_classes.append(RoutingClass.COST_OBSERVABILITY)

        # Apply routing rules
        for routing_class, rules in self.routing_rules.items():
            for rule in rules:
                if rule.condition(signal):
                    if routing_class not in routing_classes:
                        routing_classes.append(routing_class)

        return routing_classes

    def route_signal(self, signal: SignalEnvelope) -> List[tuple[RoutingClass, str, bool]]:
        """
        Route signal to consumers per F6.

        Args:
            signal: SignalEnvelope to route

        Returns:
            List of (routing_class, destination, success) tuples
        """
        routing_classes = self.classify_signal(signal)
        results = []

        for routing_class in routing_classes:
            rules = self.routing_rules.get(routing_class, [])

            for rule in rules:
                # Check condition
                if not rule.condition(signal):
                    continue

                # Tenant-aware routing check
                if rule.tenant_aware:
                    # Ensure destination includes tenant_id to prevent cross-tenant leakage
                    destination = f"{rule.destination}:{signal.tenant_id}"
                else:
                    destination = rule.destination

                # Forward to consumer
                if destination in self.consumers:
                    handler = self.consumers[destination]
                    try:
                        success = handler(signal)
                        results.append((routing_class, destination, success))
                        logger.debug(f"Signal routed: {routing_class} -> {destination} (success: {success})")
                    except Exception as e:
                        logger.error(f"Error routing signal to {destination}: {e}")
                        results.append((routing_class, destination, False))
                else:
                    logger.warning(f"No consumer registered for destination: {destination}")
                    results.append((routing_class, destination, False))

        return results

    def get_routing_classes(self, signal: SignalEnvelope) -> List[RoutingClass]:
        """
        Get routing classes for signal (without actually routing).

        Args:
            signal: SignalEnvelope

        Returns:
            List of routing classes
        """
        return self.classify_signal(signal)

