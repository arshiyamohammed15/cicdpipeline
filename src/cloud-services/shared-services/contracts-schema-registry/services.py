"""
Service layer for Contracts & Schema Registry (M34).

What: Business logic for schema management, validation, contract enforcement per PRD v1.2.0
Why: Encapsulates registry logic, provides abstraction for route handlers
Reads/Writes: Reads/writes schemas, contracts, analytics via database and dependencies
Contracts: PRD API contract, validation contract, compatibility contract
Risks: Performance degradation, data inconsistency, tenant isolation violations
"""

import hashlib
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .database.connection import get_session
from .database.models import Schema, Contract, SchemaDependency, SchemaAnalytics
from .validators.json_schema_validator import JSONSchemaValidator
from .validators.avro_validator import AvroValidator
from .validators.protobuf_validator import ProtobufValidator
from .validators.custom_validator import CustomValidator
from .compatibility.checker import CompatibilityChecker, CompatibilityMode
from .compatibility.transformer import DataTransformer
from .cache.manager import CacheManager
from .dependencies import MockM33KMS, MockM27EvidenceLedger, MockM29DataPlane, MockM21IAM
from .errors import ErrorCode, create_error_response, get_http_status
from .models import (
    SchemaMetadata, ContractDefinition, ValidationResult, ValidationError,
    CompatibilityResult, TransformationResult
)

logger = logging.getLogger(__name__)

# Per PRD constraints
MAX_SCHEMA_SIZE = 1024 * 1024  # 1MB
MAX_FIELDS_PER_SCHEMA = 1000
MAX_NESTING_DEPTH = 10
MAX_SCHEMA_VERSIONS = 100
MAX_SCHEMAS_PER_TENANT = 10000


