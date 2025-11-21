"""
Normalization engine for Signal Ingestion & Normalization (SIN) Module.

What: Normalization and enrichment engine per PRD F5
Why: Turn heterogeneous raw events into consistent canonical signals
Reads/Writes: Signal transformation (no file I/O)
Contracts: PRD §4.5 (F5)
Risks: Normalization rules must be configurable, not hard-coded
"""

import logging
from typing import Dict, Any, Optional, List

from .models import SignalEnvelope, Resource, CoercionWarning
from .dependencies import MockM34SchemaRegistry

logger = logging.getLogger(__name__)


class NormalizationError(Exception):
    """Exception raised by normalization engine."""
    pass


class NormalizationEngine:
    """
    Normalization and enrichment engine per F5.

    Per PRD F5:
    - Map source-specific field names to canonical names
    - Normalize units (time to ms, sizes to bytes, percentages to 0-100)
    - Attach actor context, resource context, correlation context
    - Tag signals with module/pain-point classification
    - Normalization logic must be configurable via data contracts and transformation rules
    """

    def __init__(self, schema_registry: Optional[MockM34SchemaRegistry] = None):
        """
        Initialize normalization engine.

        Args:
            schema_registry: Schema registry for transformation rules
        """
        self.schema_registry = schema_registry or MockM34SchemaRegistry()
        # Field mapping rules: signal_type -> {source_field: target_field}
        self.field_mappings: Dict[str, Dict[str, str]] = {}
        # Unit conversion rules: signal_type -> {field: {source_unit: target_unit, factor}}
        self.unit_conversions: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]] = {}
        # Module/pain-point classification rules
        self.classification_rules: Dict[str, str] = {}

    def _load_transformation_rules(self, signal_type: str) -> None:
        """
        Load transformation rules from schema registry for signal type.

        Args:
            signal_type: Signal type
        """
        # Get contract from registry (contains transformation rules)
        contract_data = self.schema_registry.get_contract(signal_type, "1.0.0")
        if not contract_data:
            # Try to get latest version
            versions = self.schema_registry.list_contract_versions(signal_type)
            if versions:
                contract_data = self.schema_registry.get_contract(signal_type, versions[-1])

        if contract_data:
            definition = contract_data.get('definition', contract_data)
            # Extract field mappings
            if 'field_mappings' in definition:
                self.field_mappings[signal_type] = definition['field_mappings']
            # Extract unit conversions
            if 'unit_conversions' in definition:
                self.unit_conversions[signal_type] = definition['unit_conversions']
            # Extract classification rules
            if 'classification' in definition:
                self.classification_rules[signal_type] = definition['classification']

    def normalize(self, signal: SignalEnvelope, warnings: Optional[List[CoercionWarning]] = None) -> SignalEnvelope:
        """
        Normalize signal per F5.

        Args:
            signal: Raw SignalEnvelope to normalize
            warnings: Optional list to append coercion warnings

        Returns:
            Normalized SignalEnvelope
        """
        if warnings is None:
            warnings = []

        # Load transformation rules for this signal type
        self._load_transformation_rules(signal.signal_type)

        # Create normalized payload copy
        normalized_payload = signal.payload.copy()

        # Apply field name mapping
        mappings = self.field_mappings.get(signal.signal_type, {})
        for source_field, target_field in mappings.items():
            if source_field in normalized_payload:
                value = normalized_payload.pop(source_field)
                normalized_payload[target_field] = value
                logger.debug(f"Mapped field {source_field} -> {target_field}")

        # Apply unit normalization
        conversions = self.unit_conversions.get(signal.signal_type, {})
        for field, conversion_rules in conversions.items():
            if field in normalized_payload:
                value = normalized_payload[field]
                original_value = value

                # Get source unit (if provided in payload)
                source_unit = normalized_payload.get(f"{field}_unit", "unknown")
                target_unit = conversion_rules.get('target_unit', 'ms')  # Default to ms for time

                # Apply conversion
                if isinstance(value, (int, float)):
                    factor = conversion_rules.get('factors', {}).get(source_unit, 1.0)
                    normalized_value = value * factor
                    normalized_payload[field] = normalized_value
                    normalized_payload[f"{field}_unit"] = target_unit

                    if factor != 1.0:
                        warnings.append(CoercionWarning(
                            field_path=f"payload.{field}",
                            original_value=original_value,
                            coerced_value=normalized_value,
                            warning_message=f"Unit converted from {source_unit} to {target_unit} (factor: {factor})"
                        ))

        # Create normalized signal
        normalized_signal = SignalEnvelope(
            signal_id=signal.signal_id,
            tenant_id=signal.tenant_id,
            environment=signal.environment,
            producer_id=signal.producer_id,
            actor_id=signal.actor_id,
            signal_kind=signal.signal_kind,
            signal_type=signal.signal_type,
            occurred_at=signal.occurred_at,
            ingested_at=signal.ingested_at,
            trace_id=signal.trace_id,
            span_id=signal.span_id,
            correlation_id=signal.correlation_id,
            resource=signal.resource,
            payload=normalized_payload,
            schema_version=signal.schema_version,
            sequence_no=signal.sequence_no
        )

        return normalized_signal

    def enrich(self, signal: SignalEnvelope, actor_context: Optional[Dict[str, Any]] = None,
               resource_context: Optional[Dict[str, Any]] = None) -> SignalEnvelope:
        """
        Enrich signal with actor and resource context per F5.

        Args:
            signal: SignalEnvelope to enrich
            actor_context: Optional actor context (actor_id, role, persona)
            resource_context: Optional resource context (repo, branch, PR ID, etc.)

        Returns:
            Enriched SignalEnvelope
        """
        # Attach actor context
        if actor_context:
            if 'actor_id' in actor_context and not signal.actor_id:
                signal.actor_id = actor_context['actor_id']
            # Store additional actor context in payload if needed
            if 'role' in actor_context or 'persona' in actor_context:
                if 'actor_context' not in signal.payload:
                    signal.payload['actor_context'] = {}
                if 'role' in actor_context:
                    signal.payload['actor_context']['role'] = actor_context['role']
                if 'persona' in actor_context:
                    signal.payload['actor_context']['persona'] = actor_context['persona']

        # Attach resource context
        if resource_context:
            if not signal.resource:
                signal.resource = Resource()

            for key, value in resource_context.items():
                if hasattr(signal.resource, key):
                    setattr(signal.resource, key, value)

        # Tag with module/pain-point classification
        classification = self.classification_rules.get(signal.signal_type)
        if classification:
            if 'classification' not in signal.payload:
                signal.payload['classification'] = {}
            signal.payload['classification']['module'] = classification

        return signal

    def normalize_units(self, value: float, source_unit: str, target_unit: str) -> tuple[float, bool]:
        """
        Normalize units per F5.

        Args:
            value: Value to convert
            source_unit: Source unit
            target_unit: Target unit

        Returns:
            (converted_value, was_converted) tuple
        """
        # Time conversions to milliseconds
        time_to_ms = {
            's': 1000.0,
            'sec': 1000.0,
            'seconds': 1000.0,
            'm': 60000.0,
            'min': 60000.0,
            'minutes': 60000.0,
            'h': 3600000.0,
            'hr': 3600000.0,
            'hours': 3600000.0,
            'ms': 1.0,
            'milliseconds': 1.0,
            'us': 0.001,
            'microseconds': 0.001,
            'ns': 0.000001,
            'nanoseconds': 0.000001
        }

        # Size conversions to bytes
        size_to_bytes = {
            'b': 1.0,
            'bytes': 1.0,
            'kb': 1024.0,
            'kilobytes': 1024.0,
            'mb': 1048576.0,
            'megabytes': 1048576.0,
            'gb': 1073741824.0,
            'gigabytes': 1073741824.0,
            'tb': 1099511627776.0,
            'terabytes': 1099511627776.0
        }

        # Percentage normalization (to 0-100 range)
        if target_unit == 'percent' and source_unit in ['decimal', 'ratio']:
            return value * 100.0, True

        # Time normalization
        if target_unit == 'ms' and source_unit in time_to_ms:
            return value * time_to_ms[source_unit], True

        # Size normalization
        if target_unit == 'bytes' and source_unit in size_to_bytes:
            return value * size_to_bytes[source_unit], True

        # No conversion needed
        if source_unit == target_unit:
            return value, False

        # Unknown conversion
        logger.warning(f"Unknown unit conversion: {source_unit} -> {target_unit}")
        return value, False

