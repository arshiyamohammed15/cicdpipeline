"""
CCCS integration for Cloud Services (FastAPI applications).

This module provides middleware and utilities for integrating CCCS runtime
into FastAPI-based Cloud Services.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware

from ..runtime import CCCSRuntime, CCCSConfig
from ..types import ActorContext
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class CCCSCloudServicesIntegration:
    """
    Integration helper for Cloud Services to use CCCS runtime.
    
    Provides FastAPI middleware and utilities for:
    - Identity resolution
    - Policy evaluation
    - Budget checks
    - Receipt generation
    """

    def __init__(self, runtime: CCCSRuntime):
        self._runtime = runtime

    def get_actor_from_request(self, request: Request) -> ActorContext:
        """
        Extract actor context from FastAPI request.
        
        Looks for actor context in:
        - Headers: X-Tenant-ID, X-Device-ID, X-Session-ID, X-User-ID, X-Actor-Type
        - Request state (if set by previous middleware)
        """
        tenant_id = request.headers.get("X-Tenant-ID") or request.state.get("tenant_id", "")
        device_id = request.headers.get("X-Device-ID") or request.state.get("device_id", "")
        session_id = request.headers.get("X-Session-ID") or request.state.get("session_id", "")
        user_id = request.headers.get("X-User-ID") or request.state.get("user_id", "")
        actor_type = request.headers.get("X-Actor-Type") or request.state.get("actor_type", "machine")

        return ActorContext(
            tenant_id=tenant_id,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            actor_type=actor_type,
            runtime_clock=datetime.now(timezone.utc),
            extras={},
        )

    def execute_flow_for_request(
        self,
        request: Request,
        module_id: str,
        inputs: Dict[str, Any],
        action_id: str,
        cost: float,
        config_key: str,
        payload: Dict[str, Any],
        redaction_hint: str = "",
    ) -> Dict[str, Any]:
        """
        Execute CCCS flow for a FastAPI request.
        
        Automatically extracts actor context from request.
        """
        actor_context = self.get_actor_from_request(request)
        
        try:
            return self._runtime.execute_flow(
                module_id=module_id,
                inputs=inputs,
                action_id=action_id,
                cost=cost,
                config_key=config_key,
                payload=payload,
                redaction_hint=redaction_hint,
                actor_context=actor_context,
            )
        except Exception as e:
            error_dict = self._runtime.normalize_error(e)
            logger.error(f"CCCS flow execution failed: {error_dict}")
            raise HTTPException(status_code=500, detail=error_dict)


class CCCSMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware to inject CCCS runtime into request state.
    """

    def __init__(self, app: FastAPI, cccs_integration: CCCSCloudServicesIntegration):
        super().__init__(app)
        self._cccs = cccs_integration

    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """Add CCCS integration to request state."""
        request.state.cccs = self._cccs
        response = await call_next(request)
        return response


def setup_cccs_for_fastapi(
    app: FastAPI,
    config: CCCSConfig,
    wal_path: Optional[Path] = None,
) -> CCCSCloudServicesIntegration:
    """
    Setup CCCS integration for a FastAPI application.
    
    Creates runtime, integration helper, and adds middleware.
    
    Usage:
        from fastapi import FastAPI
        from shared_libs.cccs.integration import setup_cccs_for_fastapi
        from shared_libs.cccs.runtime import CCCSConfig
        
        app = FastAPI()
        config = CCCSConfig(...)
        cccs = setup_cccs_for_fastapi(app, config)
        
        @app.post("/api/action")
        async def perform_action(request: Request):
            result = request.state.cccs.execute_flow_for_request(
                request,
                module_id="m01",
                inputs={...},
                action_id="action-1",
                cost=1.0,
                config_key="config-key",
                payload={...},
            )
            return result
    """
    runtime = CCCSRuntime(config, wal_path=wal_path)
    integration = CCCSCloudServicesIntegration(runtime)
    
    # Add middleware
    app.add_middleware(CCCSMiddleware, cccs_integration=integration)
    
    return integration