class MetricsCollector:
    """
    Metrics collector for schema registry operations.

    Tracks: validation counts, contract enforcement, compatibility checks, latencies, cache hit rates.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self.schema_validation_count = 0
        self.contract_enforcement_count = 0
        self.compatibility_check_count = 0
        self.schema_registration_count = 0
        self.validation_latencies = []
        self.contract_latencies = []
        self.compatibility_latencies = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.errors = {}

    def record_validation(self, latency_ms: float, cache_hit: bool = False):
        """Record schema validation."""
        self.schema_validation_count += 1
        self.validation_latencies.append(latency_ms)
        if len(self.validation_latencies) > 1000:
            self.validation_latencies = self.validation_latencies[-1000:]
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def record_contract_enforcement(self, latency_ms: float):
        """Record contract enforcement."""
        self.contract_enforcement_count += 1
        self.contract_latencies.append(latency_ms)
        if len(self.contract_latencies) > 1000:
            self.contract_latencies = self.contract_latencies[-1000:]

    def record_compatibility_check(self, latency_ms: float, cache_hit: bool = False):
        """Record compatibility check."""
        self.compatibility_check_count += 1
        self.compatibility_latencies.append(latency_ms)
        if len(self.compatibility_latencies) > 1000:
            self.compatibility_latencies = self.compatibility_latencies[-1000:]
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def record_schema_registration(self):
        """Record schema registration."""
        self.schema_registration_count += 1

    def record_error(self, error_code: str):
        """Record error."""
        self.errors[error_code] = self.errors.get(error_code, 0) + 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        total_requests = self.schema_validation_count + self.contract_enforcement_count + self.compatibility_check_count
        error_count = sum(self.errors.values())
        error_rate = error_count / total_requests if total_requests > 0 else 0.0

        cache_total = self.cache_hits + self.cache_misses
        cache_hit_rate = self.cache_hits / cache_total if cache_total > 0 else 0.0

        def avg_latency(latencies):
            return sum(latencies) / len(latencies) if latencies else 0.0

        return {
            "schema_validation_count": self.schema_validation_count,
            "contract_enforcement_count": self.contract_enforcement_count,
            "compatibility_check_count": self.compatibility_check_count,
            "schema_registration_count": self.schema_registration_count,
            "average_validation_latency_ms": avg_latency(self.validation_latencies),
            "average_contract_latency_ms": avg_latency(self.contract_latencies),
            "average_compatibility_latency_ms": avg_latency(self.compatibility_latencies),
            "cache_hit_rate": cache_hit_rate,
            "error_rate": error_rate
        }


# Global metrics collector instance
_metrics_collector = MetricsCollector()


class SchemaService:
    """
    Schema management service.

    Per PRD: Schema registration, versioning, deprecation, tenant isolation.
    """

    def __init__(
        self,
        kms: Optional[MockM33KMS] = None,
        evidence_ledger: Optional[MockM27EvidenceLedger] = None,
        cache_manager: Optional[CacheManager] = None
    ):
        """
        Initialize schema service.

        Args:
            kms: KMS for schema signing
            evidence_ledger: Evidence ledger for receipts
            cache_manager: Cache manager
        """
        self.kms = kms or MockM33KMS()
        self.evidence_ledger = evidence_ledger or MockM27EvidenceLedger()
        self.cache_manager = cache_manager or CacheManager()
        self.json_validator = JSONSchemaValidator()
        self.avro_validator = AvroValidator()
        self.protobuf_validator = ProtobufValidator()

    def register_schema(
        self,
        request: Dict[str, Any],
        tenant_id: str,
        created_by: str
    ) -> SchemaMetadata:
        """
        Register a new schema.

        Args:
            request: RegisterSchemaRequest data
            tenant_id: Tenant identifier
            created_by: Creator identifier

        Returns:
            SchemaMetadata

        Raises:
            ValueError: If registration fails
        """
        schema_type = request["schema_type"]
        schema_definition = request["schema_definition"]
        name = request["name"]
        namespace = request["namespace"]
        compatibility = request["compatibility"]
        metadata = request.get("metadata", {})

        # Validate schema definition
        is_valid, errors = self._validate_schema_definition(schema_type, schema_definition)
        if not is_valid:
            raise ValueError(f"Invalid schema definition: {', '.join(errors)}")

        # Check tenant quota
        self._check_tenant_quota(tenant_id)

        # Generate schema ID and version
        schema_id = str(uuid.uuid4())
        version = "1.0.0"  # Initial version

        # Check for existing schema with same name/version
        db = get_session()
        try:
            existing = db.query(Schema).filter(
                and_(
                    Schema.tenant_id == uuid.UUID(tenant_id),
                    Schema.name == name,
                    Schema.version == version
                )
            ).first()

            if existing:
                raise ValueError(f"Schema with name '{name}' and version '{version}' already exists")

            # Create schema record
            schema = Schema(
                schema_id=uuid.UUID(schema_id),
                name=name,
                namespace=namespace,
                schema_type=schema_type,
                schema_definition=schema_definition,
                version=version,
                compatibility=compatibility,
                status="draft",
                created_by=uuid.UUID(created_by),
                tenant_id=uuid.UUID(tenant_id),
                metadata=metadata
            )

            db.add(schema)
            db.commit()
            db.refresh(schema)

            # Sign schema
            schema_data = schema.to_dict()
            signature = self.kms.sign_schema(schema_data, tenant_id)

            # Cache schema
            self.cache_manager.set_schema(schema_id, schema_data)

            # Create receipt
            receipt = self._create_receipt(
                "schema_registered",
                {
                    "schema_id": schema_id,
                    "tenant_id": tenant_id
                },
                "M34"
            )
            self.evidence_ledger.store_receipt(receipt["receipt_id"], receipt)

            return SchemaMetadata(**schema_data)

        finally:
            db.close()

    def get_schema(self, schema_id: str, tenant_id: str, version: Optional[str] = None) -> Optional[SchemaMetadata]:
        """
        Get schema by ID.

        Args:
            schema_id: Schema identifier
            tenant_id: Tenant identifier
            version: Optional version

        Returns:
            SchemaMetadata or None
        """
        # Check cache first
        cached = self.cache_manager.get_schema(schema_id)
        if cached:
            # Verify tenant access
            if cached.get("tenant_id") == tenant_id:
                return SchemaMetadata(**cached)

        db = get_session()
        try:
            query = db.query(Schema).filter(
                and_(
                    Schema.schema_id == uuid.UUID(schema_id),
                    Schema.tenant_id == uuid.UUID(tenant_id)
                )
            )

            if version:
                query = query.filter(Schema.version == version)

            schema = query.first()

            if schema:
                schema_data = schema.to_dict()
                self.cache_manager.set_schema(schema_id, schema_data)
                return SchemaMetadata(**schema_data)

            return None

        finally:
            db.close()

    def list_schemas(
        self,
        tenant_id: str,
        namespace: Optional[str] = None,
        schema_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[SchemaMetadata], int]:
        """
        List schemas with filters.

        Args:
            tenant_id: Tenant identifier
            namespace: Optional namespace filter
            schema_type: Optional schema type filter
            status: Optional status filter
            limit: Result limit
            offset: Result offset

        Returns:
            Tuple of (list of schemas, total count)
        """
        db = get_session()
        try:
            query = db.query(Schema).filter(Schema.tenant_id == uuid.UUID(tenant_id))

            if namespace:
                query = query.filter(Schema.namespace == namespace)
            if schema_type:
                query = query.filter(Schema.schema_type == schema_type)
            if status:
                query = query.filter(Schema.status == status)

            total = query.count()
            schemas = query.limit(limit).offset(offset).all()

            return [SchemaMetadata(**s.to_dict()) for s in schemas], total

        finally:
            db.close()

    def update_schema(
        self,
        schema_id: str,
        request: Dict[str, Any],
        tenant_id: str,
        created_by: str
    ) -> SchemaMetadata:
        """
        Update schema (creates new version).

        Args:
            schema_id: Schema identifier
            request: UpdateSchemaRequest data
            tenant_id: Tenant identifier
            created_by: Creator identifier

        Returns:
            SchemaMetadata
        """
        db = get_session()
        try:
            # Get existing schema
            existing = db.query(Schema).filter(
                and_(
                    Schema.schema_id == uuid.UUID(schema_id),
                    Schema.tenant_id == uuid.UUID(tenant_id)
                )
            ).first()

            if not existing:
                raise ValueError("Schema not found")

            # Validate new schema definition
            is_valid, errors = self._validate_schema_definition(
                existing.schema_type,
                request["schema_definition"]
            )
            if not is_valid:
                raise ValueError(f"Invalid schema definition: {', '.join(errors)}")

            # Increment version (simplified - should use semantic versioning)
            version_parts = existing.version.split(".")
            if len(version_parts) == 3:
                major, minor, patch = map(int, version_parts)
                patch += 1
                new_version = f"{major}.{minor}.{patch}"
            else:
                new_version = f"{existing.version}.1"

            # Create new version
            new_schema = Schema(
                schema_id=uuid.UUID(str(uuid.uuid4())),  # New schema ID for new version
                name=existing.name,
                namespace=existing.namespace,
                schema_type=existing.schema_type,
                schema_definition=request["schema_definition"],
                version=new_version,
                compatibility=request["compatibility"],
                status="draft",
                created_by=uuid.UUID(created_by),
                tenant_id=existing.tenant_id,
                metadata=request.get("metadata", existing.metadata)
            )

            db.add(new_schema)
            db.commit()
            db.refresh(new_schema)

            schema_data = new_schema.to_dict()
            self.cache_manager.set_schema(str(new_schema.schema_id), schema_data)

            return SchemaMetadata(**schema_data)

        finally:
            db.close()

    def deprecate_schema(self, schema_id: str, tenant_id: str) -> None:
        """
        Deprecate schema.

        Args:
            schema_id: Schema identifier
            tenant_id: Tenant identifier
        """
        db = get_session()
        try:
            schema = db.query(Schema).filter(
                and_(
                    Schema.schema_id == uuid.UUID(schema_id),
                    Schema.tenant_id == uuid.UUID(tenant_id)
                )
            ).first()

            if schema:
                schema.status = "deprecated"
                db.commit()
                # Clear cache
                self.cache_manager.schema_cache.clear()
        finally:
            db.close()

    def _validate_schema_definition(self, schema_type: str, schema_definition: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate schema definition."""
        if schema_type == "json_schema":
            return self.json_validator.validate_schema(schema_definition)
        elif schema_type == "avro":
            return self.avro_validator.validate_schema(schema_definition)
        elif schema_type == "protobuf":
            return self.protobuf_validator.validate_schema(schema_definition)
        else:
            return False, [f"Unsupported schema type: {schema_type}"]

    def _check_tenant_quota(self, tenant_id: str) -> None:
        """Check tenant quota."""
        db = get_session()
        try:
            count = db.query(Schema).filter(Schema.tenant_id == uuid.UUID(tenant_id)).count()
            if count >= MAX_SCHEMAS_PER_TENANT:
                raise ValueError(f"Tenant quota exceeded: {MAX_SCHEMAS_PER_TENANT} schemas")
        finally:
            db.close()

    def _create_receipt(self, operation: str, context: Dict[str, Any], requesting_module: str) -> Dict[str, Any]:
        """Create validation receipt."""
        receipt_id = str(uuid.uuid4())
        receipt_data = {
            "receipt_id": receipt_id,
            "ts": datetime.utcnow().isoformat(),
            "module": "REGISTRY",
            "operation": operation,
            "registry_context": context,
            "requesting_module": requesting_module
        }
        signature = self.evidence_ledger.sign_receipt(receipt_data)
        receipt_data["signature"] = signature
        return receipt_data


