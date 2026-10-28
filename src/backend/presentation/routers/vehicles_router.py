from fastapi import APIRouter, Depends
from pydantic import ConfigDict

from ...bll.services.vehicles_service import VehicleData, VehiclesService
from ..dependencies import get_vehicles_service
from .auth import ensure_visible, get_current_driver_id, require_admin

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


@router.delete(
    "/{id}", response_model=VehicleResponse, dependencies=[Depends(require_admin)]
)
async def delete(id: int, service: VehiclesService = Depends(get_vehicles_service)):
    return await service.delete(id)
