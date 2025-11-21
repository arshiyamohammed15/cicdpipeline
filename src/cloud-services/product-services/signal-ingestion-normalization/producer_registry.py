"""
Producer Registry for Signal Ingestion & Normalization (SIN) Module.

What: Producer registration and data contract management per PRD F2
Why: Ensure all producers obey schema and governance rules
Reads/Writes: In-memory registry (can be replaced with persistent storage)
Contracts: PRD §4.2 (F2)
Risks: Registry must be shared/distributed for horizontal scaling
"""

import logging
from typing import Dict, Optional, List

from .models import ProducerRegistration, DataContract, SignalKind, SignalEnvelope
from .dependencies import MockM34SchemaRegistry, MockM35Budgeting

logger = logging.getLogger(__name__)


class ProducerRegistryError(Exception):
    """Exception raised by ProducerRegistry."""
    pass


class ProducerRegistry:
    """
    Producer registry per F2.1 and data contract management per F2.2.

    Per PRD F2.1: Maintain registry of producers with allowed signal kinds/types, schema versions, quotas.
    Per PRD F2.2: Maintain data contracts per signal_type with validation rules, PII flags, classification.
    """

    def __init__(self, schema_registry: Optional[MockM34SchemaRegistry] = None, budgeting: Optional[MockM35Budgeting] = None):
        """
        Initialize producer registry.

        Args:
            schema_registry: Schema registry dependency (for contract storage)
            budgeting: Budgeting dependency (for quota retrieval)
        """
        self.schema_registry = schema_registry or MockM34SchemaRegistry()
        self.budgeting = budgeting or MockM35Budgeting()
        # In-memory registry: producer_id -> ProducerRegistration
        self.producers: Dict[str, ProducerRegistration] = {}
        # Data contracts: signal_type:version -> DataContract
        self.contracts: Dict[str, DataContract] = {}

    def register_producer(self, producer: ProducerRegistration) -> None:
        """
        Register a producer per F2.1.

        Args:
            producer: Producer registration data

        Raises:
            ProducerRegistryError: If registration fails
        """
        if producer.producer_id in self.producers:
            raise ProducerRegistryError(f"Producer {producer.producer_id} already registered")

        # Validate contract versions exist in schema registry
        for signal_type, version in producer.contract_versions.items():
            contract = self.schema_registry.get_contract(signal_type, version)
            if contract is None:
                raise ProducerRegistryError(
                    f"Contract version {version} for signal_type {signal_type} not found in schema registry. "
                    "Contracts must be registered in schema registry before producer registration."
                )

        # Get quota from budgeting (per PRD F2.1: sourced from policy, not hard-coded)
        if producer.max_rate_per_minute is None:
            # Try to get from budgeting
            quota = self.budgeting.quotas.get(f"{producer.producer_id}:quota", {})
            producer.max_rate_per_minute = quota.get('max_rate_per_minute')

        self.producers[producer.producer_id] = producer
        logger.info(f"Producer registered: {producer.producer_id}")

    def get_producer(self, producer_id: str) -> Optional[ProducerRegistration]:
        """
        Get producer by ID.

        Args:
            producer_id: Producer ID

        Returns:
            ProducerRegistration or None if not found
        """
        return self.producers.get(producer_id)

    def update_producer(self, producer_id: str, producer: ProducerRegistration) -> None:
        """
        Update producer registration.

        Args:
            producer_id: Producer ID
            producer: Updated producer registration

        Raises:
            ProducerRegistryError: If producer not found or update fails
        """
        if producer_id not in self.producers:
            raise ProducerRegistryError(f"Producer {producer_id} not found")

        if producer.producer_id != producer_id:
            raise ProducerRegistryError("Producer ID mismatch")

        # Validate contract versions exist in schema registry
        for signal_type, version in producer.contract_versions.items():
            contract = self.schema_registry.get_contract(signal_type, version)
            if contract is None:
                raise ProducerRegistryError(
                    f"Contract version {version} for signal_type {signal_type} not found in schema registry"
                )

        self.producers[producer_id] = producer
        logger.info(f"Producer updated: {producer_id}")

    def is_signal_type_allowed(self, producer_id: str, signal_kind: SignalKind, signal_type: str) -> bool:
        """
        Check if producer is allowed to send signal type per F2.1.

        Args:
            producer_id: Producer ID
            signal_kind: Signal kind
            signal_type: Signal type

        Returns:
            True if allowed, False otherwise
        """
        producer = self.get_producer(producer_id)
        if not producer:
            return False

        if signal_kind not in producer.allowed_signal_kinds:
            return False

        if signal_type not in producer.allowed_signal_types:
            return False

        return True

    def get_contract_version(self, producer_id: str, signal_type: str) -> Optional[str]:
        """
        Get contract version for producer and signal type.

        Args:
            producer_id: Producer ID
            signal_type: Signal type

        Returns:
            Contract version or None
        """
        producer = self.get_producer(producer_id)
        if not producer:
            return None

        return producer.contract_versions.get(signal_type)

    def register_contract(self, contract: DataContract) -> None:
        """
        Register data contract per F2.2.

        Args:
            contract: Data contract

        Raises:
            ProducerRegistryError: If registration fails
        """
        key = f"{contract.signal_type}:{contract.contract_version}"

        # Store in schema registry (per PRD F2.2: stored in shared schema registry)
        self.schema_registry.register_contract(
            contract.signal_type,
            contract.contract_version,
            contract.model_dump()
        )

        # Also store locally for quick lookup
        self.contracts[key] = contract
        logger.info(f"Data contract registered: {key}")

    def get_contract(self, signal_type: str, version: str) -> Optional[DataContract]:
        """
        Get data contract for signal type and version.

        Args:
            signal_type: Signal type
            version: Contract version

        Returns:
            DataContract or None if not found
        """
        key = f"{signal_type}:{version}"

        # Try local cache first
        if key in self.contracts:
            return self.contracts[key]

        # Fall back to schema registry
        contract_data = self.schema_registry.get_contract(signal_type, version)
        if contract_data:
            contract = DataContract(**contract_data.get('definition', contract_data))
            self.contracts[key] = contract  # Cache locally
            return contract

        return None

    def list_contract_versions(self, signal_type: str) -> List[str]:
        """
        List all registered contract versions for signal type.

        Args:
            signal_type: Signal type

        Returns:
            List of version strings
        """
        return self.schema_registry.list_contract_versions(signal_type)

    def validate_signal_contract(self, signal: SignalEnvelope) -> tuple[bool, Optional[str]]:
        """
        Validate signal against producer's contract version per F2.2.

        Args:
            signal: SignalEnvelope to validate

        Returns:
            (is_valid, error_message) tuple
        """
        # Get producer
        producer = self.get_producer(signal.producer_id)
        if not producer:
            return False, f"Producer {signal.producer_id} not registered"

        # Get contract version
        contract_version = producer.contract_versions.get(signal.signal_type)
        if not contract_version:
            return False, f"Producer {signal.producer_id} has no contract for signal_type {signal.signal_type}"

        # Get contract
        contract = self.get_contract(signal.signal_type, contract_version)
        if not contract:
            return False, f"Contract {contract_version} for signal_type {signal.signal_type} not found"

        # Validate required fields
        for field in contract.required_fields:
            if field not in signal.payload:
                return False, f"Required field '{field}' missing in payload"

        # Validate disallowed fields
        if contract.disallowed_fields:
            for field in contract.disallowed_fields:
                if field in signal.payload:
                    return False, f"Disallowed field '{field}' present in payload"

        return True, None

    def get_all_producers(self) -> List[ProducerRegistration]:
        """
        Get all registered producers.

        Returns:
            List of ProducerRegistration
        """
        return list(self.producers.values())

