from fastapi import APIRouter, Depends
from pydantic import ConfigDict

from ...bll.services.vehicles_service import VehicleData, VehiclesService
from ..dependencies import get_vehicles_service

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


class VehicleResponse(VehicleData):
    id: int
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[VehicleResponse])
async def get_all(service: VehiclesService = Depends(get_vehicles_service)):
    return await service.get_all()


@router.get("/{id}", response_model=VehicleResponse)
async def get_by_id(id: int, service: VehiclesService = Depends(get_vehicles_service)):
    return await service.get_by_id(id)


@router.post("/", response_model=VehicleResponse, status_code=201)
async def create(
    data: VehicleData, service: VehiclesService = Depends(get_vehicles_service)
):
    return await service.create(data)


@router.put("/{id}", response_model=VehicleResponse)
async def update(
    id: int, data: VehicleData, service: VehiclesService = Depends(get_vehicles_service)
):
    return await service.update(id, data)


@router.delete("/{id}", response_model=VehicleResponse)
async def delete(id: int, service: VehiclesService = Depends(get_vehicles_service)):
    return await service.delete(id)
