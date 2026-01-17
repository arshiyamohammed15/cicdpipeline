"""
EPC-12 (Contracts & Schema Registry) Integration for ZeroUI Observability Layer.

Registers all observability schemas (envelope + 12 payload schemas) with EPC-12.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# EPC-12 API endpoint (configurable via env var)
EPC12_BASE_URL = os.getenv("EPC12_SCHEMA_REGISTRY_URL", "http://localhost:8000/registry/v1")
EPC12_REGISTER_ENDPOINT = f"{EPC12_BASE_URL}/schemas"

# Schema namespace for observability schemas
OBSERVABILITY_NAMESPACE = "zeroui.observability"


class EPC12SchemaRegistryClient:
    """
    Client for registering observability schemas with EPC-12.
    
    Integrates with EPC-12 (Contracts & Schema Registry) to register:
    - Event envelope schema (zero_ui.obsv.event.v1)
    - All 12 event payload schemas
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        enabled: bool = True,
    ):
        """
        Initialize EPC-12 schema registry client.
        
        Args:
            base_url: EPC-12 base URL (defaults to env var or localhost)
            enabled: Whether registration is enabled
        """
        self._base_url = base_url or EPC12_BASE_URL
        self._enabled = enabled and self._check_epc12_available()
        self._registered_schemas: List[str] = []

    def _check_epc12_available(self) -> bool:
        """Check if EPC-12 service is available."""
        try:
            import httpx
            response = httpx.get(f"{self._base_url}/health", timeout=2.0)
            return response.status_code == 200
        except Exception:
            logger.debug("EPC-12 service not available, schema registration disabled")
            return False

    def register_envelope_schema(self) -> bool:
        """
        Register event envelope schema with EPC-12.
        
        Returns:
            True if registration succeeded, False otherwise
        """
        if not self._enabled:
            logger.debug("EPC-12 registration disabled")
            return False

        schema_path = Path(__file__).parent.parent / "contracts" / "envelope_schema.json"
        if not schema_path.exists():
            logger.error(f"Envelope schema not found: {schema_path}")
            return False

        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_def = json.load(f)

            request_data = {
                "schema_type": "json_schema",
                "schema_definition": schema_def,
                "compatibility": "backward",
                "name": "zero_ui.obsv.event.v1",
                "namespace": OBSERVABILITY_NAMESPACE,
                "metadata": {
                    "description": "ZeroUI Observability Layer event envelope schema",
                    "version": "v1",
                    "module": "zeroui_observability",
                },
            }

            return self._register_schema(request_data, "envelope")
        except Exception as e:
            logger.error(f"Failed to register envelope schema: {e}")
            return False

    def register_payload_schemas(self) -> Dict[str, bool]:
        """
        Register all 12 event payload schemas with EPC-12.
        
        Returns:
            Dictionary mapping event_type to registration success status
        """
        if not self._enabled:
            logger.debug("EPC-12 registration disabled")
            return {}

        results: Dict[str, bool] = {}
        payloads_dir = Path(__file__).parent.parent / "contracts" / "payloads"

        # Event type to schema file mapping
        event_type_to_file = {
            "error.captured.v1": "error_captured_v1.json",
            "prompt.validation.result.v1": "prompt_validation_result_v1.json",
            "memory.access.v1": "memory_access_v1.json",
            "memory.validation.v1": "memory_validation_v1.json",
            "evaluation.result.v1": "evaluation_result_v1.json",
            "user.flag.v1": "user_flag_v1.json",
            "bias.scan.result.v1": "bias_scan_result_v1.json",
            "retrieval.eval.v1": "retrieval_eval_v1.json",
            "failure.replay.bundle.v1": "failure_replay_bundle_v1.json",
            "perf.sample.v1": "perf_sample_v1.json",
            "privacy.audit.v1": "privacy_audit_v1.json",
            "alert.noise_control.v1": "alert_noise_control_v1.json",
        }

        for event_type, schema_file in event_type_to_file.items():
            schema_path = payloads_dir / schema_file
            if not schema_path.exists():
                logger.warning(f"Schema file not found: {schema_path}")
                results[event_type] = False
                continue

            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema_def = json.load(f)

                request_data = {
                    "schema_type": "json_schema",
                    "schema_definition": schema_def,
                    "compatibility": "backward",
                    "name": event_type,
                    "namespace": OBSERVABILITY_NAMESPACE,
                    "metadata": {
                        "description": f"ZeroUI Observability Layer payload schema for {event_type}",
                        "version": "v1",
                        "module": "zeroui_observability",
                        "event_type": event_type,
                    },
                }

                success = self._register_schema(request_data, event_type)
                results[event_type] = success
            except Exception as e:
                logger.error(f"Failed to register schema {event_type}: {e}")
                results[event_type] = False

        return results

    def register_all_schemas(self) -> Dict[str, Any]:
        """
        Register all observability schemas (envelope + payloads) with EPC-12.
        
        Returns:
            Registration results summary
        """
        logger.info("Registering observability schemas with EPC-12...")

        results = {
            "envelope": False,
            "payloads": {},
            "total": 0,
            "succeeded": 0,
            "failed": 0,
        }

        # Register envelope schema
        results["envelope"] = self.register_envelope_schema()
        if results["envelope"]:
            results["succeeded"] += 1
        else:
            results["failed"] += 1

        # Register payload schemas
        payload_results = self.register_payload_schemas()
        results["payloads"] = payload_results
        results["total"] = len(payload_results)

        for success in payload_results.values():
            if success:
                results["succeeded"] += 1
            else:
                results["failed"] += 1

        logger.info(
            f"Schema registration complete: {results['succeeded']}/{results['total'] + 1} succeeded"
        )

        return results

    def _register_schema(self, request_data: Dict[str, Any], schema_name: str) -> bool:
        """
        Register a single schema with EPC-12.
        
        Args:
            request_data: Schema registration request data
            schema_name: Schema name for logging
            
        Returns:
            True if registration succeeded, False otherwise
        """
        try:
            import httpx

            response = httpx.post(
                EPC12_REGISTER_ENDPOINT,
                json=request_data,
                timeout=10.0,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code in (200, 201):
                schema_id = response.json().get("schema_id", "unknown")
                self._registered_schemas.append(schema_id)
                logger.info(f"Registered schema {schema_name} with EPC-12: {schema_id}")
                return True
            else:
                logger.error(
                    f"Failed to register schema {schema_name}: HTTP {response.status_code} - {response.text}"
                )
                return False
        except ImportError:
            logger.warning("httpx not available, cannot register schemas with EPC-12")
            return False
        except Exception as e:
            logger.error(f"Failed to register schema {schema_name}: {e}")
            return False


def register_observability_schemas(
    base_url: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Register all observability schemas with EPC-12.
    
    Args:
        base_url: Optional EPC-12 base URL
        enabled: Optional enable flag (defaults to checking service availability)
        
    Returns:
        Registration results summary
    """
    if enabled is None:
        enabled = os.getenv("EPC12_SCHEMA_REGISTRY_ENABLED", "true").lower() == "true"

    client = EPC12SchemaRegistryClient(base_url=base_url, enabled=enabled)
    return client.register_all_schemas()
