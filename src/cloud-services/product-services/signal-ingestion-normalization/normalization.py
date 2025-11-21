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

# Constants for unit types
TARGET_UNIT_MS = "ms"
TARGET_UNIT_BYTES = "bytes"
TARGET_UNIT_PERCENT = "percent"
SOURCE_UNIT_UNKNOWN = "unknown"

# Constants for field name patterns
FIELD_PATTERN_TIME = ["time", "duration", "latency"]
FIELD_PATTERN_SIZE = ["size", "bytes", "memory"]
FIELD_PATTERN_PERCENT = ["percent", "ratio"]


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
        # Unit conversion rules: signal_type -> {field: {target_unit: str, factors: {source_unit: factor}}}
        # Type: Dict[str, Dict[str, Dict[str, Any]]]
        # Structure: signal_type -> field_name -> {target_unit: str, factors: Dict[str, float]}
        self.unit_conversions: Dict[str, Dict[str, Dict[str, Any]]] = {}
        # Module/pain-point classification rules: signal_type -> classification string
        self.classification_rules: Dict[str, str] = {}
        
        # Thread safety note: These instance variables are shared across calls.
        # In a multi-threaded environment, consider using thread-local storage or locks
        # if transformation rules are modified during runtime.

    def _load_transformation_rules(self, signal_type: str, contract_version: Optional[str] = None) -> None:
        """
        Load transformation rules from schema registry for signal type.

        Args:
            signal_type: Signal type
            contract_version: Optional contract version (if None, tries latest or "1.0.0")
        
        Unit conversion rules structure:
        {
            "field_name": {
                "target_unit": "ms",  # or "bytes", "percent", etc.
                "factors": {
                    "s": 1000.0,
                    "sec": 1000.0,
                    # ... source_unit -> conversion_factor
                }
            }
        }
        """
        try:
            # Get contract from registry (contains transformation rules)
            if contract_version:
                contract_data = self.schema_registry.get_contract(signal_type, contract_version)
            else:
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
                    field_mappings = definition['field_mappings']
                    if isinstance(field_mappings, dict):
                        self.field_mappings[signal_type] = field_mappings
                    else:
                        logger.warning(f"Invalid field_mappings format for {signal_type}, expected dict")
                # Extract unit conversions
                if 'unit_conversions' in definition:
                    unit_conversions = definition['unit_conversions']
                    if isinstance(unit_conversions, dict):
                        self.unit_conversions[signal_type] = unit_conversions
                    else:
                        logger.warning(f"Invalid unit_conversions format for {signal_type}, expected dict")
                # Extract classification rules
                if 'classification' in definition:
                    classification = definition['classification']
                    if isinstance(classification, str):
                        self.classification_rules[signal_type] = classification
                    else:
                        logger.warning(f"Invalid classification format for {signal_type}, expected string")
        except Exception as e:
            logger.error(f"Error loading transformation rules for {signal_type}: {e}")
            # Continue with empty rules rather than failing completely

    def normalize(self, signal: SignalEnvelope, warnings: Optional[List[CoercionWarning]] = None,
                  contract_version: Optional[str] = None) -> SignalEnvelope:
        """
        Normalize signal per F5.

        Args:
            signal: Raw SignalEnvelope to normalize
            warnings: Optional list to append coercion warnings
            contract_version: Optional contract version to use for transformation rules.
                            If None, tries "1.0.0" or latest version.
                            Note: Ideally should use producer's declared contract version,
                            but requires access to producer_registry (architectural limitation).

        Returns:
            Normalized SignalEnvelope

        Example:
            >>> normalized = engine.normalize(signal, warnings=[], contract_version="2.0.0")
        """
        if warnings is None:
            warnings = []

        # Load transformation rules for this signal type
        # Note: In an ideal architecture, we would get contract_version from producer_registry
        # based on signal.producer_id and signal.signal_type. This would require either:
        # 1. Passing producer_registry to NormalizationEngine, or
        # 2. Passing contract_version from the caller (services.py) which has access to producer_registry
        # For now, we accept contract_version as optional parameter and fall back to default behavior
        self._load_transformation_rules(signal.signal_type, contract_version)

        # Create normalized payload copy
        normalized_payload = signal.payload.copy()

        # Apply field name mapping
        mappings = self.field_mappings.get(signal.signal_type, {})
        # Early return optimization if no mappings exist
        if not mappings:
            logger.debug(f"No field mappings for signal_type {signal.signal_type}")
        else:
            logger.info(f"Applying {len(mappings)} field mappings for signal_type {signal.signal_type}")
        
        for source_field, target_field in mappings.items():
            if source_field in normalized_payload:
                # Check if target field already exists
                if target_field in normalized_payload and target_field != source_field:
                    logger.warning(f"Target field {target_field} already exists, overwriting with {source_field}")
                value = normalized_payload.pop(source_field)
                normalized_payload[target_field] = value
                logger.debug(f"Mapped field {source_field} -> {target_field}")

        # Validate payload is not empty after field mapping
        if not normalized_payload:
            raise NormalizationError(f"Payload is empty after field mapping for signal_type {signal.signal_type}")

        # Apply unit normalization using normalize_units() method
        conversions = self.unit_conversions.get(signal.signal_type, {})
        # Early return optimization if no conversions exist
        if not conversions:
            logger.debug(f"No unit conversions for signal_type {signal.signal_type}")
        else:
            logger.info(f"Applying unit conversions for {len(conversions)} fields in signal_type {signal.signal_type}")
        
        for field, conversion_rules in conversions.items():
            if field in normalized_payload:
                value = normalized_payload[field]
                original_value = value

                # Get source unit (if provided in payload)
                source_unit = normalized_payload.get(f"{field}_unit", SOURCE_UNIT_UNKNOWN)
                # Determine target unit from rules, with intelligent default based on field type
                target_unit = conversion_rules.get('target_unit')
                if not target_unit:
                    # Default based on common patterns: time fields -> ms, size fields -> bytes
                    field_lower = field.lower()
                    if any(pattern in field_lower for pattern in FIELD_PATTERN_TIME):
                        target_unit = TARGET_UNIT_MS
                    elif any(pattern in field_lower for pattern in FIELD_PATTERN_SIZE):
                        target_unit = TARGET_UNIT_BYTES
                    elif any(pattern in field_lower for pattern in FIELD_PATTERN_PERCENT):
                        target_unit = TARGET_UNIT_PERCENT
                    else:
                        # If no pattern matches and no target_unit specified, skip conversion
                        logger.warning(f"No target_unit specified for field {field}, skipping unit conversion")
                        continue

                # Apply conversion using normalize_units() method
                # Validate value is numeric (int, float, or numeric string)
                if isinstance(value, (int, float)):
                    # Value is already numeric
                    pass
                elif isinstance(value, str):
                    # Try to convert string to number
                    try:
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except (ValueError, TypeError):
                        logger.warning(f"Field {field} has non-numeric value: {value}, skipping unit conversion")
                        continue
                else:
                    logger.warning(f"Field {field} has non-numeric type {type(value).__name__}, skipping unit conversion")
                    continue
                
                # Now value is guaranteed to be numeric
                normalized_value, was_converted = self.normalize_units(float(value), source_unit, target_unit)
                    if was_converted:
                        # Conversion was successful
                        normalized_payload[field] = normalized_value
                        normalized_payload[f"{field}_unit"] = target_unit
                        warnings.append(CoercionWarning(
                            field_path=f"payload.{field}",
                            original_value=original_value,
                            coerced_value=normalized_value,
                            warning_message=f"Unit converted from {source_unit} to {target_unit}"
                        ))
                    elif source_unit == target_unit:
                        # No conversion needed, just set the unit
                        normalized_payload[f"{field}_unit"] = target_unit
                    elif source_unit == SOURCE_UNIT_UNKNOWN:
                        # Source unit was unknown, set target unit but don't convert value
                        warnings.append(CoercionWarning(
                            field_path=f"payload.{field}_unit",
                            original_value=source_unit,
                            coerced_value=target_unit,
                            warning_message=f"Source unit was unknown, assuming {target_unit} (value not converted)"
                        ))
                        normalized_payload[f"{field}_unit"] = target_unit
                    else:
                        # Conversion failed (unknown conversion), log warning but don't modify
                        logger.warning(f"Unit conversion failed for field {field}: {source_unit} -> {target_unit}")
                        warnings.append(CoercionWarning(
                            field_path=f"payload.{field}_unit",
                            original_value=source_unit,
                            coerced_value=source_unit,
                            warning_message=f"Unknown unit conversion: {source_unit} -> {target_unit}, keeping original unit"
                        ))

        # Apply classification rules (even if enrich() is not called)
        classification = self.classification_rules.get(signal.signal_type)
        if classification:
            if not isinstance(classification, str):
                logger.warning(f"Invalid classification type for {signal.signal_type}: {type(classification).__name__}, expected string")
            else:
                if 'classification' not in normalized_payload:
                    normalized_payload['classification'] = {}
                normalized_payload['classification']['module'] = classification
                logger.info(f"Applied classification '{classification}' to signal_type {signal.signal_type}")

        # Create normalized signal
        # Note: Correlation context (trace_id, span_id, correlation_id) is preserved from original signal
        # PRD F5 requires correlation context attachment, which is already present in SignalEnvelope model
        # If additional correlation context enrichment is needed, it should be done in enrich() method
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

        # Pydantic validation ensures the SignalEnvelope is properly constructed
        # No additional validation needed here

        return normalized_signal

    def enrich(self, signal: SignalEnvelope, actor_context: Optional[Dict[str, Any]] = None,
               resource_context: Optional[Dict[str, Any]] = None) -> SignalEnvelope:
        """
        Enrich signal with actor and resource context per F5.

        Args:
            signal: SignalEnvelope to enrich
            actor_context: Optional actor context dict with keys: actor_id, role, persona
            resource_context: Optional resource context dict with Resource model field names

        Returns:
            Enriched SignalEnvelope

        Example:
            >>> engine.enrich(signal, 
            ...     actor_context={'actor_id': 'user123', 'role': 'developer'},
            ...     resource_context={'repository': 'org/repo', 'branch': 'main'})
        """
        # Validate and attach actor context
        if actor_context:
            if not isinstance(actor_context, dict):
                logger.warning(f"Invalid actor_context type: {type(actor_context).__name__}, expected dict")
            else:
                if 'actor_id' in actor_context and not signal.actor_id:
                    actor_id = actor_context['actor_id']
                    if isinstance(actor_id, str):
                        signal.actor_id = actor_id
                    else:
                        logger.warning(f"Invalid actor_id type: {type(actor_id).__name__}, expected string")
                
                # Store additional actor context in payload if needed
                if 'role' in actor_context or 'persona' in actor_context:
                    if 'actor_context' not in signal.payload:
                        signal.payload['actor_context'] = {}
                    if 'role' in actor_context:
                        signal.payload['actor_context']['role'] = actor_context['role']
                    if 'persona' in actor_context:
                        signal.payload['actor_context']['persona'] = actor_context['persona']

        # Validate and attach resource context
        if resource_context:
            if not isinstance(resource_context, dict):
                logger.warning(f"Invalid resource_context type: {type(resource_context).__name__}, expected dict")
            else:
                try:
                    if not signal.resource:
                        signal.resource = Resource()
                    
                    # Validate resource context keys against Resource model
                    from .models import Resource as ResourceModel
                    valid_resource_fields = set(ResourceModel.model_fields.keys())
                    
                    for key, value in resource_context.items():
                        if key in valid_resource_fields:
                            setattr(signal.resource, key, value)
                        else:
                            logger.warning(f"Invalid resource context key: {key}, not a Resource model field")
                except Exception as e:
                    logger.error(f"Error creating or updating Resource: {e}")
                    # Continue without resource context rather than failing

        # Tag with module/pain-point classification
        classification = self.classification_rules.get(signal.signal_type)
        if classification:
            if not isinstance(classification, str):
                logger.warning(f"Invalid classification type for {signal.signal_type}: {type(classification).__name__}")
            else:
                if 'classification' not in signal.payload:
                    signal.payload['classification'] = {}
                signal.payload['classification']['module'] = classification
                logger.info(f"Applied classification '{classification}' via enrich() for signal_type {signal.signal_type}")

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
        if target_unit == TARGET_UNIT_PERCENT and source_unit in ['decimal', 'ratio']:
            return value * 100.0, True

        # Time normalization
        if target_unit == TARGET_UNIT_MS and source_unit in time_to_ms:
            return value * time_to_ms[source_unit], True

        # Size normalization
        if target_unit == TARGET_UNIT_BYTES and source_unit in size_to_bytes:
            return value * size_to_bytes[source_unit], True

        # No conversion needed
        if source_unit == target_unit:
            return value, False

        # Unknown conversion
        logger.warning(f"Unknown unit conversion: {source_unit} -> {target_unit}")
        return value, False

