from fastapi import APIRouter, Depends
from pydantic import ConfigDict

from ...bll.services.vehicles_service import (
    MaintenanceData,
    TechnicalStateData,
    VehicleData,
    VehiclesService,
    VehicleStatusData,
)
from ..dependencies import get_vehicles_service
from .auth import ensure_visible, get_current_driver_id, require_admin
from .repair_records_router import RepairRecordResponse

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


class VehicleResponse(VehicleData):
    id: int
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[VehicleResponse])
async def get_all(
    driver_id: int | None = Depends(get_current_driver_id),
    service: VehiclesService = Depends(get_vehicles_service),
):
    if driver_id is None:
        return await service.get_all()
    return await service.get_by_driver(driver_id)


@router.get("/{id}", response_model=VehicleResponse)
async def get_by_id(
    id: int,
    driver_id: int | None = Depends(get_current_driver_id),
    service: VehiclesService = Depends(get_vehicles_service),
):
    obj = await service.get_by_id(id)
    if driver_id is not None:
        ensure_visible(obj, await service.get_by_driver(driver_id))
    return obj


@router.post(
    "/",
    response_model=VehicleResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def create(
    data: VehicleData, service: VehiclesService = Depends(get_vehicles_service)
):
    return await service.create(data)


@router.put(
    "/{id}", response_model=VehicleResponse, dependencies=[Depends(require_admin)]
)
async def update(
    id: int, data: VehicleData, service: VehiclesService = Depends(get_vehicles_service)
):
    return await service.update(id, data)


@router.patch(
    "/{id}/status",
    response_model=VehicleResponse,
    dependencies=[Depends(require_admin)],
)
async def change_status(
    id: int,
    data: VehicleStatusData,
    service: VehiclesService = Depends(get_vehicles_service),
):
    return await service.change_status(id, data.status)


@router.post(
    "/{id}/maintenance",
    response_model=RepairRecordResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def schedule_maintenance(
    id: int,
    data: MaintenanceData,
    service: VehiclesService = Depends(get_vehicles_service),
):
    return await service.schedule_maintenance(id, data.type, data.date)


@router.patch(
    "/{id}/technical-state",
    response_model=VehicleResponse,
    dependencies=[Depends(require_admin)],
)
async def update_technical_state(
    id: int,
    data: TechnicalStateData,
    service: VehiclesService = Depends(get_vehicles_service),
):
    return await service.update_technical_state(id, data.technical_state)


@router.delete(
    "/{id}", response_model=VehicleResponse, dependencies=[Depends(require_admin)]
)
async def delete(id: int, service: VehiclesService = Depends(get_vehicles_service)):
    return await service.delete(id)
