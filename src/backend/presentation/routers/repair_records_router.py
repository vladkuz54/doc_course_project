from fastapi import APIRouter, Depends
from pydantic import ConfigDict

from ...bll.services.repair_records_service import (
    RepairCostData,
    RepairRecordData,
    RepairRecordsService,
)
from ..dependencies import get_repair_records_service
from .auth import require_admin

router = APIRouter(
    prefix="/repair-records",
    tags=["repair-records"],
    dependencies=[Depends(require_admin)],
)


class RepairRecordResponse(RepairRecordData):
    id: int
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[RepairRecordResponse])
async def get_all(service: RepairRecordsService = Depends(get_repair_records_service)):
    return await service.get_all()


@router.get("/{id}", response_model=RepairRecordResponse)
async def get_by_id(
    id: int, service: RepairRecordsService = Depends(get_repair_records_service)
):
    return await service.get_by_id(id)


@router.post("/", response_model=RepairRecordResponse, status_code=201)
async def create(
    data: RepairRecordData,
    service: RepairRecordsService = Depends(get_repair_records_service),
):
    return await service.create(data)


@router.put("/{id}", response_model=RepairRecordResponse)
async def update(
    id: int,
    data: RepairRecordData,
    service: RepairRecordsService = Depends(get_repair_records_service),
):
    return await service.update(id, data)


@router.post("/{id}/cost", response_model=RepairRecordResponse)
async def record_cost(
    id: int,
    data: RepairCostData,
    service: RepairRecordsService = Depends(get_repair_records_service),
):
    return await service.record_repair_cost(id, data.cost)


@router.delete("/{id}", response_model=RepairRecordResponse)
async def delete(
    id: int, service: RepairRecordsService = Depends(get_repair_records_service)
):
    return await service.delete(id)
