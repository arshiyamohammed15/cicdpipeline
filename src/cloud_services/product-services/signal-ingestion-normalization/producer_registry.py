"""Producer registry stub."""
from __future__ import annotations

from typing import Dict, Tuple

from .models import ProducerRegistration


class ProducerRegistryError(Exception):
    """Raised when producer registration or lookup fails."""


class ProducerRegistry:
    def __init__(self, schema_registry, budgeting) -> None:
        self.schema_registry = schema_registry
        self.budgeting = budgeting
        self._producers: Dict[str, Tuple[ProducerRegistration, str]] = {}

    def _ensure_contracts_exist(self, producer: ProducerRegistration) -> None:
        for signal_type, version in producer.contract_versions.items():
            contract = self.schema_registry.get_contract(signal_type, version)
            if contract is None:
                raise ProducerRegistryError(f"Contract {signal_type}:{version} not found")

    def register_producer(self, producer: ProducerRegistration, tenant_id: str) -> ProducerRegistration:
        if producer.producer_id in self._producers:
            raise ProducerRegistryError(f"Producer {producer.producer_id} already registered")
        self._ensure_contracts_exist(producer)
        self._producers[producer.producer_id] = (producer, tenant_id)
        return producer

    def update_producer(self, producer: ProducerRegistration, tenant_id: str) -> ProducerRegistration:
        existing = self._producers.get(producer.producer_id)
        if existing is None:
            raise ProducerRegistryError(f"Producer {producer.producer_id} not found")
        _, owner_tenant = existing
        if owner_tenant and tenant_id and owner_tenant != tenant_id:
            raise ProducerRegistryError("producer owned by different tenant")
        self._ensure_contracts_exist(producer)
        self._producers[producer.producer_id] = (producer, owner_tenant or tenant_id)
        return producer

    def get_producer(self, producer_id: str) -> ProducerRegistration:
        entry = self._producers.get(producer_id)
        producer = entry[0] if entry else None
        if not producer:
            raise ProducerRegistryError(f"Producer {producer_id} not found")
        return producer

    def get_producer_entry(self, producer_id: str) -> Tuple[ProducerRegistration, str]:
        entry = self._producers.get(producer_id)
        if not entry:
            raise ProducerRegistryError(f"Producer {producer_id} not found")
        return entry

    def tenant_for(self, producer_id: str) -> str:
        entry = self._producers.get(producer_id)
        if entry:
            return entry[1]
        raise ProducerRegistryError(f"Producer {producer_id} not found")

    def list_producers(self):
        return [p for p, _ in self._producers.values()]
