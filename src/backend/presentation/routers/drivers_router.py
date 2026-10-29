from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from ...bll.services.drivers_service import (
    DriverData,
    DriversService,
    DriverStatusData,
)
from ..dependencies import get_drivers_service
from .auth import ensure_visible, get_current_driver_id, require_admin

router = APIRouter(prefix="/drivers", tags=["drivers"])


class DriverResponse(DriverData):
    id: int
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[DriverResponse])
async def get_all(
    driver_id: int | None = Depends(get_current_driver_id),
    service: DriversService = Depends(get_drivers_service),
):
    if driver_id is None:
        return await service.get_all()
    return await service.get_by_driver(driver_id)


@router.get("/{id}", response_model=DriverResponse)
async def get_by_id(
    id: int,
    driver_id: int | None = Depends(get_current_driver_id),
    service: DriversService = Depends(get_drivers_service),
):
    obj = await service.get_by_id(id)
    if driver_id is not None:
        ensure_visible(obj, await service.get_by_driver(driver_id))
    return obj


@router.post(
    "/",
    response_model=DriverResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def create(
    data: DriverData, service: DriversService = Depends(get_drivers_service)
):
    return await service.create(data)


@router.put(
    "/{id}", response_model=DriverResponse, dependencies=[Depends(require_admin)]
)
async def update(
    id: int, data: DriverData, service: DriversService = Depends(get_drivers_service)
):
    return await service.update(id, data)


@router.patch(
    "/{id}/status",
    response_model=DriverResponse,
    dependencies=[Depends(require_admin)],
)
async def change_status(
    id: int,
    data: DriverStatusData,
    service: DriversService = Depends(get_drivers_service),
):
    return await service.change_status(id, data.employment_status)


@router.delete(
    "/{id}", response_model=DriverResponse, dependencies=[Depends(require_admin)]
)
async def delete(id: int, service: DriversService = Depends(get_drivers_service)):
    return await service.delete(id)
