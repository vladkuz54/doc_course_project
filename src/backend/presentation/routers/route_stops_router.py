from fastapi import APIRouter, Depends
from pydantic import ConfigDict

from ...bll.services.route_stops_service import RouteStopData, RouteStopsService
from ..dependencies import get_route_stops_service

router = APIRouter(prefix="/route-stops", tags=["route-stops"])


class RouteStopResponse(RouteStopData):
    id: int
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[RouteStopResponse])
async def get_all(service: RouteStopsService = Depends(get_route_stops_service)):
    return await service.get_all()


@router.get("/{id}", response_model=RouteStopResponse)
async def get_by_id(
    id: int, service: RouteStopsService = Depends(get_route_stops_service)
):
    return await service.get_by_id(id)


@router.post("/", response_model=RouteStopResponse, status_code=201)
async def create(
    data: RouteStopData, service: RouteStopsService = Depends(get_route_stops_service)
):
    return await service.create(data)


@router.put("/{id}", response_model=RouteStopResponse)
async def update(
    id: int,
    data: RouteStopData,
    service: RouteStopsService = Depends(get_route_stops_service),
):
    return await service.update(id, data)


@router.delete("/{id}", response_model=RouteStopResponse)
async def delete(
    id: int, service: RouteStopsService = Depends(get_route_stops_service)
):
    return await service.delete(id)