class ValidationService:
    """
    Validation service.

    Per PRD: Data validation against schemas, contract enforcement.
    """

    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        evidence_ledger: Optional[MockM27EvidenceLedger] = None
    ):
        """
        Initialize validation service.

        Args:
            cache_manager: Cache manager
            evidence_ledger: Evidence ledger
        """
        self.cache_manager = cache_manager or CacheManager()
        self.evidence_ledger = evidence_ledger or MockM27EvidenceLedger()
        self.json_validator = JSONSchemaValidator()
        self.avro_validator = AvroValidator()
        self.protobuf_validator = ProtobufValidator()
        self.custom_validator = CustomValidator()

    def validate_data(
        self,
        schema_id: str,
        data: Dict[str, Any],
        tenant_id: str,
        version: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate data against schema.

        Args:
            schema_id: Schema identifier
            data: Data to validate
            tenant_id: Tenant identifier
            version: Optional schema version

        Returns:
            ValidationResult
        """
        # Get schema
        schema_service = SchemaService()
        schema = schema_service.get_schema(schema_id, tenant_id, version)

        if not schema:
            return ValidationResult(
                valid=False,
                errors=[ValidationError(
                    field=".",
                    message="Schema not found",
                    code="SCHEMA_NOT_FOUND"
                )]
            )

        # Check validation cache
        data_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        cached = self.cache_manager.get_validation(schema_id, data_hash)
        if cached:
            return ValidationResult(**cached)

        # Perform validation
        schema_type = schema.schema_type
        schema_definition = schema.schema_definition

        if schema_type == "json_schema":
            is_valid, errors = self.json_validator.validate(schema_definition, data, schema_id)
        elif schema_type == "avro":
            is_valid, errors = self.avro_validator.validate(schema_definition, data, schema_id)
        elif schema_type == "protobuf":
            is_valid, errors = self.protobuf_validator.validate(schema_definition, data, schema_id)
        else:
            return ValidationResult(
                valid=False,
                errors=[ValidationError(
                    field=".",
                    message=f"Unsupported schema type: {schema_type}",
                    code="INVALID_SCHEMA_TYPE"
                )]
            )

        # Convert errors to ValidationError models
        validation_errors = [
            ValidationError(
                field=e.get("field", "."),
                message=e.get("message", "Validation error"),
                code=e.get("code", "VALIDATION_ERROR")
            )
            for e in errors
        ]

        result = ValidationResult(valid=is_valid, errors=validation_errors)

        # Cache result
        self.cache_manager.set_validation(schema_id, data_hash, result.model_dump())

        # Create receipt
        receipt = self._create_receipt(
            "schema_validated",
            {
                "schema_id": schema_id,
                "validation_result": "pass" if is_valid else "fail",
                "tenant_id": tenant_id
            },
            "M34"
        )
        self.evidence_ledger.store_receipt(receipt["receipt_id"], receipt)

        return result

    def _create_receipt(self, operation: str, context: Dict[str, Any], requesting_module: str) -> Dict[str, Any]:
        """Create validation receipt."""
        receipt_id = str(uuid.uuid4())
        receipt_data = {
            "receipt_id": receipt_id,
            "ts": datetime.utcnow().isoformat(),
            "module": "REGISTRY",
            "operation": operation,
            "registry_context": context,
            "requesting_module": requesting_module
        }
        signature = self.evidence_ledger.sign_receipt(receipt_data)
        receipt_data["signature"] = signature
        return receipt_data


class ContractService:
    """
    Contract management service.

    Per PRD: Contract creation, enforcement, violation handling.
    """

    def __init__(self, evidence_ledger: Optional[MockM27EvidenceLedger] = None):
        """
        Initialize contract service.

        Args:
            evidence_ledger: Evidence ledger
        """
        self.evidence_ledger = evidence_ledger or MockM27EvidenceLedger()
        self.validation_service = ValidationService()

    def create_contract(
        self,
        request: Dict[str, Any],
        tenant_id: str,
        created_by: str
    ) -> ContractDefinition:
        """
        Create a new contract.

        Args:
            request: CreateContractRequest data
            tenant_id: Tenant identifier
            created_by: Creator identifier

        Returns:
            ContractDefinition
        """
        # Verify schema exists
        schema_service = SchemaService()
        schema = schema_service.get_schema(request["schema_id"], tenant_id)
        if not schema:
            raise ValueError("Schema not found")

        db = get_session()
        try:
            contract = Contract(
                contract_id=uuid.uuid4(),
                name=request["name"],
                type=request["type"],
                schema_id=uuid.UUID(request["schema_id"]),
                validation_rules=request["validation_rules"],
                enforcement_level=request["enforcement_level"],
                violation_actions=request["violation_actions"],
                version="1.0.0",
                tenant_id=uuid.UUID(tenant_id),
                created_by=uuid.UUID(created_by)
            )

            db.add(contract)
            db.commit()
            db.refresh(contract)

            return ContractDefinition(**contract.to_dict())

        finally:
            db.close()

    def enforce_contract(
        self,
        contract_id: str,
        data: Dict[str, Any],
        tenant_id: str
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Enforce contract on data.

        Args:
            contract_id: Contract identifier
            data: Data to validate
            tenant_id: Tenant identifier

        Returns:
            Tuple of (is_valid, violations)
        """
        db = get_session()
        try:
            contract = db.query(Contract).filter(
                and_(
                    Contract.contract_id == uuid.UUID(contract_id),
                    Contract.tenant_id == uuid.UUID(tenant_id)
                )
            ).first()

            if not contract:
                raise ValueError("Contract not found")

            # Validate against schema first
            schema = SchemaService().get_schema(str(contract.schema_id), tenant_id)
            if not schema:
                raise ValueError("Schema not found")

            validation_result = self.validation_service.validate_data(
                str(contract.schema_id),
                data,
                tenant_id
            )

            if not validation_result.valid:
                violations = [
                    {
                        "field": e.field,
                        "message": e.message,
                        "severity": contract.enforcement_level
                    }
                    for e in validation_result.errors
                ]
                return False, violations

            # Apply contract validation rules
            violations = []
            for rule in contract.validation_rules:
                field = rule.get("field")
                rule_type = rule.get("rule_type")

                if field in data:
                    value = data[field]

                    # Apply rule validation
                    if rule_type == "required" and not value:
                        violations.append({
                            "field": field,
                            "message": rule.get("error_message", f"Field '{field}' is required"),
                            "severity": contract.enforcement_level
                        })
                    elif rule_type == "range":
                        min_val = rule.get("min")
                        max_val = rule.get("max")
                        if min_val is not None and value < min_val:
                            violations.append({
                                "field": field,
                                "message": rule.get("error_message", f"Field '{field}' below minimum"),
                                "severity": contract.enforcement_level
                            })
                        if max_val is not None and value > max_val:
                            violations.append({
                                "field": field,
                                "message": rule.get("error_message", f"Field '{field}' above maximum"),
                                "severity": contract.enforcement_level
                            })

            is_valid = len(violations) == 0 or contract.enforcement_level != "strict"
            return is_valid, violations

        finally:
            db.close()

    def list_contracts(
        self,
        tenant_id: str,
        schema_id: Optional[str] = None,
        contract_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[ContractDefinition], int]:
        """
        List contracts with filters.

        Args:
            tenant_id: Tenant identifier
            schema_id: Optional schema identifier filter
            contract_type: Optional contract type filter
            limit: Result limit
            offset: Result offset

        Returns:
            Tuple of (list of contracts, total count)
        """
        db = get_session()
        try:
            query = db.query(Contract).filter(Contract.tenant_id == uuid.UUID(tenant_id))

            if schema_id:
                query = query.filter(Contract.schema_id == uuid.UUID(schema_id))
            if contract_type:
                query = query.filter(Contract.type == contract_type)

            total = query.count()
            contracts = query.limit(limit).offset(offset).all()

            return [ContractDefinition(**c.to_dict()) for c in contracts], total

        finally:
            db.close()

    def get_contract(self, contract_id: str, tenant_id: str) -> Optional[ContractDefinition]:
        """
        Get contract by ID.

        Args:
            contract_id: Contract identifier
            tenant_id: Tenant identifier

        Returns:
            ContractDefinition or None
        """
        db = get_session()
        try:
            contract = db.query(Contract).filter(
                and_(
                    Contract.contract_id == uuid.UUID(contract_id),
                    Contract.tenant_id == uuid.UUID(tenant_id)
                )
            ).first()

            if contract:
                return ContractDefinition(**contract.to_dict())
            return None

        finally:
            db.close()


class CompatibilityService:
    """
    Compatibility checking service.

    Per PRD: Compatibility checking between schema versions.
    """

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Initialize compatibility service.

        Args:
            cache_manager: Cache manager
        """
        self.cache_manager = cache_manager or CacheManager()
        self.checker = CompatibilityChecker()

    def check_compatibility(
        self,
        source_schema: Dict[str, Any],
        target_schema: Dict[str, Any],
        compatibility_mode: str = "backward"
    ) -> CompatibilityResult:
        """
        Check compatibility between schemas.

        Args:
            source_schema: Source schema definition
            target_schema: Target schema definition
            compatibility_mode: Compatibility mode

        Returns:
            CompatibilityResult
        """
        # Check cache
        source_id = str(hash(str(source_schema)))
        target_id = str(hash(str(target_schema)))
        cached = self.cache_manager.get_compatibility(source_id, target_id)
        if cached:
            return CompatibilityResult(**cached)

        # Perform compatibility check
        mode = CompatibilityMode(compatibility_mode)
        is_compatible, breaking_changes, warnings = self.checker.check_compatibility(
            source_schema,
            target_schema,
            mode
        )

        result = CompatibilityResult(
            compatible=is_compatible,
            breaking_changes=breaking_changes,
            warnings=warnings
        )

        # Cache result
        self.cache_manager.set_compatibility(source_id, target_id, result.model_dump())

        return result


class TransformationService:
    """
    Data transformation service.

    Per PRD: Schema-to-schema data transformation.
    """

    def __init__(self):
        """Initialize transformation service."""
        self.transformer = DataTransformer()
        self.schema_service = SchemaService()

    def transform_data(
        self,
        source_schema_id: str,
        target_schema_id: str,
        data: Dict[str, Any],
        tenant_id: str,
        source_version: Optional[str] = None,
        target_version: Optional[str] = None
    ) -> TransformationResult:
        """
        Transform data between schema versions.

        Args:
            source_schema_id: Source schema identifier
            target_schema_id: Target schema identifier
            data: Data to transform
            tenant_id: Tenant identifier
            source_version: Optional source version
            target_version: Optional target version

        Returns:
            TransformationResult
        """
        # Get schemas
        source_schema = self.schema_service.get_schema(source_schema_id, tenant_id, source_version)
        target_schema = self.schema_service.get_schema(target_schema_id, tenant_id, target_version)

        if not source_schema or not target_schema:
            raise ValueError("Schema not found")

        # Perform transformation
        transformed_data, applied, warnings = self.transformer.transform(
            source_schema.schema_definition,
            target_schema.schema_definition,
            data,
            source_schema_id,
            target_schema_id
        )

        return TransformationResult(
            transformed_data=transformed_data,
            transformation_applied=applied,
            warnings=warnings
        )
