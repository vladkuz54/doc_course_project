from fastapi import APIRouter, Depends
from pydantic import ConfigDict

from ...bll.services.routes_service import RouteData, RoutesService
from ..dependencies import get_routes_service

router = APIRouter(prefix="/routes", tags=["routes"])


class RouteResponse(RouteData):
    id: int
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[RouteResponse])
async def get_all(service: RoutesService = Depends(get_routes_service)):
    return await service.get_all()


@router.get("/{id}", response_model=RouteResponse)
async def get_by_id(id: int, service: RoutesService = Depends(get_routes_service)):
    return await service.get_by_id(id)


@router.post("/", response_model=RouteResponse, status_code=201)
async def create(data: RouteData, service: RoutesService = Depends(get_routes_service)):
    return await service.create(data)


@router.put("/{id}", response_model=RouteResponse)
async def update(
    id: int, data: RouteData, service: RoutesService = Depends(get_routes_service)
):
    return await service.update(id, data)


@router.delete("/{id}", response_model=RouteResponse)
async def delete(id: int, service: RoutesService = Depends(get_routes_service)):
    return await service.delete(id)
