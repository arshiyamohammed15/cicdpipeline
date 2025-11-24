"""Component registry HTTP endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from ..models import ComponentDefinition, ComponentRegistrationResponse
from ..security import ensure_scope, require_scope
from ..service_container import get_db_session, get_registry_service

router = APIRouter()


def _registry_service(session=Depends(get_db_session)):
    return get_registry_service(session)


@router.post(
    "/components",
    response_model=ComponentRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register or update a monitored component",
)
def register_component(
    payload: ComponentDefinition,
    service=Depends(_registry_service),
    claims=Depends(require_scope),
):
    """Implements FR-1 registry POST endpoint."""
    ensure_scope(claims, "health_reliability_monitoring.write")
    return service.register_component(payload)


@router.get(
    "/components/{component_id}",
    response_model=ComponentDefinition,
    summary="Retrieve component definition",
)
def get_component(
    component_id: str,
    service=Depends(_registry_service),
    claims=Depends(require_scope),
):
    """Fetch component metadata by ID."""
    component = service.get_component(component_id)
    if not component:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Component not found")
    return component


@router.get(
    "/components",
    response_model=list[ComponentDefinition],
    summary="List all monitored components",
)
def list_components(service=Depends(_registry_service), claims=Depends(require_scope)):
    """List all registered components."""
    return service.list_components()

