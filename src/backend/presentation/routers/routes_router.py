from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ConfigDict

from ...bll.services.routes_service import (
    RouteCompleteData,
    RouteCreateData,
    RouteData,
    RouteDriverData,
    RoutesService,
    RouteStartData,
    RouteStatusData,
    RouteStopsData,
    RouteVehicleData,
)
from ...dal.db_models import RouteStops
from ..dependencies import get_routes_service
from .auth import ensure_visible, get_current_driver_id, require_admin

router = APIRouter(prefix="/routes", tags=["routes"])


class RouteResponse(RouteData):
    id: int
    planned_return_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    status: Literal["PLANNED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[RouteResponse])
async def get_all(
    driver_id: int | None = Depends(get_current_driver_id),
    service: RoutesService = Depends(get_routes_service),
):
    if driver_id is None:
        return await service.get_all()
    return await service.list_by_driver(driver_id)


@router.get("/{id}", response_model=RouteResponse)
async def get_by_id(
    id: int,
    driver_id: int | None = Depends(get_current_driver_id),
    service: RoutesService = Depends(get_routes_service),
):
    obj = await service.get_by_id(id)
    if driver_id is not None:
        ensure_visible(obj, await service.list_by_driver(driver_id))
    return obj


@router.post(
    "/",
    response_model=RouteResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def create(
    data: RouteCreateData, service: RoutesService = Depends(get_routes_service)
):
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


async def _ensure_can_act(id, driver_id, service):
    route = await service.get_by_id(id)
    if driver_id is not None:
        ensure_visible(route, await service.list_by_driver(driver_id))


@router.put(
    "/{id}/stops", response_model=RouteResponse, dependencies=[Depends(require_admin)]
)
async def edit_stops(
    id: int,
    data: RouteStopsData,
    service: RoutesService = Depends(get_routes_service),
):
    return await service.edit_stops(
        id, [RouteStops(address=address) for address in data.stops]
    )


@router.put(
    "/{id}/driver", response_model=RouteResponse, dependencies=[Depends(require_admin)]
)
async def assign_driver(
    id: int,
    data: RouteDriverData,
    service: RoutesService = Depends(get_routes_service),
):
    return await service.assign_driver(id, data.driver_id)


@router.put(
    "/{id}/vehicle", response_model=RouteResponse, dependencies=[Depends(require_admin)]
)
async def assign_vehicle(
    id: int,
    data: RouteVehicleData,
    service: RoutesService = Depends(get_routes_service),
):
    return await service.assign_vehicle(id, data.vehicle_id)


@router.post(
    "/{id}/cancel", response_model=RouteResponse, dependencies=[Depends(require_admin)]
)
async def cancel(id: int, service: RoutesService = Depends(get_routes_service)):
    return await service.cancel(id)


@router.post("/{id}/start", response_model=RouteResponse)
async def start(
    id: int,
    data: RouteStartData | None = None,
    driver_id: int | None = Depends(get_current_driver_id),
    service: RoutesService = Depends(get_routes_service),
):
    await _ensure_can_act(id, driver_id, service)
    started_at = data.started_at if data else None
    if driver_id is not None and started_at is not None:
        raise HTTPException(
            status_code=403, detail="Вказати час початку може лише адміністратор."
        )
    return await service.start(id, started_at)


@router.post("/{id}/complete", response_model=RouteResponse)
async def complete(
    id: int,
    data: RouteCompleteData | None = None,
    driver_id: int | None = Depends(get_current_driver_id),
    service: RoutesService = Depends(get_routes_service),
):
    await _ensure_can_act(id, driver_id, service)
    returned_at = data.returned_at if data else None
    if driver_id is not None and returned_at is not None:
        raise HTTPException(
            status_code=403, detail="Вказати час повернення може лише адміністратор."
        )
    return await service.complete(id, returned_at)


@router.post("/{id}/stops/{stop_id}/arrive", response_model=RouteResponse)
async def arrive_at_stop(
    id: int,
    stop_id: int,
    driver_id: int | None = Depends(get_current_driver_id),
    service: RoutesService = Depends(get_routes_service),
):
    if driver_id is None:
        raise HTTPException(
            status_code=403,
            detail="Відмічати прибуття на зупинки може лише водій цього маршруту.",
        )
    await _ensure_can_act(id, driver_id, service)
    return await service.arrive_at_stop(id, stop_id)
