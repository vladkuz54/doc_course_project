from fastapi import APIRouter, Depends
from pydantic import ConfigDict

from ...bll.services.routes_service import RouteData, RoutesService, RouteStatusData
from ..dependencies import get_routes_service
from .auth import ensure_visible, get_current_driver_id, require_admin

router = APIRouter(prefix="/routes", tags=["routes"])


class RouteResponse(RouteData):
    id: int
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[RouteResponse])
async def get_all(
    driver_id: int | None = Depends(get_current_driver_id),
    service: RoutesService = Depends(get_routes_service),
):
    if driver_id is None:
        return await service.get_all()
    return await service.get_by_driver(driver_id)


@router.get("/{id}", response_model=RouteResponse)
async def get_by_id(
    id: int,
    driver_id: int | None = Depends(get_current_driver_id),
    service: RoutesService = Depends(get_routes_service),
):
    obj = await service.get_by_id(id)
    if driver_id is not None:
        ensure_visible(obj, await service.get_by_driver(driver_id))
    return obj


@router.post(
    "/",
    response_model=RouteResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def create(data: RouteData, service: RoutesService = Depends(get_routes_service)):
    return await service.create(data)


@router.put(
    "/{id}", response_model=RouteResponse, dependencies=[Depends(require_admin)]
)
async def update(
    id: int, data: RouteData, service: RoutesService = Depends(get_routes_service)
):
    return await service.update(id, data)


@router.patch(
    "/{id}/status",
    response_model=RouteResponse,
    dependencies=[Depends(require_admin)],
)
async def change_status(
    id: int,
    data: RouteStatusData,
    service: RoutesService = Depends(get_routes_service),
):
    return await service.change_status(id, data.status)


@router.delete(
    "/{id}", response_model=RouteResponse, dependencies=[Depends(require_admin)]
)
async def delete(id: int, service: RoutesService = Depends(get_routes_service)):
    return await service.delete(id)
