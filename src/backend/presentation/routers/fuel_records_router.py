from fastapi import APIRouter, Depends
from pydantic import ConfigDict

from ...bll.interfaces.fuel_records_interface import IFuelRecordsService
from ...bll.services.fuel_records_service import FuelRecordData
from ..dependencies import get_fuel_records_service
from .auth import require_admin

router = APIRouter(
    prefix="/fuel-records", tags=["fuel-records"], dependencies=[Depends(require_admin)]
)


class FuelRecordResponse(FuelRecordData):
    id: int
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[FuelRecordResponse])
async def get_all(service: IFuelRecordsService = Depends(get_fuel_records_service)):
    return await service.get_all()


@router.get("/{id}", response_model=FuelRecordResponse)
async def get_by_id(
    id: int, service: IFuelRecordsService = Depends(get_fuel_records_service)
):
    return await service.get_by_id(id)


@router.post("/", response_model=FuelRecordResponse, status_code=201)
async def create(
    data: FuelRecordData,
    service: IFuelRecordsService = Depends(get_fuel_records_service),
):
    return await service.create(data)


@router.put("/{id}", response_model=FuelRecordResponse)
async def update(
    id: int,
    data: FuelRecordData,
    service: IFuelRecordsService = Depends(get_fuel_records_service),
):
    return await service.update(id, data)


@router.delete("/{id}", response_model=FuelRecordResponse)
async def delete(
    id: int, service: IFuelRecordsService = Depends(get_fuel_records_service)
):
    return await service.delete(id)
