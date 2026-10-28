from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from ...bll.services.drivers_service import DriverData, DriversService
from ..dependencies import get_drivers_service

router = APIRouter(prefix="/drivers", tags=["drivers"])


class DriverResponse(DriverData):
    id: int
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[DriverResponse])
async def get_all(service: DriversService = Depends(get_drivers_service)):
    return await service.get_all()


@router.get("/{id}", response_model=DriverResponse)
async def get_by_id(id: int, service: DriversService = Depends(get_drivers_service)):
    return await service.get_by_id(id)


@router.post("/", response_model=DriverResponse, status_code=201)
async def create(
    data: DriverData, service: DriversService = Depends(get_drivers_service)
):
    return await service.create(data)


@router.put("/{id}", response_model=DriverResponse)
async def update(
    id: int, data: DriverData, service: DriversService = Depends(get_drivers_service)
):
    return await service.update(id, data)


@router.delete("/{id}", response_model=DriverResponse)
async def delete(id: int, service: DriversService = Depends(get_drivers_service)):
    return await service.delete(id)
