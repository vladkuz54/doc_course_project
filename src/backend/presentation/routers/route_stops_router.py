from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import ConfigDict

from ...bll.interfaces.route_stops_interface import IRouteStopsService
from ...bll.services.route_stops_service import RouteStopData
from ..dependencies import get_route_stops_service
from .auth import ensure_visible, get_current_driver_id

router = APIRouter(prefix="/route-stops", tags=["route-stops"])


class RouteStopResponse(RouteStopData):
    id: int
    arrived_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[RouteStopResponse])
async def get_all(
    driver_id: int | None = Depends(get_current_driver_id),
    service: IRouteStopsService = Depends(get_route_stops_service),
):
    if driver_id is None:
        return await service.get_all()
    return await service.get_by_driver(driver_id)


@router.get("/{id}", response_model=RouteStopResponse)
async def get_by_id(
    id: int,
    driver_id: int | None = Depends(get_current_driver_id),
    service: IRouteStopsService = Depends(get_route_stops_service),
):
    obj = await service.get_by_id(id)
    if driver_id is not None:
        ensure_visible(obj, await service.get_by_driver(driver_id))
    return obj
